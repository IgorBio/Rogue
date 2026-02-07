"""
Camera class for 3D rendering.

Represents the player's camera in 3D space with position, angle, and FOV.
"""
import math
from typing import Tuple, Optional
from domain.entities.position import Position


class RayHit:
    """Represents the result of a ray cast."""

    def __init__(self, distance: float, wall_type: str, texture_x: float,
                 hit_x: int, hit_y: int, side: str, door=None):
        """
        Initialize a ray hit result.

        Args:
            distance: Perpendicular distance to wall (fisheye corrected)
            wall_type: Type of wall hit ('room_wall', 'corridor_wall', 'door_open', 'door_locked')
            texture_x: X coordinate on texture (0.0 - 1.0)
            hit_x: Grid X coordinate where ray hit
            hit_y: Grid Y coordinate where ray hit
            side: Which side was hit ('NS' for north/south, 'EW' for east/west)
            door: Door object if the hit wall is a door (optional)
        """
        self.distance = distance
        self.wall_type = wall_type
        self.texture_x = texture_x
        self.hit_x = hit_x
        self.hit_y = hit_y
        self.side = side
        self.door = door


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
