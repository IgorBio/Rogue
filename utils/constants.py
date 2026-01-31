"""
Game constants and configuration values.
Stage 26: Added MIMIC enemy type.
"""

# Map dimensions
MAP_WIDTH = 80
MAP_HEIGHT = 24

# Game structure
ROOM_COUNT = 9
LEVEL_COUNT = 21
ROOMS_PER_ROW = 3

# Section dimensions for 3x3 grid
SECTION_WIDTH = MAP_WIDTH // ROOMS_PER_ROW
SECTION_HEIGHT = MAP_HEIGHT // ROOMS_PER_ROW

# Room size constraints
MIN_ROOM_WIDTH = 5
MAX_ROOM_WIDTH = 12
MIN_ROOM_HEIGHT = 4
MAX_ROOM_HEIGHT = 7

# Initial player stats
INITIAL_PLAYER_HEALTH = 100
INITIAL_PLAYER_MAX_HEALTH = 100
INITIAL_PLAYER_STRENGTH = 10
INITIAL_PLAYER_DEXTERITY = 10

# Backpack
MAX_ITEMS_PER_TYPE = 9

# Minimum health if elixir expiry would kill player
MIN_HEALTH_AFTER_ELIXIR_EXPIRY = 1  

# Item/Enemy/Stat constants moved to config/game_config.py
# Removed here to avoid duplication — use:
#   from config.game_config import ItemType, StatType, EnemyType, ENEMY_STATS

# Difficulty scaling
ENEMY_COUNT_BASE = 3
ENEMY_COUNT_PER_LEVEL = 0.5
MAX_ENEMIES_PER_LEVEL = 25
ENEMY_STAT_SCALING = 1.05

# Item spawn rates (base values - scale down with level)
FOOD_SPAWN_RATE = 0.6
ELIXIR_SPAWN_RATE = 0.3
SCROLL_SPAWN_RATE = 0.2
WEAPON_SPAWN_RATE = 0.15

# Mimic spawn rate (Stage 26)
MIMIC_SPAWN_RATE = 0.15  # 15% chance to spawn mimics instead of items

# Treasure scaling
TREASURE_LEVEL_MULTIPLIER = 0.1