"""
Ray casting utilities for 3D rendering.

Implements the DDA (Digital Differential Analyzer) algorithm for efficient
wall detection in a grid-based world.
"""

import math
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from presentation.camera.camera import Camera

from presentation.camera.camera import RayHit


def cast_ray(camera: 'Camera', ray_angle: float, level,
             max_distance: float = 20.0) -> Optional[RayHit]:
    """
    Cast a single ray from the camera position at the given angle.

    Args:
        camera: Camera object with position and FOV.
        ray_angle: Absolute angle of the ray in degrees.
        level: Level object used for collision queries.
        max_distance: Maximum ray travel distance.

    Returns:
        RayHit if a wall was found, otherwise None.
    """
    rad = math.radians(ray_angle)
    ray_dir_x = math.cos(rad)
    ray_dir_y = math.sin(rad)

    if abs(ray_dir_x) < 0.0001:
        ray_dir_x = 0.0001
    if abs(ray_dir_y) < 0.0001:
        ray_dir_y = 0.0001

    map_x = int(camera.x)
    map_y = int(camera.y)

    delta_dist_x = abs(1 / ray_dir_x)
    delta_dist_y = abs(1 / ray_dir_y)

    if ray_dir_x < 0:
        step_x = -1
        side_dist_x = (camera.x - map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (map_x + 1.0 - camera.x) * delta_dist_x

    if ray_dir_y < 0:
        step_y = -1
        side_dist_y = (camera.y - map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (map_y + 1.0 - camera.y) * delta_dist_y

    hit = False
    side = 'NS'
    distance = 0.0

    while not hit and distance < max_distance:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 'NS'
            distance = side_dist_x - delta_dist_x
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 'EW'
            distance = side_dist_y - delta_dist_y

        door = level.get_door_at(map_x, map_y)
        if door:
            hit = True
            break

        if level.is_wall(map_x, map_y):
            hit = True
        elif not level.is_walkable(map_x, map_y):
            hit = True

    if not hit:
        return None

    angle_diff = ray_angle - camera.angle
    perp_distance = distance * math.cos(math.radians(angle_diff))

    if side == 'NS':
        wall_x = camera.y + distance * ray_dir_y
    else:
        wall_x = camera.x + distance * ray_dir_x
    wall_x -= math.floor(wall_x)

    wall_type, door = _determine_wall_hit(level, map_x, map_y, side)

    return RayHit(
        distance=perp_distance,
        wall_type=wall_type,
        texture_x=wall_x,
        hit_x=map_x,
        hit_y=map_y,
        side=side,
        door=door,
    )


def cast_fov_rays(camera: 'Camera', level,
                  num_rays: int = 80) -> List[Optional[RayHit]]:
    """
    Cast one ray per screen column across the camera's field of view.

    Args:
        camera: Camera object.
        level: Level object.
        num_rays: Number of rays (should equal viewport width).

    Returns:
        List of RayHit objects, one per column (None where no wall was hit).
    """
    results = []
    start_angle = camera.angle - (camera.fov / 2)
    angle_step = camera.fov / num_rays
    for i in range(num_rays):
        results.append(cast_ray(camera, start_angle + i * angle_step, level))
    return results


def _determine_wall_hit(level, x: int, y: int, side: str):
    """
    Classify the wall tile at (x, y) that was hit by a ray.

    Returns:
        Tuple of (wall_type: str, door).

    Wall types:
        'room_wall'                  Plain room wall with no adjacent corridor.
        'room_wall_entrance'         The single tile that IS the corridor opening.
                                     The ray struck its face head-on (perpendicular
                                     to the corridor axis).
        'room_wall_beside_entrance'  The torso/jamb view of the entrance tile, or
                                     a wall tile adjacent to a pure corridor tile.
                                     The ray struck a face parallel to the corridor.
        'corridor_wall'              Corridor boundary or out-of-bounds tile.
        'door_open' / 'door_locked'  Door tiles.

    Geometry notes
    --------------
    The level generator starts each corridor ON the room's wall tile:

        _connect_rooms_horizontal:
            x1 = room1.x + room1.width - 1   <- right wall tile of room1
            corridor.add_tile(x1, y_mid)     <- SAME tile as the wall

    So the entrance tile W_E satisfies both is_wall() and get_corridor_at().
    The tiles directly above and below W_E (W_B) are plain wall tiles; their
    only corridor-adjacent neighbour is W_E itself, which is also a wall.

    Classification
    --------------
    Case A  This tile is itself a corridor tile (W_E).
            Find the first *pure* corridor neighbour (not also a wall) to
            determine the corridor axis, then match against the DDA side:
              horizontal corridor (dx neighbour) -> entrance face hit with side 'NS'
              vertical   corridor (dy neighbour) -> entrance face hit with side 'EW'
            Matching side  -> 'room_wall_entrance'
            Non-matching   -> 'room_wall_beside_entrance'

    Case B  Plain wall tile adjacent to a corridor.
            Only pure corridor neighbours (not walls) are counted, preventing
            W_B tiles from being misclassified because W_E is adjacent.
            Pure corridor neighbour found -> 'room_wall_beside_entrance'
            No such neighbour             -> 'room_wall'
    """
    door = level.get_door_at(x, y)
    if door:
        return ('door_locked' if door.is_locked else 'door_open'), door

    is_room_wall = any(room.is_on_wall(x, y) for room in level.rooms)
    if not is_room_wall:
        return 'corridor_wall', None

    # Case A: entrance tile (wall + corridor overlap)
    self_corridor, _ = level.get_corridor_at(x, y)
    if self_corridor is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nb_corr, _ = level.get_corridor_at(x + dx, y + dy)
            if nb_corr is not None and not level.is_wall(x + dx, y + dy):
                if dx != 0 and side == 'NS':
                    return 'room_wall_entrance', None
                if dy != 0 and side == 'EW':
                    return 'room_wall_entrance', None
                return 'room_wall_beside_entrance', None
        return 'room_wall_entrance', None

    # Case B: plain wall tile beside a corridor
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb_corr, _ = level.get_corridor_at(x + dx, y + dy)
        if nb_corr is not None and not level.is_wall(x + dx, y + dy):
            return 'room_wall_beside_entrance', None

    return 'room_wall', None


def world_to_screen_column(camera: 'Camera', ray_index: int,
                            num_rays: int, screen_width: int) -> int:
    """Map a ray index to a screen column index."""
    return int((ray_index / num_rays) * screen_width)


def calculate_wall_height(distance: float, screen_height: int,
                          wall_unit_size: float = 1.0) -> int:
    """
    Calculate projected wall height in screen characters.

    Args:
        distance: Perpendicular distance to the wall.
        screen_height: Viewport height in characters.
        wall_unit_size: World-space height of one wall unit.

    Returns:
        Clamped wall height in characters.
    """
    if distance < 0.1:
        distance = 0.1
    wall_height = int((screen_height * wall_unit_size) / distance)
    return max(1, min(wall_height, screen_height * 2))
