"""
Camera controller for 3D mode with combat and item interaction support.
"""
import math
from presentation.camera.camera import Camera
from config.game_config import CameraConfig, CombatConfig


class CameraController:
    """Manages camera movement, collision detection, and 3D interactions."""

    # Half-width of the aiming zone in screen columns.  The targeting cone
    # is computed so that an entity whose projected screen_x falls within
    # +/- _AIM_HALF_PIXELS of the viewport centre counts as "in the reticle".
    _AIM_HALF_PIXELS = 2
    _FALLBACK_VIEWPORT_WIDTH = 80

    def __init__(self, camera, level, move_speed=CameraConfig.MOVE_SPEED,
                 rotation_speed=CameraConfig.ROTATION_SPEED):
        """
        Initialize camera controller.

        Args:
            camera: Camera object to control
            level: Level object for collision detection
            move_speed: Movement speed in units per step
            rotation_speed: Rotation speed in degrees per step
        """
        self.camera = camera
        self.level = level
        self.move_speed = move_speed
        self.rotation_speed = rotation_speed

        self.velocity_x = 0.0
        self.velocity_y = 0.0

        self.collision_radius = CameraConfig.COLLISION_RADIUS
        self.interaction_range = CombatConfig.MELEE_ATTACK_RANGE
        self._targeting_viewport_width = self._FALLBACK_VIEWPORT_WIDTH

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move_forward(self):
        """Move camera forward in facing direction."""
        new_x, new_y = self.camera.move_forward(self.move_speed)
        return self._try_move(new_x, new_y)

    def move_backward(self):
        """Move camera backward (opposite of facing direction)."""
        new_x, new_y = self.camera.move_backward(self.move_speed)
        return self._try_move(new_x, new_y)

    def strafe_left(self):
        """Move camera left (perpendicular to facing direction)."""
        perpendicular_angle = self.camera.angle - 90
        rad = math.radians(perpendicular_angle)
        new_x = self.camera.x + math.cos(rad) * self.move_speed
        new_y = self.camera.y + math.sin(rad) * self.move_speed
        return self._try_move(new_x, new_y)

    def strafe_right(self):
        """Move camera right (perpendicular to facing direction)."""
        perpendicular_angle = self.camera.angle + 90
        rad = math.radians(perpendicular_angle)
        new_x = self.camera.x + math.cos(rad) * self.move_speed
        new_y = self.camera.y + math.sin(rad) * self.move_speed
        return self._try_move(new_x, new_y)

    def rotate_left(self):
        """Rotate camera left (counter-clockwise)."""
        self.camera.rotate(-self.rotation_speed)
        return True

    def rotate_right(self):
        """Rotate camera right (clockwise)."""
        self.camera.rotate(self.rotation_speed)
        return True

    def _try_move(self, new_x, new_y):
        """Attempt to move to new position with collision detection."""
        if self._is_position_valid(new_x, new_y):
            self.camera.set_position(new_x, new_y)
            return True
        return False

    def _is_position_valid(self, x, y):
        """Check if a position is valid (walkable and not too close to walls)."""
        if not self.level.is_walkable(int(x), int(y)):
            return False
        check_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for angle in check_angles:
            rad = math.radians(angle)
            check_x = x + math.cos(rad) * self.collision_radius
            check_y = y + math.sin(rad) * self.collision_radius
            if not self.level.is_walkable(int(check_x), int(check_y)):
                return False
        return True

    # ------------------------------------------------------------------
    # Targeting helpers
    # ------------------------------------------------------------------

    def _compute_aim_cos_threshold(self, viewport_width=None):
        """
        Return the cosine threshold matching the reticle's physical aim cone.

        The aiming cone angle is derived from the projection geometry so that
        it corresponds exactly to +/- _AIM_HALF_PIXELS screen columns around
        the viewport centre, the same columns where the sprite renderer draws
        the entity glyph.

        When *viewport_width* is not available, use an emergency fallback
        width so aim logic still follows projection geometry.
        """
        fov_rad = math.radians(self.camera.fov)
        if not viewport_width or viewport_width <= 0:
            viewport_width = self._targeting_viewport_width or self._FALLBACK_VIEWPORT_WIDTH

        half_w = viewport_width / 2.0
        proj_dist = half_w / math.tan(fov_rad / 2.0)
        aim_angle = math.atan(self._AIM_HALF_PIXELS / proj_dist)
        return math.cos(aim_angle)

    def set_targeting_viewport_width(self, viewport_width):
        """Store active viewport width used by aiming logic."""
        if viewport_width and viewport_width > 0:
            self._targeting_viewport_width = int(viewport_width)

    def _has_line_of_sight(self, level, tx, ty, max_dist):
        """
        Return True when a straight ray from the camera reaches (tx, ty)
        without hitting a wall first.

        Uses a lightweight DDA pass — no texture or door logic needed.
        """
        dx = tx - self.camera.x
        dy = ty - self.camera.y
        angle_to_target = math.atan2(dy, dx)
        ray_dir_x = math.cos(angle_to_target)
        ray_dir_y = math.sin(angle_to_target)

        if abs(ray_dir_x) < 0.0001:
            ray_dir_x = 0.0001
        if abs(ray_dir_y) < 0.0001:
            ray_dir_y = 0.0001

        map_x = int(self.camera.x)
        map_y = int(self.camera.y)

        delta_dist_x = abs(1.0 / ray_dir_x)
        delta_dist_y = abs(1.0 / ray_dir_y)

        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (self.camera.x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - self.camera.x) * delta_dist_x

        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (self.camera.y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - self.camera.y) * delta_dist_y

        travelled = 0.0
        while travelled < max_dist:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                travelled = side_dist_x - delta_dist_x
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                travelled = side_dist_y - delta_dist_y

            if travelled >= max_dist - 0.1:
                break

            if level.is_wall(map_x, map_y) or not level.is_walkable(map_x, map_y):
                return False

        return True

    # ------------------------------------------------------------------
    # Entity detection
    # ------------------------------------------------------------------

    def get_entity_in_front(self, level, check_distance=None, viewport_width=None):
        """
        Get the entity (enemy, item, or exit) that the camera is aiming at.

        The aiming cone is calibrated to the projection geometry so the
        reticle symbol and the targeting detection agree on what is "centred".
        Entities behind walls (no line of sight) are excluded.

        Args:
            level: Level object containing entities.
            check_distance: Maximum targeting distance (default: interaction_range).
            viewport_width: Viewport width in columns for precise aim calibration.

        Returns:
            Tuple of (entity, entity_type, distance) or (None, None, None).
        """
        if check_distance is None:
            check_distance = self.interaction_range
        if viewport_width and viewport_width > 0:
            self._targeting_viewport_width = int(viewport_width)

        # Immediate exit: player is standing on the exit tile.
        grid_x, grid_y = int(self.camera.x), int(self.camera.y)
        if level.exit_position and level.exit_position == (grid_x, grid_y):
            return (level.exit_position, 'exit', 0.0)

        dir_x, dir_y = self.camera.get_direction_vector()
        cos_threshold = self._compute_aim_cos_threshold(viewport_width)
        best = (None, None, None)

        def _consider_entity(entity, entity_type):
            nonlocal best
            if entity_type == 'exit':
                tx, ty = entity
            else:
                if not entity.position:
                    return
                tx, ty = entity.position

            # Use tile centre for a symmetric aim check.
            cx = tx + 0.5
            cy = ty + 0.5
            dx = cx - self.camera.x
            dy = cy - self.camera.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.01 or dist > check_distance:
                return

            cos_val = (dx * dir_x + dy * dir_y) / dist
            if cos_val < cos_threshold:
                return

            # Skip entities hidden behind walls.
            if not self._has_line_of_sight(level, cx, cy, dist):
                return

            if best[2] is None or dist < best[2]:
                best = (entity, entity_type, dist)

        for room in level.rooms:
            for enemy in room.enemies:
                if not enemy.is_alive():
                    continue
                _consider_entity(enemy, 'enemy')

        for room in level.rooms:
            for item in room.items:
                _consider_entity(item, 'item')

        if level.exit_position:
            _consider_entity(level.exit_position, 'exit')

        return best

    # ------------------------------------------------------------------
    # Combat / interaction
    # ------------------------------------------------------------------

    def attack_entity_in_front(self, character, level):
        """
        Detect an enemy directly in front of the camera.

        This method no longer executes combat. It merely reports the enemy
        object (if present) and a short message; the domain-level combat
        system is responsible for resolving the attack and applying effects.

        Returns:
            Tuple of (success, message, enemy) where enemy is the Enemy instance.
        """
        entity, entity_type, distance = self.get_entity_in_front(level)

        if entity_type != 'enemy':
            return (False, "No enemy in front", None)

        if distance > self.interaction_range:
            return (False, "Enemy too far away", None)

        return (True, f"Enemy spotted: {getattr(entity, 'enemy_type', 'enemy')}", entity)

    def pickup_item_in_front(self, character, level):
        """
        Pick up an item directly in front of the camera.

        Args:
            character: Character object (with backpack)
            level: Level object

        Returns:
            Tuple of (success, message, item)
        """
        entity, entity_type, distance = self.get_entity_in_front(level)

        if entity_type != 'item':
            return (False, "No item in front", None)

        if distance > self.interaction_range:
            return (False, "Item too far away", None)

        success = character.backpack.add_item(entity)

        if success:
            for room in level.rooms:
                if entity in room.items:
                    room.remove_item(entity)
                    break

            from config.game_config import ItemType

            if entity.item_type == ItemType.TREASURE:
                message = f"Picked up {entity.value} treasure!"
            elif entity.item_type == ItemType.FOOD:
                message = f"Picked up food (heals {entity.health_restoration} HP)"
            elif entity.item_type == ItemType.WEAPON:
                message = f"Picked up {entity.name}"
            elif entity.item_type == ItemType.ELIXIR:
                message = f"Picked up elixir ({entity.stat_type} +{entity.bonus})"
            elif entity.item_type == ItemType.SCROLL:
                message = f"Picked up scroll ({entity.stat_type} +{entity.bonus})"
            elif entity.item_type == ItemType.KEY:
                message = f"Picked up {entity.color.value} key!"
            else:
                message = "Picked up item"

            return (True, message, entity)
        else:
            return (False, "Backpack full!", None)

    def check_exit_in_front(self, level):
        """
        Check if the exit is directly in front of the camera.

        Returns:
            Tuple of (at_exit, distance)
        """
        entity, entity_type, distance = self.get_entity_in_front(level)
        if entity_type == 'exit':
            return (True, distance)
        return (False, None)

    def try_open_door(self, character):
        """
        Try to open a door in front of the camera.

        Args:
            character: Character object (for key checking)

        Returns:
            Tuple of (success, message)
        """
        rad = math.radians(self.camera.angle)
        steps = int(self.interaction_range * 4)
        door = None
        for step in range(1, steps + 1):
            dist = step * 0.25
            check_x = self.camera.x + math.cos(rad) * dist
            check_y = self.camera.y + math.sin(rad) * dist
            door = self.level.get_door_at(int(check_x), int(check_y))
            if door:
                break

        if not door:
            return (False, "No door nearby")

        if not door.is_locked:
            return (True, "Door is already open")

        from domain.key_door_system import unlock_door_if_possible

        if unlock_door_if_possible(door, character):
            return (True, f"Unlocked {door.color.value} door!")
        else:
            return (False, f"Need {door.color.value} key to unlock this door")

    # ------------------------------------------------------------------
    # State accessors / mutators
    # ------------------------------------------------------------------

    def get_position(self):
        """Get current camera position."""
        return (self.camera.x, self.camera.y)

    def get_angle(self):
        """Get current camera angle."""
        return self.camera.angle

    def set_position(self, x, y):
        """Set camera position (for teleporting)."""
        self.camera.set_position(x, y)

    def set_angle(self, angle):
        """Set camera angle (for teleporting/respawn)."""
        self.camera.angle = angle % 360

    def set_move_speed(self, speed):
        """Change movement speed."""
        self.move_speed = max(0.1, min(speed, 2.0))

    def set_rotation_speed(self, speed):
        """Change rotation speed."""
        self.rotation_speed = max(1, min(speed, 90))

    def set_interaction_range(self, range_value):
        """Change interaction range."""
        self.interaction_range = max(0.5, min(range_value, 5.0))

    def get_direction_name(self):
        """Get cardinal direction name based on angle."""
        angle = self.camera.angle % 360
        if angle < 22.5 or angle >= 337.5:
            return "East"
        elif angle < 67.5:
            return "North-East"
        elif angle < 112.5:
            return "North"
        elif angle < 157.5:
            return "North-West"
        elif angle < 202.5:
            return "West"
        elif angle < 247.5:
            return "South-West"
        elif angle < 292.5:
            return "South"
        elif angle < 337.5:
            return "South-East"
        return "East"

    def get_direction_arrow(self):
        """Get arrow character for current direction."""
        angle = self.camera.angle % 360
        if angle < 22.5 or angle >= 337.5:
            return "→"
        elif angle < 67.5:
            return "↗"
        elif angle < 112.5:
            return "↑"
        elif angle < 157.5:
            return "↖"
        elif angle < 202.5:
            return "←"
        elif angle < 247.5:
            return "↙"
        elif angle < 292.5:
            return "↓"
        elif angle < 337.5:
            return "↘"
        return "→"
