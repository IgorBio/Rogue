"""
Procedural level generation for dungeon floors.

This module generates randomized dungeon levels with rooms, corridors,
enemies, items, and doors. Integrates with dynamic difficulty adjustment
to scale challenge based on player performance.
"""
import random
from domain.entities.level import Level
from domain.entities.room import Room
from domain.entities.corridor import Corridor
from domain.entities.item import Food, Weapon, Elixir, Scroll
from domain.entities.enemy import create_enemy
from domain.key_door_system import place_keys_and_doors
from config.game_config import GameConfig, ItemConfig, EnemyConfig
from config.game_config import EnemyType, StatType


# Room/map layout constants (use GameConfig directly)
ROOM_COUNT = GameConfig.ROOM_COUNT
ROOMS_PER_ROW = GameConfig.ROOMS_PER_ROW
SECTION_WIDTH = GameConfig.SECTION_WIDTH
SECTION_HEIGHT = GameConfig.SECTION_HEIGHT
MIN_ROOM_WIDTH = GameConfig.MIN_ROOM_WIDTH
MAX_ROOM_WIDTH = GameConfig.MAX_ROOM_WIDTH
MIN_ROOM_HEIGHT = GameConfig.MIN_ROOM_HEIGHT
MAX_ROOM_HEIGHT = GameConfig.MAX_ROOM_HEIGHT


# Level generation constants (migrated to GameConfig/ItemConfig/EnemyConfig)
MIN_STARTING_LEVEL = GameConfig.MIN_STARTING_LEVEL if hasattr(GameConfig, 'MIN_STARTING_LEVEL') else 1
MIN_ENEMIES_PER_LEVEL = GameConfig.MIN_ENEMIES_PER_LEVEL if hasattr(GameConfig, 'MIN_ENEMIES_PER_LEVEL') else 2
MIN_FOOD_ITEMS = GameConfig.MIN_FOOD_ITEMS if hasattr(GameConfig, 'MIN_FOOD_ITEMS') else 2
MIN_WEAPON_ITEMS = GameConfig.MIN_WEAPON_ITEMS if hasattr(GameConfig, 'MIN_WEAPON_ITEMS') else 1
MAX_ENEMIES_PER_ROOM = GameConfig.MAX_ENEMIES_PER_ROOM if hasattr(GameConfig, 'MAX_ENEMIES_PER_ROOM') else 4

# Enemy spawn / scaling (from EnemyConfig)
ENEMY_COUNT_BASE = EnemyConfig.ENEMY_COUNT_BASE
ENEMY_COUNT_PER_LEVEL = EnemyConfig.ENEMY_COUNT_PER_LEVEL
MAX_ENEMIES_PER_LEVEL = EnemyConfig.MAX_ENEMIES_PER_LEVEL
ENEMY_STAT_SCALING = EnemyConfig.ENEMY_STAT_SCALING

# Item spawn rates (from ItemConfig)
FOOD_SPAWN_RATE = ItemConfig.FOOD_SPAWN_RATE
WEAPON_SPAWN_RATE = ItemConfig.WEAPON_SPAWN_RATE
ELIXIR_SPAWN_RATE = ItemConfig.ELIXIR_SPAWN_RATE
SCROLL_SPAWN_RATE = ItemConfig.SCROLL_SPAWN_RATE
MIMIC_SPAWN_RATE = ItemConfig.MIMIC_SPAWN_RATE

# Legacy treasure multiplier (kept for compatibility)
TREASURE_LEVEL_MULTIPLIER = 0.1

# Enemy distribution by level tier
TIER_1_LEVEL = EnemyConfig.TIER_1_LEVEL
TIER_2_LEVEL = EnemyConfig.TIER_2_LEVEL
MIMIC_MIN_LEVEL = ItemConfig.MIMIC_MIN_LEVEL

# Weapon generation
WEAPON_BASE_BONUS_MIN = ItemConfig.WEAPON_BASE_BONUS_MIN
WEAPON_BASE_BONUS_MAX = ItemConfig.WEAPON_BASE_BONUS_MAX
WEAPON_BONUS_PER_THREE_LEVELS = ItemConfig.WEAPON_BONUS_PER_THREE_LEVELS

# Food generation
FOOD_BASE_HEALING_MIN = ItemConfig.FOOD_BASE_HEALING_MIN
FOOD_BASE_HEALING_MAX = ItemConfig.FOOD_BASE_HEALING_MAX
FOOD_HEALING_PER_LEVEL = ItemConfig.FOOD_HEALING_PER_LEVEL

# Elixir generation
ELIXIR_BASE_BONUS_MIN = ItemConfig.ELIXIR_BASE_BONUS_MIN
ELIXIR_BASE_BONUS_MAX = ItemConfig.ELIXIR_BASE_BONUS_MAX
ELIXIR_BONUS_PER_FOUR_LEVELS = ItemConfig.ELIXIR_BONUS_PER_FOUR_LEVELS
ELIXIR_DURATION_MIN = ItemConfig.ELIXIR_DURATION_MIN
ELIXIR_DURATION_MAX = ItemConfig.ELIXIR_DURATION_MAX

# Scroll generation
SCROLL_BASE_BONUS_MIN = ItemConfig.SCROLL_BASE_BONUS_MIN
SCROLL_BASE_BONUS_MAX = ItemConfig.SCROLL_BASE_BONUS_MAX
SCROLL_BONUS_PER_FIVE_LEVELS = ItemConfig.SCROLL_BONUS_PER_FIVE_LEVELS

# Weapon names
WEAPON_NAMES = ItemConfig.WEAPON_NAMES

# Level factor calculation
LEVEL_FACTOR_DIVISOR = GameConfig.LEVEL_FACTOR_DIVISOR
MIN_LEVEL_FACTOR = GameConfig.MIN_LEVEL_FACTOR


def generate_level(level_number, difficulty_adjustments=None):
    """
    Generate a complete dungeon level with rooms and corridors.
    
    Args:
        level_number: Current level number
        difficulty_adjustments: Optional dict with difficulty modifiers
    
    Returns:
        Level: Generated level instance
    """
    level = Level(level_number)
    
    rooms = _generate_rooms()
    for room in rooms:
        level.add_room(room)
    
    corridors = _generate_corridors(rooms)
    for corridor in corridors:
        level.add_corridor(corridor)
    
    level.starting_room_index = random.randint(0, ROOM_COUNT - 1)
    exit_choices = [i for i in range(ROOM_COUNT) if i != level.starting_room_index]
    level.exit_room_index = random.choice(exit_choices)
    
    exit_room = level.rooms[level.exit_room_index]
    level.exit_position = exit_room.get_center()
    
    _spawn_enemies(level, difficulty_adjustments)
    _spawn_items(level, difficulty_adjustments)
    
    if level_number >= MIN_STARTING_LEVEL:
        place_keys_and_doors(level)
    
    return level


def _generate_rooms():
    """Generate 9 rooms in a 3x3 grid layout."""
    rooms = []
    
    for row in range(ROOMS_PER_ROW):
        for col in range(ROOMS_PER_ROW):
            section_x = col * SECTION_WIDTH
            section_y = row * SECTION_HEIGHT
            
            room_width = random.randint(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH)
            room_height = random.randint(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT)
            
            max_x = section_x + SECTION_WIDTH - room_width - 1
            max_y = section_y + SECTION_HEIGHT - room_height - 1
            
            room_x = random.randint(section_x + 1, max(section_x + 1, max_x))
            room_y = random.randint(section_y + 1, max(section_y + 1, max_y))
            
            room = Room(room_x, room_y, room_width, room_height)
            rooms.append(room)
    
    return rooms


def _generate_corridors(rooms):
    """Generate corridors connecting all 9 rooms."""
    corridors = []
    
    for row in range(ROOMS_PER_ROW):
        for col in range(ROOMS_PER_ROW - 1):
            room_index = row * ROOMS_PER_ROW + col
            next_room_index = room_index + 1
            
            corridor = _connect_rooms_horizontal(
                rooms[room_index],
                rooms[next_room_index]
            )
            corridors.append(corridor)
    
    for col in range(ROOMS_PER_ROW):
        for row in range(ROOMS_PER_ROW - 1):
            room_index = row * ROOMS_PER_ROW + col
            below_room_index = room_index + ROOMS_PER_ROW
            
            corridor = _connect_rooms_vertical(
                rooms[room_index],
                rooms[below_room_index]
            )
            corridors.append(corridor)
    
    return corridors


def _connect_rooms_horizontal(room1, room2):
    """Create a horizontal corridor between two rooms."""
    corridor = Corridor()
    
    x1 = room1.x + room1.width - 1
    y1 = room1.y + room1.height // 2
    
    x2 = room2.x
    y2 = room2.y + room2.height // 2
    
    mid_x = (x1 + x2) // 2
    
    for x in range(x1, mid_x + 1):
        corridor.add_tile(x, y1)
    
    start_y = min(y1, y2)
    end_y = max(y1, y2)
    for y in range(start_y, end_y + 1):
        corridor.add_tile(mid_x, y)
    
    for x in range(mid_x, x2 + 1):
        corridor.add_tile(x, y2)
    
    return corridor


def _connect_rooms_vertical(room1, room2):
    """Create a vertical corridor between two rooms."""
    corridor = Corridor()
    
    x1 = room1.x + room1.width // 2
    y1 = room1.y + room1.height - 1
    
    x2 = room2.x + room2.width // 2
    y2 = room2.y
    
    mid_y = (y1 + y2) // 2
    
    for y in range(y1, mid_y + 1):
        corridor.add_tile(x1, y)
    
    start_x = min(x1, x2)
    end_x = max(x1, x2)
    for x in range(start_x, end_x + 1):
        corridor.add_tile(x, mid_y)
    
    for y in range(mid_y, y2 + 1):
        corridor.add_tile(x2, y)
    
    return corridor


def _spawn_enemies(level, difficulty_adjustments=None):
    """
    Spawn enemies in the level based on difficulty.
    
    Args:
        level: Level object
        difficulty_adjustments: Optional dict with difficulty modifiers
    """

    enemy_count = int(ENEMY_COUNT_BASE + (level.level_number * ENEMY_COUNT_PER_LEVEL))
    
    if difficulty_adjustments:
        enemy_modifier = difficulty_adjustments.get('enemy_count_modifier', 1.0)
        enemy_count = int(enemy_count * enemy_modifier)
    
    enemy_count = min(max(enemy_count, MIN_ENEMIES_PER_LEVEL), MAX_ENEMIES_PER_LEVEL)
    
    available_rooms = [i for i in range(len(level.rooms)) 
                      if i != level.starting_room_index]
    
    if not available_rooms:
        return
    
    enemy_types = _get_enemy_distribution(level.level_number)
    
    enemies_spawned = 0
    while enemies_spawned < enemy_count and available_rooms:
        room_idx = random.choice(available_rooms)
        room = level.rooms[room_idx]
        
        enemy_type = random.choice(enemy_types)
        pos = room.get_random_floor_position()
        
        enemy = create_enemy(enemy_type, pos[0], pos[1])
        _scale_enemy_stats(enemy, level.level_number, difficulty_adjustments)
        
        room.add_enemy(enemy)
        enemies_spawned += 1
        
        if len(room.enemies) >= MAX_ENEMIES_PER_ROOM:
            available_rooms.remove(room_idx)


def _get_enemy_distribution(level_number):
    """Get the enemy type distribution for a given level."""
    if level_number <= TIER_1_LEVEL:
        return (
            [EnemyType.ZOMBIE] * 5 +
            [EnemyType.VAMPIRE] * 1 +
            [EnemyType.GHOST] * 1
        )
    elif level_number <= TIER_2_LEVEL:
        return (
            [EnemyType.ZOMBIE] * 3 +
            [EnemyType.VAMPIRE] * 2 +
            [EnemyType.GHOST] * 2 +
            [EnemyType.OGRE] * 2 +
            [EnemyType.SNAKE_MAGE] * 1
        )
    else:
        return (
            [EnemyType.ZOMBIE] * 2 +
            [EnemyType.VAMPIRE] * 2 +
            [EnemyType.GHOST] * 3 +
            [EnemyType.OGRE] * 3 +
            [EnemyType.SNAKE_MAGE] * 3
        )


def _scale_enemy_stats(enemy, level_number, difficulty_adjustments=None):
    """
    Scale enemy stats based on level difficulty.
    
    Args:
        enemy: Enemy instance
        level_number: Current level number
        difficulty_adjustments: Optional dict with difficulty modifiers
    """
    if level_number <= 1:
        base_scaling = 1.0
    else:
        base_scaling = ENEMY_STAT_SCALING ** (level_number - 1)
    
    if difficulty_adjustments:
        stat_modifier = difficulty_adjustments.get('enemy_stat_modifier', 1.0)
        scaling_factor = base_scaling * stat_modifier
    else:
        scaling_factor = base_scaling
    
    enemy.max_health = int(enemy.max_health * scaling_factor)
    enemy.health = enemy.max_health
    enemy.strength = int(enemy.strength * scaling_factor)
    enemy.dexterity = int(enemy.dexterity * scaling_factor)


def _spawn_items(level, difficulty_adjustments=None):
    """
    Spawn items in the level based on difficulty.
    
    Args:
        level: Level object
        difficulty_adjustments: Optional dict with difficulty modifiers
    """
    
    available_rooms = [i for i in range(len(level.rooms)) 
                      if i != level.starting_room_index]
    
    if not available_rooms:
        return
    
    level_factor = max(MIN_LEVEL_FACTOR, 1.0 - (level.level_number / LEVEL_FACTOR_DIVISOR))
    
    if difficulty_adjustments:
        item_modifier = difficulty_adjustments.get('item_spawn_modifier', 1.0)
        healing_modifier = difficulty_adjustments.get('healing_modifier', 1.0)
        level_factor *= item_modifier
    else:
        healing_modifier = 1.0
    
    food_count = int(FOOD_SPAWN_RATE * len(available_rooms) * level_factor * healing_modifier)
    weapon_count = int(WEAPON_SPAWN_RATE * len(available_rooms))
    elixir_count = int(ELIXIR_SPAWN_RATE * len(available_rooms) * level_factor)
    scroll_count = int(SCROLL_SPAWN_RATE * len(available_rooms) * level_factor)
    
    food_count = max(MIN_FOOD_ITEMS, food_count)
    weapon_count = max(MIN_WEAPON_ITEMS, weapon_count)
    
    for _ in range(food_count):
        _spawn_food_or_mimic(level, available_rooms, healing_modifier)
    
    for _ in range(weapon_count):
        _spawn_weapon_or_mimic(level, available_rooms, difficulty_adjustments)
    
    for _ in range(elixir_count):
        _spawn_elixir_or_mimic(level, available_rooms, difficulty_adjustments)
    
    for _ in range(scroll_count):
        _spawn_scroll_or_mimic(level, available_rooms, difficulty_adjustments)


def _spawn_food_or_mimic(level, available_rooms, healing_modifier):
    """Spawn food item or mimic disguised as food."""
    
    room_idx = random.choice(available_rooms)
    room = level.rooms[room_idx]
    pos = room.get_random_floor_position()
    
    if random.random() < MIMIC_SPAWN_RATE and level.level_number >= MIMIC_MIN_LEVEL:
        mimic = create_enemy(EnemyType.MIMIC, pos[0], pos[1], disguise_type='%')
        _scale_enemy_stats(mimic, level.level_number)
        room.add_enemy(mimic)
    else:
        base_healing = random.randint(FOOD_BASE_HEALING_MIN, FOOD_BASE_HEALING_MAX)
        level_bonus = level.level_number * FOOD_HEALING_PER_LEVEL
        healing = int((base_healing + level_bonus) * healing_modifier)
        
        food = Food(healing)
        food.position = pos
        room.add_item(food)


def _spawn_weapon_or_mimic(level, available_rooms, difficulty_adjustments):
    """Spawn weapon item or mimic disguised as weapon."""
    
    room_idx = random.choice(available_rooms)
    room = level.rooms[room_idx]
    pos = room.get_random_floor_position()
    
    if random.random() < MIMIC_SPAWN_RATE and level.level_number >= MIMIC_MIN_LEVEL:
        mimic = create_enemy(EnemyType.MIMIC, pos[0], pos[1], disguise_type='(')
        _scale_enemy_stats(mimic, level.level_number, difficulty_adjustments)
        room.add_enemy(mimic)
    else:
        base_bonus = random.randint(WEAPON_BASE_BONUS_MIN, WEAPON_BASE_BONUS_MAX)
        level_bonus = level.level_number // WEAPON_BONUS_PER_THREE_LEVELS
        weapon_bonus = base_bonus + level_bonus
        
        weapon_name = random.choice(WEAPON_NAMES)
        
        weapon = Weapon(f"{weapon_name} +{weapon_bonus}", weapon_bonus)
        weapon.position = pos
        room.add_item(weapon)


def _spawn_elixir_or_mimic(level, available_rooms, difficulty_adjustments):
    """Spawn elixir item or mimic disguised as elixir."""
    
    room_idx = random.choice(available_rooms)
    room = level.rooms[room_idx]
    pos = room.get_random_floor_position()
    
    if random.random() < MIMIC_SPAWN_RATE and level.level_number >= MIMIC_MIN_LEVEL:
        mimic = create_enemy(EnemyType.MIMIC, pos[0], pos[1], disguise_type='!')
        _scale_enemy_stats(mimic, level.level_number, difficulty_adjustments)
        room.add_enemy(mimic)
    else:
        stat_type = random.choice([StatType.STRENGTH, StatType.DEXTERITY, StatType.MAX_HEALTH])
        
        base_bonus = random.randint(ELIXIR_BASE_BONUS_MIN, ELIXIR_BASE_BONUS_MAX)
        level_bonus = level.level_number // ELIXIR_BONUS_PER_FOUR_LEVELS
        bonus = base_bonus + level_bonus
        
        duration = random.randint(ELIXIR_DURATION_MIN, ELIXIR_DURATION_MAX)
        
        elixir = Elixir(stat_type, bonus, duration)
        elixir.position = pos
        room.add_item(elixir)


def _spawn_scroll_or_mimic(level, available_rooms, difficulty_adjustments):
    """Spawn scroll item or mimic disguised as scroll."""
    
    room_idx = random.choice(available_rooms)
    room = level.rooms[room_idx]
    pos = room.get_random_floor_position()
    
    if random.random() < MIMIC_SPAWN_RATE and level.level_number >= MIMIC_MIN_LEVEL:
        mimic = create_enemy(EnemyType.MIMIC, pos[0], pos[1], disguise_type='?')
        _scale_enemy_stats(mimic, level.level_number, difficulty_adjustments)
        room.add_enemy(mimic)
    else:
        stat_type = random.choice([StatType.STRENGTH, StatType.DEXTERITY, StatType.MAX_HEALTH])
        
        base_bonus = random.randint(SCROLL_BASE_BONUS_MIN, SCROLL_BASE_BONUS_MAX)
        level_bonus = level.level_number // SCROLL_BONUS_PER_FIVE_LEVELS
        bonus = base_bonus + level_bonus
        
        scroll = Scroll(stat_type, bonus)
        scroll.position = pos
        room.add_item(scroll)


def spawn_emergency_healing(level, character_position):
    """
    Spawn emergency healing near the player when they're struggling.
    
    Args:
        level: Current level
        character_position: (x, y) tuple of player position
    
    Returns:
        bool: True if healing was spawned, False otherwise
    """

    room, room_idx = level.get_room_at(character_position[0], character_position[1])
    
    if not room:
        return False
    
    px, py = character_position
    
    adjacent_positions = [
        (px - 1, py),
        (px + 1, py),
        (px, py - 1),
        (px, py + 1),
    ]
    
    for pos in adjacent_positions:
        if room.contains_point(pos[0], pos[1]):
            if not _is_position_occupied(pos, room):
                healing = 40 + (level.level_number * 3)
                food = Food(healing)
                food.position = pos
                room.add_item(food)
                return True
    
    for _ in range(5):
        pos = room.get_random_floor_position()
        
        if not _is_position_occupied(pos, room):
            healing = 40 + (level.level_number * 3)
            food = Food(healing)
            food.position = pos
            room.add_item(food)
            return True
    
    return False


def _is_position_occupied(pos, room):
    """Check if a position is occupied by an enemy or item."""
    for enemy in room.enemies:
        if enemy.position == pos:
            return True
    
    for item in room.items:
        if item.position == pos:
            return True
    
    return False