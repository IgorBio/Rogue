"""
Camera synchronization for presentation layer.

This module handles synchronization between domain Position/Character
and presentation Camera objects. It uses Position.to_camera_coords()
for coordinate transformation, keeping domain layer clean.

Usage:
    from presentation.camera_sync import CameraSync
    from domain.entities.position import Position
    
    camera_sync = CameraSync()
    
    # Sync camera to character position
    camera_sync.sync_camera_to_character(camera, character)
    
    # Or sync to specific position
    position = Position(10, 20)
    camera_sync.sync_camera_to_position(camera, position)
"""

from typing import Tuple, Optional, Any
from domain.entities.position import Position
from domain.entities.character import Character


class CameraSync:
    """
    Synchronizes Camera with domain Position/Character.
    
    This is a presentation-layer class that manages the relationship
    between domain positions (int grid coordinates) and presentation
    camera (float coordinates with offsets).
    
    Attributes:
        center_offset: Offset to center camera in grid cell (default 0.5)
        _last_position: Last known position for tracking changes
    
    Example:
        camera_sync = CameraSync(center_offset=0.5)
        camera_sync.sync_camera_to_character(camera, character)
    """
    
    def __init__(self, center_offset: float = 0.5):
        """
        Initialize camera sync.
        
        Args:
            center_offset: Offset to center camera in grid cell (default 0.5)
        """
        self.center_offset = center_offset
        self._last_position: Optional[Tuple[float, float]] = None
    
    def sync_camera_to_position(self, camera: Any, position: Position,
                                preserve_angle: bool = True) -> None:
        """
        Synchronize Camera position to Position.
        
        Places camera at the center of the grid cell.
        
        Args:
            camera: Camera to update
            position: Position to sync from
            preserve_angle: If True, keep camera's current angle
        
        Example:
            Position(10, 20) → Camera at (10.5, 20.5)
        """
        cam_x, cam_y = position.to_camera_coords(self.center_offset)
        
        if preserve_angle:
            old_angle = getattr(camera, 'angle', 0)
            camera.set_position(cam_x, cam_y)
            camera.angle = old_angle
        else:
            camera.set_position(cam_x, cam_y)
        
        self._last_position = (cam_x, cam_y)
    
    def sync_camera_to_character(self, camera: Any, character: Character,
                                 preserve_angle: bool = True) -> None:
        """
        Synchronize Camera position to Character position.

        Args:
            camera: Camera to update
            character: Character to sync from
            preserve_angle: If True, keep camera's current angle

        Example:
            Character at (10, 20) → Camera at (10.5, 20.5)
        """
        position = Position(*character.position)
        self.sync_camera_to_position(camera, position, preserve_angle)

    def sync_character_from_camera(self, character: Character, camera: Any,
                                  snap_mode: str = 'floor') -> None:
        """
        Synchronize Character position from Camera position.

        Args:
            character: Character to update
            camera: Camera to sync from
            snap_mode: 'floor' or 'round' for coordinate conversion

        Example:
            Camera at (10.5, 20.7) → Character at (10, 20) [floor]
            Camera at (10.5, 20.7) → Character at (11, 21) [round]
        """
        position = Position.from_camera_coords(camera.x, camera.y, snap_mode)
        character.move_to(position.x, position.y)
    
    def sync_camera_to_coords(self, camera: Any, x: int, y: int,
                             preserve_angle: bool = True) -> None:
        """
        Synchronize Camera to specific grid coordinates.
        
        Args:
            camera: Camera to update
            x: Grid X coordinate
            y: Grid Y coordinate
            preserve_angle: If True, keep camera's current angle
        """
        position = Position(x, y)
        self.sync_camera_to_position(camera, position, preserve_angle)
    
    def get_camera_grid_position(self, camera: Any) -> Tuple[int, int]:
        """
        Get grid position from camera coordinates.
        
        Args:
            camera: Camera instance
        
        Returns:
            Tuple[int, int]: Grid coordinates (x, y)
        """
        # Use Position.from_camera_coords with floor mode
        pos = Position.from_camera_coords(camera.x, camera.y, snap_mode='floor')
        return pos.tuple
    
    def is_camera_at_position(self, camera: Any, position: Position,
                             tolerance: float = 0.01) -> bool:
        """
        Check if camera is at specific position (considering offset).
        
        Args:
            camera: Camera to check
            position: Position to compare with
            tolerance: Tolerance for float comparison
        
        Returns:
            bool: True if camera is at position
        """
        expected_x, expected_y = position.to_camera_coords(self.center_offset)
        actual_x, actual_y = camera.x, camera.y
        
        return (abs(actual_x - expected_x) < tolerance and 
                abs(actual_y - expected_y) < tolerance)
    
    def calculate_offset(self, camera: Any, position: Position) -> Tuple[float, float]:
        """
        Calculate offset between camera and position.
        
        Args:
            camera: Camera instance
            position: Position to compare with
        
        Returns:
            Tuple[float, float]: (offset_x, offset_y)
        """
        expected_x, expected_y = position.to_camera_coords(self.center_offset)
        return (camera.x - expected_x, camera.y - expected_y)
    
    def reset(self) -> None:
        """Reset tracking state."""
        self._last_position = None


# Global instance for application-wide use
camera_sync = CameraSync()
