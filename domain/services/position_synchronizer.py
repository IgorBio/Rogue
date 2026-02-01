"""
Position synchronization system for 2D ↔ 3D view switching.

REFACTORING NOTE (Step 1.4):
- Central system for syncing Character and Camera positions
- Ensures coordinate consistency when switching between 2D and 3D views
- Handles fractional offsets for smooth Camera positioning
- Provides bidirectional synchronization: Character → Camera and Camera → Character
"""

from typing import Tuple, Optional, Any
from domain.entities.position import Position
from domain.entities.character import Character
# Note: Camera is a presentation-layer object; avoid importing it at module level to keep domain layer decoupled.


class PositionSynchronizer:
    """
    Synchronizes positions between Character (2D, int coordinates) and 
    Camera (3D, float coordinates with grid alignment).

    This class ensures that switching between 2D and 3D views maintains
    positional consistency while respecting the different coordinate
    requirements of each system.

    Key responsibilities:
    - Sync Character position to Camera (2D → 3D)
    - Sync Camera position to Character (3D → 2D)
    - Handle fractional offsets for smooth Camera movement
    - Validate position updates
    """

    def __init__(self, center_offset: float = 0.5):
        """
        Initialize synchronizer.

        Args:
            center_offset: Offset to center camera in grid cell (default 0.5)
                          When syncing Character to Camera, camera is placed at
                          (character.x + center_offset, character.y + center_offset)
        """
        self.center_offset = center_offset
        self._last_character_pos: Optional[Tuple[int, int]] = None
        self._last_camera_pos: Optional[Tuple[float, float]] = None

    def sync_camera_to_character(self, camera: Any, character: Character, 
                                 preserve_angle: bool = True) -> None:
        """
        Synchronize Camera position to Character position.

        Places camera at the center of the character's grid cell.
        Useful when switching from 2D to 3D view.

        Args:
            camera: Camera to update
            character: Character to sync from
            preserve_angle: If True, keep camera's current angle

        Example:
            Character at (10, 20) → Camera at (10.5, 20.5)
        """
        char_x, char_y = character.position

        # Place camera at center of character's grid cell
        cam_x = float(char_x) + self.center_offset
        cam_y = float(char_y) + self.center_offset

        # Update camera position
        if preserve_angle:
            old_angle = camera.angle
            camera.set_position(cam_x, cam_y)
            camera.angle = old_angle
        else:
            camera.set_position(cam_x, cam_y)

        # Store for tracking
        self._last_character_pos = (char_x, char_y)
        self._last_camera_pos = (cam_x, cam_y)

    def sync_character_to_camera(self, character: Character, camera: Any,
                                snap_to_grid: bool = True) -> None:
        """
        Synchronize Character position to Camera position.

        Places character on the grid cell where camera is located.
        Useful when switching from 3D to 2D view.

        Args:
            character: Character to update
            camera: Camera to sync from
            snap_to_grid: If True, use camera's grid position (floor)
                         If False, round to nearest grid cell

        Example:
            Camera at (10.5, 20.7) → Character at (10, 20) [snap_to_grid=True]
            Camera at (10.5, 20.7) → Character at (11, 21) [snap_to_grid=False, rounded]
        """
        if snap_to_grid:
            # Use grid position (floor)
            char_x, char_y = camera.grid_position
        else:
            # Round to nearest grid cell
            char_x = round(camera.x)
            char_y = round(camera.y)

        # Update character position
        character.move_to(char_x, char_y)

        # Store for tracking
        self._last_character_pos = (char_x, char_y)
        self._last_camera_pos = (camera.x, camera.y)

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

    def is_camera_moved(self, camera: Any) -> bool:
        """
        Check if camera has moved since last sync.

        Args:
            camera: Camera to check

        Returns:
            bool: True if camera position changed
        """
        if self._last_camera_pos is None:
            return True

        current_pos = (camera.x, camera.y)
        return current_pos != self._last_camera_pos

    def auto_sync_if_needed(self, character: Character, camera: Any,
                           mode: str = 'character_to_camera') -> bool:
        """
        Automatically sync if position changed.

        Args:
            character: Character instance
            camera: Camera instance
            mode: Sync direction ('character_to_camera' or 'camera_to_character')

        Returns:
            bool: True if sync was performed
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

    def get_sync_offset(self, character: Character, camera: Any) -> Tuple[float, float]:
        """
        Calculate current offset between character and camera.

        Args:
            character: Character instance
            camera: Camera instance

        Returns:
            tuple: (offset_x, offset_y) in grid units
        """
        char_x, char_y = character.position
        cam_x, cam_y = camera.x, camera.y

        offset_x = cam_x - char_x
        offset_y = cam_y - char_y

        return (offset_x, offset_y)

    def are_positions_synced(self, character: Character, camera: Any,
                            tolerance: float = 0.1) -> bool:
        """
        Check if character and camera are on the same grid cell.

        Args:
            character: Character instance
            camera: Camera instance
            tolerance: Tolerance for float comparison (not used for grid check)

        Returns:
            bool: True if on same grid cell
        """
        return character.position == camera.grid_position

    def reset_tracking(self) -> None:
        """Reset position tracking (clears last known positions)."""
        self._last_character_pos = None
        self._last_camera_pos = None


class PositionSyncValidator:
    """
    Validator for position synchronization operations.

    Provides utility methods to validate sync operations and detect issues.
    """


class PositionSyncValidator:
    """
    Validator for position synchronization operations.

    Provides utility methods to validate sync operations and detect issues.
    """

    @staticmethod
    def validate_sync(character: Character, camera: Any) -> dict:
        """
        Validate current sync state between character and camera.

        Args:
            character: Character instance
            camera: Any duck-typed camera-like object (expects .x, .y, .grid_position)

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
        cam_pos = (camera.x, camera.y)
        cam_grid = camera.grid_position

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
    def suggest_sync_direction(character: Character, camera: Any) -> str:
        """
        Suggest which sync direction to use based on current state.

        Args:
            character: Character instance
            camera: Any duck-typed camera-like object (expects .x, .y, .grid_position)

        Returns:
            str: Suggested direction ('character_to_camera', 'camera_to_character', or 'none')
        """
        char_pos = character.position
        cam_grid = camera.grid_position

        if char_pos == cam_grid:
            return 'none'  # Already synced

        # If camera is at center of a cell, prefer syncing character to camera
        cam_frac_x = camera.x - int(camera.x)
        cam_frac_y = camera.y - int(camera.y)

        if abs(cam_frac_x - 0.5) < 0.1 and abs(cam_frac_y - 0.5) < 0.1:
            return 'camera_to_character'

        # Default: sync camera to character
        return 'character_to_camera'


# Convenience functions for common operations
def quick_sync_to_2d(character: Character, camera: Any) -> None:
    """
    Quick sync for switching to 2D view (Camera → Character).

    Args:
        character: Character to update
        camera: Camera to sync from
    """
    sync = PositionSynchronizer()
    sync.sync_character_to_camera(character, camera, snap_to_grid=True)


def quick_sync_to_3d(camera: Any, character: Character) -> None:
    """
    Quick sync for switching to 3D view (Character → Camera).

    Args:
        camera: Camera to update
        character: Character to sync from
    """
    sync = PositionSynchronizer()
    sync.sync_camera_to_character(camera, character, preserve_angle=True)
