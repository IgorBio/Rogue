"""
Synchronization helpers for presentation-domain layer coordination.

This module contains utilities that bridge presentation and domain layers,
such as creating synchronized Character-Camera pairs.
"""
from typing import Tuple, Any

from domain.entities.character import Character
from utils.raycasting import Camera


def create_synced_pair(character_pos: Tuple[int, int], angle: float = 0.0,
                       fov: float = 60.0, center_offset: float = 0.5) -> Tuple[Character, Any]:
    """
    Create a synchronized Character and Camera pair.

    Args:
        character_pos: (x, y) position for character
        angle: Camera viewing angle in degrees
        fov: Camera field of view in degrees
        center_offset: Offset for centering camera

    Returns:
        tuple: (character, camera) - both synced to same position
    """
    char_x, char_y = character_pos

    character = Character(char_x, char_y)
    camera = Camera(
        char_x + center_offset,
        char_y + center_offset,
        angle=angle,
        fov=fov
    )

    return character, camera
