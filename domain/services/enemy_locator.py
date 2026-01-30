"""EnemyLocator: helpers to find enemies and items inside a Level.

Small, focused service to keep `GameSession` thin while keeping lookup
logic testable and reusable by other services (movement, combat).
"""
from typing import Optional, Tuple
from config.game_config import EnemyType

# Normalize constant name for robust comparisons (supports Enum or raw string)
MIMIC_NAME = getattr(EnemyType.MIMIC, 'name', str(EnemyType.MIMIC))


def _enemy_type_name(enemy):
    et = getattr(enemy, 'enemy_type', None)
    if et is None:
        return None
    if hasattr(et, 'name'):
        return et.name
    return str(et)


class EnemyLocator:
    def __init__(self):
        pass

    def get_disguised_mimic_at(self, level, x: int, y: int):
        """Return a disguised mimic at (x,y) or None."""
        for room in level.rooms:
            for enemy in room.enemies:
                if (enemy.position == (x, y) and
                    enemy.is_alive() and
                    _enemy_type_name(enemy) == MIMIC_NAME and
                    getattr(enemy, 'is_disguised', False)):
                    return enemy
        return None

    def get_revealed_enemy_at(self, level, x: int, y: int):
        """Return a revealed (non-disguised) enemy at (x,y) or None."""
        for room in level.rooms:
            for enemy in room.enemies:
                if enemy.position == (x, y) and enemy.is_alive():
                    if (_enemy_type_name(enemy) == MIMIC_NAME and
                            getattr(enemy, 'is_disguised', False)):
                        continue
                    return enemy
        return None

    def get_enemy_room(self, level, enemy):
        """Return the room containing `enemy` or None."""
        for room in level.rooms:
            if enemy in room.enemies:
                return room
        return None

    def get_item_at(self, level, x: int, y: int):
        """Return item at (x,y) in the level, or None."""
        for room in level.rooms:
            for item in room.items:
                if item.position and item.position == (x, y):
                    return item
        return None
