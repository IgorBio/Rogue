"""EnemyLocator: helpers to find enemies and items inside a Level.

Small, focused service to keep `GameSession` thin while keeping lookup
logic testable and reusable by other services (movement, combat).
"""
from typing import Optional, Tuple
from config.game_config import EnemyType


class EnemyLocator:
    def __init__(self):
        pass

    def get_disguised_mimic_at(self, level, x: int, y: int):
        """Return a disguised mimic at (x,y) or None."""
        for room in level.rooms:
            for enemy in room.enemies:
                if (enemy.position == (x, y) and
                    enemy.is_alive() and
                    enemy.enemy_type == EnemyType.MIMIC and
                    getattr(enemy, 'is_disguised', False)):
                    return enemy
        return None

    def get_revealed_enemy_at(self, level, x: int, y: int):
        """Return a revealed (non-disguised) enemy at (x,y) or None."""
        for room in level.rooms:
            for enemy in room.enemies:
                if enemy.position == (x, y) and enemy.is_alive():
                    if (enemy.enemy_type == EnemyType.MIMIC and
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
