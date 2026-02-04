"""
Coordinate system for the game.
"""

from typing import Tuple, Union


class Position:
    """
    Class for managing position in the game.

    Attributes:
        _x (int): X coordinate
        _y (int): Y coordinate
    """

    def __init__(self, x: Union[int, float], y: Union[int, float]):
        """
        Initialize position.

        Args:
            x: X coordinate (will be converted to int)
            y: Y coordinate (will be converted to int)
        """
        self._x = int(x)
        self._y = int(y)

    @property
    def x(self) -> int:
        """Get X coordinate"""
        return self._x

    @property
    def y(self) -> int:
        """Get Y coordinate"""
        return self._y

    @property
    def tuple(self) -> Tuple[int, int]:
        """Get position as tuple (x, y)"""
        return (self._x, self._y)

    def update(self, x: Union[int, float], y: Union[int, float]) -> None:
        """
        Update position (with automatic conversion to int).

        Args:
            x: New X coordinate
            y: New Y coordinate
        """
        self._x = int(x)
        self._y = int(y)

    def move_by(self, dx: Union[int, float], dy: Union[int, float]) -> None:
        """
        Move position by delta.

        Args:
            dx: Change in X coordinate
            dy: Change in Y coordinate
        """
        self._x += int(dx)
        self._y += int(dy)

    def distance_to(self, other: Union['Position', Tuple[int, int]]) -> float:
        """
        Calculate Euclidean distance to another position.

        Args:
            other: Another position or coordinate tuple

        Returns:
            float: Distance
        """
        if isinstance(other, Position):
            dx = self._x - other._x
            dy = self._y - other._y
        else:
            dx = self._x - other[0]
            dy = self._y - other[1]

        return (dx * dx + dy * dy) ** 0.5

    def manhattan_distance_to(self, other: Union['Position', Tuple[int, int]]) -> int:
        """
        Calculate Manhattan distance to another position.

        Args:
            other: Another position or coordinate tuple

        Returns:
            int: Manhattan distance
        """
        if isinstance(other, Position):
            return abs(self._x - other._x) + abs(self._y - other._y)
        else:
            return abs(self._x - other[0]) + abs(self._y - other[1])

    def copy(self) -> 'Position':
        """
        Create a copy of the position.

        Returns:
            Position: New object with same coordinates
        """
        return Position(self._x, self._y)

    def to_camera_coords(self, offset: float = 0.5) -> Tuple[float, float]:
        """
        Convert grid position to camera coordinates.

        Camera uses float coordinates with offset for centering
        in grid cell (e.g., 10.5 instead of 10).

        Args:
            offset: Centering offset (default 0.5)

        Returns:
            Tuple[float, float]: Camera coordinates (x, y)
        """
        return (float(self._x) + offset, float(self._y) + offset)

    @classmethod
    def from_camera_coords(cls, x: float, y: float,
                          snap_mode: str = 'floor') -> 'Position':
        """
        Create Position from camera coordinates.

        Args:
            x: Camera X coordinate (float)
            y: Camera Y coordinate (float)
            snap_mode: Rounding method:
                      'floor' — round down (int())
                      'round' — round to nearest

        Returns:
            Position: New position with int coordinates
        """
        if snap_mode == 'floor':
            return cls(int(x), int(y))
        elif snap_mode == 'round':
            return cls(round(x), round(y))
        else:
            raise ValueError(f"Unknown snap_mode: {snap_mode}")

    def is_adjacent_to(self, other: Union['Position', Tuple[int, int]]) -> bool:
        """
        Check if position is adjacent (including diagonals).
        Positions are considered adjacent if they differ by at most 1 on each axis.

        Args:
            other: Another position or coordinate tuple

        Returns:
            bool: True if positions are adjacent
        """
        if isinstance(other, Position):
            other_x, other_y = other._x, other._y
        else:
            other_x, other_y = other[0], other[1]

        # Check that difference on each axis <= 1
        dx = abs(self._x - other_x)
        dy = abs(self._y - other_y)

        # Adjacent if both <= 1 but not both == 0 (not same position)
        return dx <= 1 and dy <= 1 and (dx != 0 or dy != 0)

    def __eq__(self, other) -> bool:
        """
        Compare position with another position or tuple.

        Args:
            other: Position, tuple or any object

        Returns:
            bool: True if positions are equal
        """
        if isinstance(other, Position):
            return self._x == other._x and self._y == other._y
        if isinstance(other, tuple) and len(other) == 2:
            return self._x == other[0] and self._y == other[1]
        return False

    def __ne__(self, other) -> bool:
        """Check inequality"""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries"""
        return hash((self._x, self._y))

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"Position({self._x}, {self._y})"

    def __str__(self) -> str:
        """String representation for user"""
        return f"({self._x}, {self._y})"

    def __iter__(self):
        """Allows unpacking: x, y = position"""
        return iter((self._x, self._y))

    def __getitem__(self, index: int) -> int:
        """Allow subscript access: position[0] == x, position[1] == y"""
        if index == 0:
            return self._x
        elif index == 1:
            return self._y
        else:
            raise IndexError("Position index out of range (only 0 and 1 are valid)")


# Helper functions for backward compatibility

def create_position(x, y):
    """
    Factory function to create a Position.
    
    Args:
        x: X coordinate (int or float)
        y: Y coordinate (int or float)
    
    Returns:
        Position: New Position instance
    """
    return Position(x, y)


def positions_equal(pos1, pos2):
    """
    Check if two positions are equal.
    
    Args:
        pos1: First position (Position or tuple)
        pos2: Second position (Position or tuple)
    
    Returns:
        bool: True if positions are equal
    """
    if isinstance(pos1, Position) and isinstance(pos2, Position):
        return pos1 == pos2
    if isinstance(pos1, Position):
        return pos1 == pos2
    if isinstance(pos2, Position):
        return pos2 == pos1
    return pos1 == pos2
