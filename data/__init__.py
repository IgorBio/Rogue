"""
Data Layer - Persistence and Statistics Management.

This package handles all data persistence operations including:
- Save/load game state to JSON files
- Statistics tracking and leaderboard management
- Game session recovery and state restoration
"""

from data.save_manager import SaveManager
from data.statistics import Statistics, StatisticsManager

__all__ = [
    'SaveManager',
    'Statistics',
    'StatisticsManager',
]