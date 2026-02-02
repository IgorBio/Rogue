"""
Ray casting utilities for 3D rendering.

Implements DDA (Digital Differential Analyzer) algorithm for wall detection.
"""

import math
from typing import Tuple, Optional, List
from domain.entities.position import Position


class RayHit:
    """Represents the result of a ray cast."""

    def __init__(self, distance: float, wall_type: str, texture_x: float,
                 hit_x: int, hit_y: int, side: str):
        """
        Initialize a ray hit result.

        Args:
            distance: Perpendicular distance to wall (fisheye corrected)
            wall_type: Type of wall hit ('room_wall', 'corridor_wall', 'door')
            texture_x: X coordinate on texture (0.0 - 1.0)
            hit_x: Grid X coordinate where ray hit
            hit_y: Grid Y coordinate where ray hit
            side: Which side was hit ('NS' for north/south, 'EW' for east/west)
        """
        self.distance = distance
        self.wall_type = wall_type
        self.texture_x = texture_x
        self.hit_x = hit_x
        self.hit_y = hit_y
        self.side = side


class Camera:
    """
    Represents the player's camera in 3D space.

    Uses Position for coordinate management but exposes float coordinates
    for raycasting precision. The Position stores the grid-aligned base
    position, while fractional offsets are maintained separately.

    Attributes:
        _position (Position): Grid-aligned base position
        _offset_x (float): Fractional offset within grid cell (0.0 to 1.0)
        _offset_y (float): Fractional offset within grid cell (0.0 to 1.0)
        angle (float): Facing angle in degrees
        fov (float): Field of view in degrees
    """

    def __init__(self, x: float, y: float, angle: float = 0.0, fov: float = 60.0):
        """
        Initialize camera.

        Args:
            x: X position in world space (can be float)
            y: Y position in world space (can be float)
            angle: Facing angle in degrees (0 = East, 90 = North, etc.)
            fov: Field of view in degrees
        """
        # Split into integer grid position and fractional offset
        self._position = Position(int(x), int(y))
        self._offset_x = x - int(x)  # Fractional part: 0.0 to 1.0
        self._offset_y = y - int(y)

        self.angle = angle  # Degrees
        self.fov = fov  # Degrees

    @property
    def x(self) -> float:
        """
        Get X coordinate as float (for raycasting).

        Returns:
            float: X coordinate (grid position + offset)
        """
        return float(self._position.x) + self._offset_x

    @property
    def y(self) -> float:
        """
        Get Y coordinate as float (for raycasting).

        Returns:
            float: Y coordinate (grid position + offset)
        """
        return float(self._position.y) + self._offset_y

    @property
    def position(self) -> Tuple[float, float]:
        """
        Get position as float tuple (backward compatibility).

        Returns:
            tuple: (x, y) as floats
        """
        return (self.x, self.y)

    @property
    def position_obj(self) -> Position:
        """
        Get grid-aligned Position object.

        Returns:
            Position: Position object (integer coordinates)
        """
        return self._position

    @property
    def grid_position(self) -> Tuple[int, int]:
        """
        Get grid-aligned position as int tuple.

        Returns:
            tuple: (x, y) as integers
        """
        return self._position.tuple

    def set_position(self, x: float, y: float):
        """
        Set camera position.

        Args:
            x: New X coordinate (can be float)
            y: New Y coordinate (can be float)
        """
        self._position.update(int(x), int(y))
        self._offset_x = x - int(x)
        self._offset_y = y - int(y)

    def move_to(self, x: float, y: float):
        """
        Move camera to new position.

        Args:
            x: New X coordinate
            y: New Y coordinate
        """
        self.set_position(x, y)

    def get_direction_vector(self) -> Tuple[float, float]:
        """
        Get the direction vector the camera is facing.

        Returns:
            tuple: (dx, dy) direction vector
        """
        rad = math.radians(self.angle)
        return math.cos(rad), math.sin(rad)

    def rotate(self, degrees: float):
        """
        Rotate camera by given degrees.

        Args:
            degrees: Degrees to rotate (positive = counterclockwise)
        """
        self.angle = (self.angle + degrees) % 360

    def move_forward(self, distance: float) -> Tuple[float, float]:
        """
        Calculate new position if moving forward.

        Args:
            distance: Distance to move

        Returns:
            Tuple of (new_x, new_y) as floats
        """
        dx, dy = self.get_direction_vector()
        return self.x + dx * distance, self.y + dy * distance

    def move_backward(self, distance: float) -> Tuple[float, float]:
        """
        Calculate new position if moving backward.

        Args:
            distance: Distance to move

        Returns:
            Tuple of (new_x, new_y) as floats
        """
        return self.move_forward(-distance)

    def move_strafe(self, distance: float) -> Tuple[float, float]:
        """
        Calculate new position if strafing (moving sideways).

        Args:
            distance: Distance to strafe (positive = right, negative = left)

        Returns:
            Tuple of (new_x, new_y) as floats
        """
        dx, dy = self.get_direction_vector()
        # Rotate direction 90 degrees for strafe
        strafe_dx = -dy
        strafe_dy = dx
        return self.x + strafe_dx * distance, self.y + strafe_dy * distance

    def distance_to(self, target_x: float, target_y: float) -> float:
        """
        Calculate distance to a point.

        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate

        Returns:
            float: Euclidean distance
        """
        dx = self.x - target_x
        dy = self.y - target_y
        return math.sqrt(dx * dx + dy * dy)

    def __repr__(self):
        return (f"Camera(pos=({self.x:.2f}, {self.y:.2f}), "
                f"grid={self._position.tuple}, angle={self.angle:.1f}°, fov={self.fov}°)")


def cast_ray(camera: Camera, ray_angle: float, level, 
             max_distance: float = 20.0) -> Optional[RayHit]:
    """
    Cast a single ray from camera position at given angle.

    Uses DDA algorithm for efficient grid traversal.

    Args:
        camera: Camera object with position
        ray_angle: Angle of ray in degrees (absolute, not relative to camera)
        level: Level object for collision detection
        max_distance: Maximum ray distance

    Returns:
        RayHit object if wall found, None otherwise
    """
    # Convert angle to radians
    rad = math.radians(ray_angle)

    # Ray direction
    ray_dir_x = math.cos(rad)
    ray_dir_y = math.sin(rad)

    # Prevent division by zero
    if abs(ray_dir_x) < 0.0001:
        ray_dir_x = 0.0001
    if abs(ray_dir_y) < 0.0001:
        ray_dir_y = 0.0001

    # Current map position
    map_x = int(camera.x)
    map_y = int(camera.y)

    # Length of ray from one x or y-side to next x or y-side
    delta_dist_x = abs(1 / ray_dir_x)
    delta_dist_y = abs(1 / ray_dir_y)

    # Calculate step direction and initial side distances
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

    # Perform DDA
    hit = False
    side = 'NS'  # Which side was hit (NS = north/south, EW = east/west)
    distance = 0.0

    while not hit and distance < max_distance:
        # Jump to next map square
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

        # Check if ray has hit a wall
        if level.is_wall(map_x, map_y):
            hit = True
        elif not level.is_walkable(map_x, map_y):
            # Hit something non-walkable (could be out of bounds)
            hit = True

    if not hit:
        return None

    # Calculate perpendicular distance (avoid fisheye effect)
    angle_diff = ray_angle - camera.angle
    perp_distance = distance * math.cos(math.radians(angle_diff))

    # Calculate exact hit position for texture mapping
    if side == 'NS':
        wall_x = camera.y + distance * ray_dir_y
    else:
        wall_x = camera.x + distance * ray_dir_x

    wall_x -= math.floor(wall_x)  # Keep only fractional part (0.0 - 1.0)

    # Determine wall type
    wall_type = _determine_wall_type(level, map_x, map_y)

    return RayHit(
        distance=perp_distance,
        wall_type=wall_type,
        texture_x=wall_x,
        hit_x=map_x,
        hit_y=map_y,
        side=side
    )


def cast_fov_rays(camera: Camera, level, num_rays: int = 80) -> List[Optional[RayHit]]:
    """
    Cast multiple rays across the camera's field of view.

    Args:
        camera: Camera object
        level: Level object
        num_rays: Number of rays to cast (more = better quality, slower)

    Returns:
        List of RayHit objects (one per screen column)
    """
    results = []

    # Calculate angle for each ray
    start_angle = camera.angle - (camera.fov / 2)
    angle_step = camera.fov / num_rays

    for i in range(num_rays):
        ray_angle = start_angle + (i * angle_step)
        hit = cast_ray(camera, ray_angle, level)
        results.append(hit)

    return results


def _determine_wall_type(level, x: int, y: int) -> str:
    """
    Determine what type of wall is at the given position.

    Args:
        level: Level object
        x: Grid X coordinate
        y: Grid Y coordinate

    Returns:
        Wall type string: 'room_wall', 'corridor_wall', or 'door'
    """
    # Check if it's a door
    door = level.get_door_at(x, y)
    if door:
        return 'door'

    # Check if in a room
    for room in level.rooms:
        if room.is_on_wall(x, y):
            return 'room_wall'

    # Must be a corridor wall or out of bounds
    return 'corridor_wall'


def world_to_screen_column(camera: Camera, ray_index: int, num_rays: int,
                          screen_width: int) -> int:
    """
    Convert ray index to screen column.

    Args:
        camera: Camera object
        ray_index: Index of the ray (0 to num_rays-1)
        num_rays: Total number of rays
        screen_width: Width of screen in characters

    Returns:
        Screen column index (0 to screen_width-1)
    """
    return int((ray_index / num_rays) * screen_width)


def calculate_wall_height(distance: float, screen_height: int,
                         wall_unit_size: float = 1.0) -> int:
    """
    Calculate how tall a wall should appear on screen based on distance.

    Args:
        distance: Perpendicular distance to wall
        screen_height: Height of screen in characters
        wall_unit_size: Height of one grid unit in world space

    Returns:
        Wall height in screen characters
    """
    if distance < 0.1:
        distance = 0.1  # Prevent division by zero

    # Simple perspective projection
    wall_height = int((screen_height * wall_unit_size) / distance)

    # Clamp to reasonable values
    return max(1, min(wall_height, screen_height * 2))


# Test function
def test_raycasting():
    """
    Test ray casting with a simple example.

    This would require a mock level object in real testing.
    """
    print("Ray Casting Module Loaded Successfully!")
    print("\nKey Functions:")
    print("- Camera: Manages position and orientation")
    print("- cast_ray(): Casts single ray using DDA algorithm")
    print("- cast_fov_rays(): Casts multiple rays for full FOV")
    print("- RayHit: Stores ray collision data")

    print("\nExample Camera:")
    cam = Camera(5.5, 5.5, angle=0.0, fov=60.0)
    print(f"  Position: ({cam.x}, {cam.y})")
    print(f"  Grid Position: {cam.grid_position}")
    print(f"  Angle: {cam.angle}°")
    print(f"  FOV: {cam.fov}°")

    dx, dy = cam.get_direction_vector()
    print(f"  Direction Vector: ({dx:.2f}, {dy:.2f})")

    print("\nRay Casting Formula:")
    print("  Perpendicular Distance = Distance × cos(ray_angle - camera_angle)")
    print("  Wall Height = (Screen_Height × Wall_Size) / Distance")
    print("\nReady for integration with game level!")


if __name__ == "__main__":
    test_raycasting()
