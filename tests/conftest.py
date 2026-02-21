"""
Pytest configuration and fixtures for Dungeon Crawler tests.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def character():
    from domain.entities.character import Character
    return Character(x=10, y=10)

@pytest.fixture
def character_damaged():
    from domain.entities.character import Character
    char = Character(x=10, y=10)
    char.take_damage(50)
    return char

@pytest.fixture
def zombie_enemy():
    from domain.entities.enemy import create_enemy
    from config.game_config import EnemyType
    return create_enemy(EnemyType.ZOMBIE, x=15, y=15)

@pytest.fixture
def vampire_enemy():
    from domain.entities.enemy import create_enemy
    from config.game_config import EnemyType
    return create_enemy(EnemyType.VAMPIRE, x=15, y=15)

@pytest.fixture
def mimic_enemy():
    from domain.entities.enemy import create_enemy
    from config.game_config import EnemyType
    return create_enemy(EnemyType.MIMIC, x=15, y=15, disguise_type='%')

@pytest.fixture
def food_item():
    from domain.entities.item import Food
    food = Food(health_restoration=30)
    food.position = (10, 10)
    return food

@pytest.fixture
def weapon_item():
    from domain.entities.item import Weapon
    weapon = Weapon(name="Test Sword", strength_bonus=5)
    weapon.position = (10, 10)
    return weapon

@pytest.fixture
def elixir_item():
    from domain.entities.item import Elixir
    from config.game_config import StatType
    elixir = Elixir(stat_type=StatType.STRENGTH, bonus=5, duration=10)
    elixir.position = (10, 10)
    return elixir

@pytest.fixture
def scroll_item():
    from domain.entities.item import Scroll
    from config.game_config import StatType
    scroll = Scroll(stat_type=StatType.STRENGTH, bonus=3)
    scroll.position = (10, 10)
    return scroll

@pytest.fixture
def simple_room():
    from domain.entities.room import Room
    return Room(x=10, y=10, width=10, height=8)

@pytest.fixture
def room_with_enemies(simple_room, zombie_enemy, vampire_enemy):
    simple_room.add_enemy(zombie_enemy)
    simple_room.add_enemy(vampire_enemy)
    return simple_room

@pytest.fixture
def room_with_items(simple_room, food_item, weapon_item):
    simple_room.add_item(food_item)
    simple_room.add_item(weapon_item)
    return simple_room

@pytest.fixture
def simple_corridor():
    from domain.entities.corridor import Corridor
    corridor = Corridor()
    for i in range(5):
        corridor.add_tile(20 + i, 20)
    return corridor

@pytest.fixture
def test_level():
    from domain.level_generator import generate_level
    return generate_level(level_number=1, difficulty_adjustments=None)

@pytest.fixture
def statistics():
    from data.statistics import Statistics
    return Statistics()

@pytest.fixture
def difficulty_manager():
    from domain.dynamic_difficulty import DifficultyManager
    return DifficultyManager()

@pytest.fixture
def save_manager(tmp_path):
    from data.save_manager import SaveManager
    return SaveManager(save_dir=str(tmp_path))

@pytest.fixture
def game_session(statistics, save_manager):
    from domain.game_session import GameSession
    return GameSession(
        test_mode=True,
        test_level=1,
        test_fog_of_war=False,
        statistics_factory=lambda: statistics,
        save_manager_factory=lambda: save_manager,
    )

@pytest.fixture
def game_session_with_fog(statistics, save_manager):
    from domain.game_session import GameSession
    return GameSession(
        test_mode=True,
        test_level=1,
        test_fog_of_war=True,
        statistics_factory=lambda: statistics,
        save_manager_factory=lambda: save_manager,
    )

@pytest.fixture
def camera():
    from presentation.camera import Camera
    return Camera(x=10, y=10, angle=0.0, fov=60.0)

@pytest.fixture
def mock_level_simple():
    from domain.entities.level import Level
    from domain.entities.room import Room
    from domain.entities.corridor import Corridor
    level = Level(level_number=1)
    room1 = Room(x=5, y=5, width=10, height=8)
    room2 = Room(x=20, y=5, width=10, height=8)
    level.add_room(room1)
    level.add_room(room2)
    corridor = Corridor()
    for x in range(15, 20):
        corridor.add_tile(x, 9)
    level.add_corridor(corridor)
    level.starting_room_index = 0
    level.exit_room_index = 1
    level.exit_position = (25, 9)

    return level

def pytest_configure(config):
    config.addinivalue_line(
        "markers", """slow: marks tests as slow (deselect with '-m "not slow"')"""
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


class TestHelper:
    @staticmethod
    def create_character_at_health_percent(percent):
        from domain.entities.character import Character
        char = Character(0, 0)
        char.health = int(char.max_health * percent)
        return char

    @staticmethod
    def create_enemy_with_stats(enemy_type, health, strength, dexterity):
        from domain.entities.enemy import create_enemy
        enemy = create_enemy(enemy_type, 0, 0)
        enemy.health = health
        enemy.max_health = health
        enemy.strength = strength
        enemy.dexterity = dexterity
        return enemy


@pytest.fixture
def test_helper():
    return TestHelper()
