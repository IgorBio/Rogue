"""
Centralized game configuration.
All magic numbers and settings in one place.
"""


class GameConfig:
    """Core game parameters"""

    # === LEVELS ===
    TOTAL_LEVELS = 21
    MIN_STARTING_LEVEL = 1

    # === LEVEL GENERATION ===
    LEVEL_FACTOR_DIVISOR = 30
    MIN_LEVEL_FACTOR = 0.3

    # Enemies
    MIN_ENEMIES_PER_LEVEL = 2
    MAX_ENEMIES_PER_ROOM = 4

    # Items
    MIN_FOOD_ITEMS = 2
    MIN_WEAPON_ITEMS = 1

    # === DIFFICULTY SYSTEM ===
    # Health thresholds
    HEALTH_EXCELLENT_THRESHOLD = 0.8
    HEALTH_GOOD_THRESHOLD = 0.6
    HEALTH_AVERAGE_THRESHOLD = 0.4
    HEALTH_LOW_THRESHOLD = 0.2

    TREASURE_LEVEL_MULTIPLIER = 0.1

    # Damage thresholds
    DAMAGE_RATIO_EXCELLENT = 3.0
    DAMAGE_RATIO_STRONG = 2.0
    DAMAGE_RATIO_AHEAD = 1.0
    DAMAGE_RATIO_BEHIND = 0.5
    DAMAGE_RATIO_STRUGGLING = 0.3

    # Item usage
    ITEM_USAGE_EFFICIENT = 0.5
    ITEM_USAGE_AVERAGE = 0.3

    # Difficulty modifiers
    MIN_DIFFICULTY_MODIFIER = 0.5
    MAX_DIFFICULTY_MODIFIER = 1.5
    ADJUSTMENT_RATE = 0.1
    DRIFT_RATE_FACTOR = 0.3

    # Performance thresholds
    PERFORMANCE_EXCELLENT = 1.3
    PERFORMANCE_STRUGGLING = 0.8
    COMBAT_MULTIPLIER_LOW = 0.5
    COMBAT_MULTIPLIER_HIGH = 1.5

    # Emergency healing
    EMERGENCY_HEALTH_THRESHOLD = 0.25
    CRITICAL_HEALTH_THRESHOLD = 0.15
    EMERGENCY_HEALING_MODIFIER = 1.2

    # === TEST MODE ===
    TEST_MODE_STATS = {
        'health': 999,
        'max_health': 999,
        'strength': 999,
        'dexterity': 999
    }

    # === CAMERA (3D) ===
    DEFAULT_CAMERA_ANGLE = 0.0
    DEFAULT_CAMERA_FOV = 60.0

    # === ROOMS AND CORRIDORS ===
    ROOM_COUNT = 9
    ROOMS_PER_ROW = 3
    MIN_ROOM_WIDTH = 8
    MAX_ROOM_WIDTH = 20
    MIN_ROOM_HEIGHT = 5
    MAX_ROOM_HEIGHT = 7

    # Map dimensions
    MAP_WIDTH = 80
    MAP_HEIGHT = 24

    # Section dimensions for 3x3 grid
    SECTION_WIDTH = MAP_WIDTH // ROOMS_PER_ROW
    SECTION_HEIGHT = MAP_HEIGHT // ROOMS_PER_ROW


class ItemConfig:
    """Item configuration"""

    # Weapons
    WEAPON_BASE_BONUS_MIN = 3
    WEAPON_BASE_BONUS_MAX = 8
    WEAPON_BONUS_PER_THREE_LEVELS = 1
    WEAPON_NAMES = ["Dagger", "Sword", "Axe", "Mace", "Spear", "Hammer"]

    # Food
    FOOD_BASE_HEALING_MIN = 15
    FOOD_BASE_HEALING_MAX = 30
    FOOD_HEALING_PER_LEVEL = 2

    # Elixirs
    ELIXIR_BASE_BONUS_MIN = 3
    ELIXIR_BASE_BONUS_MAX = 8
    ELIXIR_BONUS_PER_FOUR_LEVELS = 1
    ELIXIR_DURATION_MIN = 5
    ELIXIR_DURATION_MAX = 15

    # Scrolls
    SCROLL_BASE_BONUS_MIN = 2
    SCROLL_BASE_BONUS_MAX = 5
    SCROLL_BONUS_PER_FIVE_LEVELS = 1

    # Spawn rates
    FOOD_SPAWN_RATE = 0.5
    WEAPON_SPAWN_RATE = 0.3
    ELIXIR_SPAWN_RATE = 0.25
    SCROLL_SPAWN_RATE = 0.2
    MIMIC_SPAWN_RATE = 0.15
    MIMIC_MIN_LEVEL = 5


class EnemyConfig:
    """Enemy configuration"""

    # Generation
    ENEMY_COUNT_BASE = 3
    ENEMY_COUNT_PER_LEVEL = 1
    MAX_ENEMIES_PER_LEVEL = 15
    ENEMY_STAT_SCALING = 1.1

    # Appearance levels
    TIER_1_LEVEL = 7
    TIER_2_LEVEL = 14

    # AI behavior
    GHOST_TELEPORT_COOLDOWN_MIN = 3
    GHOST_TELEPORT_COOLDOWN_MAX = 5
    GHOST_INVISIBILITY_COOLDOWN_MIN = 4
    GHOST_INVISIBILITY_COOLDOWN_MAX = 7

    SNAKE_MAGE_DIRECTION_COOLDOWN_MIN = 3
    SNAKE_MAGE_DIRECTION_COOLDOWN_MAX = 6
    SNAKE_MAGE_SLEEP_CHANCE = 0.3

    VAMPIRE_HEALTH_STEAL_MIN = 2
    VAMPIRE_HEALTH_STEAL_MAX = 5


class PlayerConfig:
    """Player configuration"""

    INITIAL_HEALTH = 100
    INITIAL_MAX_HEALTH = 100
    INITIAL_STRENGTH = 10
    INITIAL_DEXTERITY = 10

    MAX_ITEMS_PER_TYPE = 10
    MIN_HEALTH_AFTER_ELIXIR_EXPIRY = 1

    # Adjacent cells for dropping items
    ADJACENT_OFFSETS = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (1, -1), (-1, 1), (1, 1)
    ]


class CameraConfig:
    """Конфигурация 3D камеры."""
    GRID_CELL_SIZE = 1.0  # Размер одной клетки в мировых единицах
    CAMERA_OFFSET = 0.5   # Смещение камеры от угла клетки (центрирование)
    MOVE_SPEED = 1.0      # Скорость = 1 клетка за шаг
    ROTATION_SPEED = 15.0  # градусов за шаг
    COLLISION_RADIUS = 0.3  # радиус коллизии в мировых единицах


# Type classes
class ItemType:
    TREASURE = "treasure"
    FOOD = "food"
    ELIXIR = "elixir"
    SCROLL = "scroll"
    WEAPON = "weapon"
    KEY = "key"


class StatType:
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    MAX_HEALTH = "max_health"


class EnemyType:
    ZOMBIE = "zombie"
    VAMPIRE = "vampire"
    GHOST = "ghost"
    OGRE = "ogre"
    SNAKE_MAGE = "snake_mage"
    MIMIC = "mimic"


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
