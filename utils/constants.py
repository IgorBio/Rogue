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

# Item types
class ItemType:
    TREASURE = "treasure"
    FOOD = "food"
    ELIXIR = "elixir"
    SCROLL = "scroll"
    WEAPON = "weapon"
    KEY = "key"

# Elixir/Scroll stat types
class StatType:
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    MAX_HEALTH = "max_health"

# Enemy types
class EnemyType:
    ZOMBIE = "zombie"
    VAMPIRE = "vampire"
    GHOST = "ghost"
    OGRE = "ogre"
    SNAKE_MAGE = "snake_mage"
    MIMIC = "mimic"  # Stage 26: Added Mimic

# Enemy base stats (health, strength, dexterity, hostility)
ENEMY_STATS = {
    EnemyType.ZOMBIE: {
        'health': 40,
        'strength': 8,
        'dexterity': 4,
        'hostility': 5,
        'char': 'z',
        'color': 'green'
    },
    EnemyType.VAMPIRE: {
        'health': 50,
        'strength': 7,
        'dexterity': 12,
        'hostility': 8,
        'char': 'v',
        'color': 'red'
    },
    EnemyType.GHOST: {
        'health': 20,
        'strength': 5,
        'dexterity': 13,
        'hostility': 3,
        'char': 'g',
        'color': 'white'
    },
    EnemyType.OGRE: {
        'health': 80,
        'strength': 15,
        'dexterity': 3,
        'hostility': 6,
        'char': 'o',
        'color': 'yellow'
    },
    EnemyType.SNAKE_MAGE: {
        'health': 35,
        'strength': 6,
        'dexterity': 15,
        'hostility': 7,
        'char': 's',
        'color': 'white'
    },
    EnemyType.MIMIC: {
        'health': 60,
        'strength': 4,
        'dexterity': 14,
        'hostility': 2,
        'char': 'm',
        'color': 'white'
    }
}

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