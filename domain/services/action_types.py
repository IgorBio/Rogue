"""
Action Types Enum for type-safe action handling.

Replaces magic strings with explicit enum values for better
IDE support, type safety, and maintainability.

Usage:
    from domain.services.action_types import ActionType
    
    if action_type == ActionType.MOVE:
        handle_movement()
"""
from enum import Enum, auto


class ActionType(Enum):
    """
    Enumeration of all possible player actions.
    
    Groups actions by category for clarity:
    - Movement actions (2D and 3D)
    - Item usage actions
    - Combat actions
    - System actions
    """
    
    # 2D Movement
    MOVE = "move"
    MOVE_NORTH = "move_north"
    MOVE_SOUTH = "move_south"
    MOVE_EAST = "move_east"
    MOVE_WEST = "move_west"
    
    # 3D Movement
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    STRAFE_LEFT = "strafe_left"
    STRAFE_RIGHT = "strafe_right"
    ROTATE_LEFT = "rotate_left"
    ROTATE_RIGHT = "rotate_right"
    
    # Item Usage
    USE_FOOD = "use_food"
    USE_WEAPON = "use_weapon"
    USE_ELIXIR = "use_elixir"
    USE_SCROLL = "use_scroll"
    
    # Combat
    ATTACK = "attack"
    
    # Interaction
    INTERACT = "interact"
    PICKUP = "pickup"
    WAIT = "wait"
    
    # System
    QUIT = "quit"
    NONE = "none"
    
    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value
    
    @classmethod
    def is_movement(cls, action: 'ActionType') -> bool:
        """Check if action is a movement action."""
        return action in {
            cls.MOVE, cls.MOVE_NORTH, cls.MOVE_SOUTH, 
            cls.MOVE_EAST, cls.MOVE_WEST,
            cls.MOVE_FORWARD, cls.MOVE_BACKWARD,
            cls.STRAFE_LEFT, cls.STRAFE_RIGHT
        }
    
    @classmethod
    def is_rotation(cls, action: 'ActionType') -> bool:
        """Check if action is a rotation action (3D only)."""
        return action in {cls.ROTATE_LEFT, cls.ROTATE_RIGHT}
    
    @classmethod
    def is_item_usage(cls, action: 'ActionType') -> bool:
        """Check if action involves using an item."""
        return action in {
            cls.USE_FOOD, cls.USE_WEAPON, 
            cls.USE_ELIXIR, cls.USE_SCROLL
        }
    
    @classmethod
    def is_3d_only(cls, action: 'ActionType') -> bool:
        """Check if action is only valid in 3D mode."""
        return action in {
            cls.MOVE_FORWARD, cls.MOVE_BACKWARD,
            cls.STRAFE_LEFT, cls.STRAFE_RIGHT,
            cls.ROTATE_LEFT, cls.ROTATE_RIGHT
        }
    
    @classmethod
    def from_string(cls, value: str) -> 'ActionType':
        """
        Convert string to ActionType enum.
        
        Args:
            value: String representation of action type
            
        Returns:
            Corresponding ActionType enum value
            
        Raises:
            ValueError: If string doesn't match any action type
        """
        try:
            return cls(value)
        except ValueError:
            # Try to match by name (case-insensitive)
            for member in cls:
                if member.name.lower() == value.lower():
                    return member
            raise ValueError(f"Unknown action type: {value}")


# Direction mappings for 2D movement
DIRECTION_MAP = {
    ActionType.MOVE_NORTH: (0, -1),
    ActionType.MOVE_SOUTH: (0, 1),
    ActionType.MOVE_EAST: (1, 0),
    ActionType.MOVE_WEST: (-1, 0),
}


# Backward compatibility aliases (deprecated, for migration only)
ACTION_MOVE = ActionType.MOVE
ACTION_USE_FOOD = ActionType.USE_FOOD
ACTION_USE_WEAPON = ActionType.USE_WEAPON
ACTION_USE_ELIXIR = ActionType.USE_ELIXIR
ACTION_USE_SCROLL = ActionType.USE_SCROLL
ACTION_QUIT = ActionType.QUIT
ACTION_NONE = ActionType.NONE
ACTION_MOVE_FORWARD = ActionType.MOVE_FORWARD
ACTION_MOVE_BACKWARD = ActionType.MOVE_BACKWARD
ACTION_STRAFE_LEFT = ActionType.STRAFE_LEFT
ACTION_STRAFE_RIGHT = ActionType.STRAFE_RIGHT
ACTION_ROTATE_LEFT = ActionType.ROTATE_LEFT
ACTION_ROTATE_RIGHT = ActionType.ROTATE_RIGHT
ACTION_INTERACT = ActionType.INTERACT
ACTION_ATTACK = ActionType.ATTACK
ACTION_PICKUP = ActionType.PICKUP
