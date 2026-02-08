"""
Camera controller for 3D mode with combat and item interaction support.
"""
import math
from presentation.camera.camera import Camera
from config.game_config import CameraConfig


class CameraController:
    """Manages camera movement, collision detection, and 3D interactions."""
    
    def __init__(self, camera, level, move_speed=CameraConfig.MOVE_SPEED, rotation_speed=CameraConfig.ROTATION_SPEED):
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
        
        # Movement state
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # Collision padding (prevents getting too close to walls)
        self.collision_radius = CameraConfig.COLLISION_RADIUS
        
        # Interaction range
        self.interaction_range = 1.5  # Distance to interact with entities
    
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
        perpendicular_angle = self.camera.angle + 90
        rad = math.radians(perpendicular_angle)
        
        new_x = self.camera.x + math.cos(rad) * self.move_speed
        new_y = self.camera.y + math.sin(rad) * self.move_speed
        
        return self._try_move(new_x, new_y)
    
    def strafe_right(self):
        """Move camera right (perpendicular to facing direction)."""
        perpendicular_angle = self.camera.angle - 90
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
        """
        Attempt to move to new position with collision detection.
        
        Args:
            new_x: Target X position
            new_y: Target Y position
        
        Returns:
            Boolean indicating if movement was successful
        """
        # Check if new position is valid
        if self._is_position_valid(new_x, new_y):
            self.camera.set_position(new_x, new_y)
            return True
        
        # Movement blocked
        return False
    
    def _is_position_valid(self, x, y):
        """Check if a position is valid (walkable and not too close to walls)."""
        # Check the center point
        if not self.level.is_walkable(int(x), int(y)):
            return False
        
        # Check collision circle (prevents clipping into walls)
        check_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        
        for angle in check_angles:
            rad = math.radians(angle)
            check_x = x + math.cos(rad) * self.collision_radius
            check_y = y + math.sin(rad) * self.collision_radius
            
            if not self.level.is_walkable(int(check_x), int(check_y)):
                return False
        
        return True
    
    def get_entity_in_front(self, level, check_distance=None):
        """
        Get the entity (enemy or item) directly in front of the camera.
        
        Args:
            level: Level object containing entities
            check_distance: Maximum distance to check (default: interaction_range)
        
        Returns:
            Tuple of (entity, entity_type, distance) or (None, None, None)
            entity_type can be 'enemy' or 'item'
        """
        if check_distance is None:
            check_distance = self.interaction_range
        
        # Calculate position in front of camera
        rad = math.radians(self.camera.angle)
        
        # Check multiple distances (stepped ray)
        steps = int(check_distance * 4)  # Check every 0.25 units
        
        for step in range(1, steps + 1):
            dist = step * 0.25
            check_x = self.camera.x + math.cos(rad) * dist
            check_y = self.camera.y + math.sin(rad) * dist
            
            # Check for enemies
            for room in level.rooms:
                for enemy in room.enemies:
                    if not enemy.is_alive():
                        continue
                    
                    ex, ey = enemy.position
                    
                    # Check if enemy is at this position (with tolerance)
                    if abs(ex - check_x) < 0.5 and abs(ey - check_y) < 0.5:
                        return (enemy, 'enemy', dist)
            
            # Check for items
            for room in level.rooms:
                for item in room.items:
                    if not item.position:
                        continue
                    
                    ix, iy = item.position
                    
                    # Check if item is at this position (with tolerance)
                    if abs(ix - check_x) < 0.5 and abs(iy - check_y) < 0.5:
                        return (item, 'item', dist)
            
            # Check for exit
            if level.exit_position:
                ex, ey = level.exit_position
                if abs(ex - check_x) < 0.5 and abs(ey - check_y) < 0.5:
                    return ('exit', 'exit', dist)
        
        return (None, None, None)
    
    def attack_entity_in_front(self, character, level):
        """
        Detect an enemy directly in front of the camera.

        This method no longer executes combat. It merely reports the enemy
        object (if present) and a short message; the domain-level combat
        system is responsible for resolving the attack and applying effects.

        Returns:
            Tuple of (success, message, enemy) where enemy is the Enemy instance
        """
        entity, entity_type, distance = self.get_entity_in_front(level)

        if entity_type != 'enemy':
            return (False, "No enemy in front", None)

        if distance > self.interaction_range:
            return (False, "Enemy too far away", None)

        # Report the enemy; actual combat will be performed by the session's CombatSystem
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
        
        # Try to add to backpack
        success = character.backpack.add_item(entity)
        
        if success:
            # Remove from level
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
        
        Args:
            level: Level object
        
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
        # Check position in front of camera
        rad = math.radians(self.camera.angle)
        check_x = self.camera.x + math.cos(rad) * self.interaction_range
        check_y = self.camera.y + math.sin(rad) * self.interaction_range
        
        door = self.level.get_door_at(int(check_x), int(check_y))
        
        if not door:
            return (False, "No door nearby")
        
        if not door.is_locked:
            return (True, "Door is already open")
        
        # Check if player has the key
        from domain.key_door_system import unlock_door_if_possible
        
        if unlock_door_if_possible(door, character):
            return (True, f"Unlocked {door.color.value} door!")
        else:
            return (False, f"Need {door.color.value} key to unlock this door")
    
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
