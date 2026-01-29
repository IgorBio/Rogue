"""
Configuration package for Dungeon Crawler.
Contains centralized game configuration and constants.
"""

from .game_config import (
    GameConfig,
    ItemConfig,
    EnemyConfig,
    PlayerConfig,
    SaveConfig,
    get_config_summary,
    validate_config
)

__all__ = [
    'GameConfig',
    'ItemConfig',
    'EnemyConfig',
    'PlayerConfig',
    'SaveConfig',
    'get_config_summary',
    'validate_config'
]

# Валидация при импорте
validate_config()
