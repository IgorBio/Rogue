"""
Position synchronization utilities for domain objects.
"""

from typing import Tuple, Optional
from domain.entities.position import Position
from domain.entities.character import Character


class PositionSynchronizer:
    """
    Synchronizes positions between domain objects (Character and Position).

    Domain-only responsibilities:
    - Track character position changes
    - Provide alignment checks against camera coordinates (tuples)
    """

    def __init__(self, center_offset: float = 0.5):
        self.center_offset = center_offset
        self._last_character_pos: Optional[Tuple[int, int]] = None

    def sync_character_to_position(self, character: Character, position: Position) -> None:
        """Synchronize Character position to Position."""
        character.move_to(position.x, position.y)
        self._last_character_pos = character.position

    def is_character_moved(self, character: Character) -> bool:
        """Check if character has moved since last sync."""
        if self._last_character_pos is None:
            return True
        return character.position != self._last_character_pos

    def get_character_offset(self, character: Character,
                             camera_coords: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate offset between character and camera coordinates."""
        char_x, char_y = character.position
        cam_x, cam_y = camera_coords
        return (cam_x - char_x, cam_y - char_y)

    def are_positions_aligned(self, character: Character,
                              camera_coords: Tuple[float, float]) -> bool:
        """Check if character and camera are on the same grid cell."""
        char_pos = Position(*character.position)
        expected_x, expected_y = char_pos.to_camera_coords(self.center_offset)
        cam_x, cam_y = camera_coords
        return (int(cam_x) == int(expected_x) and int(cam_y) == int(expected_y))

    def reset_tracking(self) -> None:
        """Reset position tracking."""
        self._last_character_pos = None


class PositionSyncValidator:
    """Validator for position synchronization operations."""

    @staticmethod
    def validate_sync(character: Character,
                      camera_coords: Tuple[float, float],
                      center_offset: float = 0.5) -> dict:
        """Validate current sync state between character and camera coords."""
        char_pos = character.position
        cam_pos = camera_coords
        cam_grid = Position.from_camera_coords(cam_pos[0], cam_pos[1], snap_mode='floor').tuple

        offset_x = cam_pos[0] - char_pos[0]
        offset_y = cam_pos[1] - char_pos[1]

        is_synced = (char_pos == cam_grid)

        issues = []
        if not is_synced:
            issues.append(f"Grid mismatch: Character at {char_pos}, Camera grid at {cam_grid}")
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
                               camera_coords: Tuple[float, float]) -> str:
        """Suggest which sync direction to use based on current state."""
        char_pos = character.position
        cam_x, cam_y = camera_coords
        cam_grid = Position.from_camera_coords(cam_x, cam_y, snap_mode='floor').tuple

        if char_pos == cam_grid:
            return 'none'

        cam_frac_x = cam_x - int(cam_x)
        cam_frac_y = cam_y - int(cam_y)

        if abs(cam_frac_x - 0.5) < 0.1 and abs(cam_frac_y - 0.5) < 0.1:
            return 'camera_to_character'

        return 'character_to_camera'


def quick_sync_character_to_camera_coords(character: Character,
                                           camera_coords: Tuple[float, float],
                                           snap_mode: str = 'floor') -> None:
    """Quick sync character to camera coordinates (Camera -> Character)."""
    position = Position.from_camera_coords(camera_coords[0], camera_coords[1], snap_mode)
    character.move_to(position.x, position.y)


def quick_sync_camera_coords_to_position(camera_coords: Tuple[float, float],
                                          center_offset: float = 0.5) -> Tuple[float, float]:
    """Convert position to camera coordinates (Character -> Camera)."""
    position = Position.from_camera_coords(camera_coords[0], camera_coords[1])
    return position.to_camera_coords(center_offset)
