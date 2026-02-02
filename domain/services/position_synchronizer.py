"""
Position synchronization system for 2D ↔ 3D view switching.
"""

import warnings
from typing import Tuple, Optional, Any
from domain.entities.position import Position
from domain.entities.character import Character


def _deprecated(msg):
    """Simple deprecation decorator using warnings."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated: {msg}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


class PositionSynchronizer:
    """
    Synchronizes positions between domain objects (Character and Position).

    This class ensures positional consistency while respecting the different
    coordinate requirements of each system.

    Key responsibilities:
    - Track position changes for domain objects
    - Provide coordinate conversion utilities via Position class methods
    - Validate position updates
    """

    def __init__(self, center_offset: float = 0.5):
        """
        Initialize synchronizer.

        Args:
            center_offset: Offset to center camera in grid cell (default 0.5)
                          Used for coordinate conversion via Position.to_camera_coords()
        """
        self.center_offset = center_offset
        self._last_character_pos: Optional[Tuple[int, int]] = None
        self._last_camera_pos: Optional[Tuple[float, float]] = None

    def sync_character_to_position(self, character: Character, position: Position) -> None:
        """
        Synchronize Character position to Position.

        Args:
            character: Character to update
            position: Position to sync from
        """
        character.move_to(position.x, position.y)
        self._last_character_pos = character.position

    def is_character_moved(self, character: Character) -> bool:
        """
        Check if character has moved since last sync.

        Args:
            character: Character to check

        Returns:
            bool: True if character position changed
        """
        if self._last_character_pos is None:
            return True

        return character.position != self._last_character_pos

    def get_character_offset(self, character: Character,
                            camera_coords: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calculate offset between character and camera coordinates.

        Args:
            character: Character instance
            camera_coords: Camera (x, y) coordinates

        Returns:
            tuple: (offset_x, offset_y) in grid units
        """
        char_x, char_y = character.position
        cam_x, cam_y = camera_coords

        offset_x = cam_x - char_x
        offset_y = cam_y - char_y

        return (offset_x, offset_y)

    def are_positions_aligned(self, character: Character,
                             camera_coords: Tuple[float, float]) -> bool:
        """
        Check if character and camera are on the same grid cell.

        Args:
            character: Character instance
            camera_coords: Camera (x, y) coordinates

        Returns:
            bool: True if on same grid cell
        """
        char_pos = Position(*character.position)
        expected_cam = char_pos.to_camera_coords(self.center_offset)
        
        # Check if camera is at expected position (same grid cell)
        cam_x, cam_y = camera_coords
        expected_x, expected_y = expected_cam
        
        return (int(cam_x) == int(expected_x) and
                int(cam_y) == int(expected_y))

    def reset_tracking(self) -> None:
        """Reset position tracking (clears last known positions)."""
        self._last_character_pos = None
        self._last_camera_pos = None

    @_deprecated("Use presentation.camera_sync.CameraSync.sync_camera_to_character")
    def sync_camera_to_character(self, camera: Any, character: Character,
                                 preserve_angle: bool = True) -> None:
        """
        DEPRECATED: Use presentation.camera_sync.CameraSync.sync_camera_to_character
        
        Synchronize Camera position to Character position.
        """
        from presentation.camera_sync import CameraSync
        sync = CameraSync(self.center_offset)
        sync.sync_camera_to_character(camera, character, preserve_angle)
        
        # Update tracking state for backward compatibility
        self._last_character_pos = character.position
        self._last_camera_pos = (camera.x, camera.y)
    
    @_deprecated("Use presentation.camera_sync.CameraSync.sync_character_from_camera")
    def sync_character_to_camera(self, character: Character, camera: Any,
                                snap_to_grid: bool = True) -> None:
        """
        DEPRECATED: Use presentation.camera_sync.CameraSync.sync_character_from_camera
        
        Synchronize Character position to Camera position.
        """
        from presentation.camera_sync import CameraSync
        sync = CameraSync(self.center_offset)
        sync.sync_character_from_camera(character, camera,
                                        snap_mode='floor' if snap_to_grid else 'round')
        
        # Update tracking state for backward compatibility
        self._last_character_pos = character.position
        self._last_camera_pos = (camera.x, camera.y)
    
    @_deprecated("Camera tracking moved to presentation layer")
    def is_camera_moved(self, camera: Any) -> bool:
        """
        DEPRECATED: Camera tracking moved to presentation layer
        
        Check if camera has moved since last sync.
        """
        if self._last_camera_pos is None:
            return True
        current_pos = (camera.x, camera.y)
        return current_pos != self._last_camera_pos
    
    @_deprecated("Use presentation.camera_sync.CameraSync methods directly")
    def auto_sync_if_needed(self, character: Character, camera: Any,
                           mode: str = 'character_to_camera') -> bool:
        """
        DEPRECATED: Use presentation.camera_sync.CameraSync methods directly
        """
        if mode == 'character_to_camera':
            if self.is_character_moved(character):
                self.sync_camera_to_character(camera, character)
                return True
        elif mode == 'camera_to_character':
            if self.is_camera_moved(camera):
                self.sync_character_to_camera(character, camera)
                return True
        
        return False
    
    @_deprecated("Use presentation.camera_sync.CameraSync.calculate_offset")
    def get_sync_offset(self, character: Character, camera: Any) -> Tuple[float, float]:
        """
        DEPRECATED: Use presentation.camera_sync.CameraSync.calculate_offset
        """
        char_x, char_y = character.position
        cam_x, cam_y = camera.x, camera.y
        return (cam_x - char_x, cam_y - char_y)
    
    @_deprecated("Use presentation.camera_sync.CameraSync.is_camera_at_position")
    def are_positions_synced(self, character: Character, camera: Any,
                            tolerance: float = 0.1) -> bool:
        """
        DEPRECATED: Use presentation.camera_sync.CameraSync.is_camera_at_position
        
        Check if character and camera are on the same grid cell.
        """
        # Check if camera has grid_position attribute
        if hasattr(camera, 'grid_position'):
            return character.position == camera.grid_position
        else:
            # Fallback: calculate grid position from coordinates
            cam_grid = Position.from_camera_coords(camera.x, camera.y, snap_mode='floor').tuple
            return character.position == cam_grid


class PositionSyncValidator:
    """
    Validator for position synchronization operations.

    Provides utility methods to validate sync operations and detect issues.
    """

    @staticmethod
    def validate_sync(character: Character,
                     camera: Any,
                     center_offset: float = 0.5) -> dict:
        """
        Validate current sync state between character and camera.

        Args:
            character: Character instance
            camera: Camera instance or (x, y) coordinates tuple
            center_offset: Expected camera offset (default 0.5)

        Returns:
            dict: Validation results with keys:
                - 'is_synced': bool
                - 'character_pos': tuple
                - 'camera_pos': tuple
                - 'camera_grid_pos': tuple
                - 'offset': tuple
                - 'issues': list of issue strings
        """
        char_pos = character.position
        
        # Handle both Camera object and tuple for backward compatibility
        if isinstance(camera, tuple):
            cam_pos = camera
            cam_grid = Position.from_camera_coords(cam_pos[0], cam_pos[1], snap_mode='floor').tuple
        else:
            cam_pos = (camera.x, camera.y)
            # Try to get grid_position if available, otherwise calculate
            if hasattr(camera, 'grid_position'):
                cam_grid = camera.grid_position
            else:
                cam_grid = Position.from_camera_coords(cam_pos[0], cam_pos[1], snap_mode='floor').tuple

        offset_x = cam_pos[0] - char_pos[0]
        offset_y = cam_pos[1] - char_pos[1]

        is_synced = (char_pos == cam_grid)

        issues = []
        if not is_synced:
            issues.append(f"Grid mismatch: Character at {char_pos}, Camera grid at {cam_grid}")

        # Check for extreme offsets
        if abs(offset_x) > 2.0 or abs(offset_y) > 2.0:
            issues.append(f"Large offset detected: ({offset_x:.2f}, {offset_y:.2f})")

        return {
            'is_synced': is_synced,
            'character_pos': char_pos,
            'camera_pos': cam_pos,
            'camera_grid_pos': cam_grid,
            'offset': (offset_x, offset_y),
            'issues': issues
        }

    @staticmethod
    def suggest_sync_direction(character: Character,
                              camera: Any) -> str:
        """
        Suggest which sync direction to use based on current state.

        Args:
            character: Character instance
            camera: Camera instance or (x, y) coordinates tuple

        Returns:
            str: Suggested direction ('character_to_camera', 'camera_to_character', or 'none')
        """
        char_pos = character.position
        
        # Handle both Camera object and tuple for backward compatibility
        if isinstance(camera, tuple):
            cam_x, cam_y = camera
            cam_grid = Position.from_camera_coords(cam_x, cam_y, snap_mode='floor').tuple
        else:
            cam_x, cam_y = camera.x, camera.y
            if hasattr(camera, 'grid_position'):
                cam_grid = camera.grid_position
            else:
                cam_grid = Position.from_camera_coords(cam_x, cam_y, snap_mode='floor').tuple

        if char_pos == cam_grid:
            return 'none'  # Already synced

        # If camera is at center of a cell, prefer syncing character to camera
        cam_frac_x = cam_x - int(cam_x)
        cam_frac_y = cam_y - int(cam_y)

        if abs(cam_frac_x - 0.5) < 0.1 and abs(cam_frac_y - 0.5) < 0.1:
            return 'camera_to_character'

        # Default: sync camera to character
        return 'character_to_camera'



def quick_sync_character_to_camera_coords(character: Character,
                                         camera_coords: Tuple[float, float],
                                         snap_mode: str = 'floor') -> None:
    """
    Quick sync character to camera coordinates (Camera → Character).

    Args:
        character: Character to update
        camera_coords: Camera (x, y) coordinates
        snap_mode: 'floor' or 'round' for coordinate conversion
    """
    position = Position.from_camera_coords(camera_coords[0], camera_coords[1], snap_mode)
    character.move_to(position.x, position.y)


def quick_sync_camera_coords_to_position(camera_coords: Tuple[float, float],
                                        center_offset: float = 0.5) -> Tuple[float, float]:
    """
    Convert position to camera coordinates (Character → Camera).

    Args:
        camera_coords: Source coordinates (for position extraction)
        center_offset: Camera center offset
    
    Returns:
        Tuple[float, float]: Camera coordinates with offset
    """
    position = Position.from_camera_coords(camera_coords[0], camera_coords[1])
    return position.to_camera_coords(center_offset)



@_deprecated("Use presentation.camera_sync.CameraSync.sync_character_from_camera")
def quick_sync_to_2d(character, camera):
    """
    DEPRECATED: Use presentation.camera_sync.CameraSync.sync_character_from_camera
    
    Quick sync for switching to 2D view (Camera → Character).
    
    Args:
        character: Character to update
        camera: Camera to sync from
    """
    # Import here to avoid circular dependency
    from presentation.camera_sync import CameraSync
    sync = CameraSync()
    sync.sync_character_from_camera(character, camera)


@_deprecated("Use presentation.camera_sync.CameraSync.sync_camera_to_character")
def quick_sync_to_3d(camera, character):
    """
    DEPRECATED: Use presentation.camera_sync.CameraSync.sync_camera_to_character
    
    Quick sync for switching to 3D view (Character → Camera).
    
    Args:
        camera: Camera to update
        character: Character to sync from
    """
    # Import here to avoid circular dependency
    from presentation.camera_sync import CameraSync
    sync = CameraSync()
    sync.sync_camera_to_character(camera, character)


def create_synced_pair(character_factory, camera_factory, x, y, center_offset=0.5):
    """
    Create a synchronized pair of Character and Camera.
    
    Args:
        character_factory: Factory to create Character
        camera_factory: Factory to create Camera
        x: Initial X position (grid)
        y: Initial Y position (grid)
        center_offset: Camera center offset
    
    Returns:
        tuple: (character, camera)
    """
    # Import here to avoid circular dependency
    from presentation.camera_sync import CameraSync
    
    character = character_factory(x, y)
    position = Position(x, y)
    cam_x, cam_y = position.to_camera_coords(center_offset)
    camera = camera_factory(cam_x, cam_y)
    
    return (character, camera)
