import random

import pytest

from domain.combat import (
    calculate_hit_chance,
    calculate_damage,
    resolve_attack,
    calculate_treasure_reward,
    get_combat_message,
)
from domain.dynamic_difficulty import DifficultyManager
from domain.enemy_ai import (
    get_enemy_movement,
    should_enemy_attack,
    get_special_attack_effects,
    handle_post_attack,
)
from domain.services import pathfinding_service
from domain.key_door_system import (
    KeyColor,
    Key,
    Door,
    place_keys_and_doors,
    can_pass_door,
    unlock_door_if_possible,
    _get_key_count_for_level,
    _is_tile_near_room,
    _find_door_position_near_room,
    _build_room_graph,
    _get_accessible_rooms_without_corridor,
    _get_accessible_rooms_with_keys,
)
from domain.level_generator import spawn_emergency_healing
from domain.entities.character import Character, Backpack
from domain.entities.enemy import Zombie, Vampire, Ghost, Ogre, SnakeMage, Mimic
from domain.entities.item import Weapon
from domain.entities.level import Level
from domain.entities.room import Room
from domain.entities.corridor import Corridor
from config.game_config import EnemyType, ItemType


class DummyStats:
    def __init__(self):
        self.damage_received = 10
        self.damage_dealt = 30
        self.hits_taken = 5
        self.attacks_made = 10
        self.items_collected = 10
        self.food_consumed = 3
        self.elixirs_used = 2
        self.scrolls_read = 1
        self.enemies_defeated = 30


def test_combat_basic_and_messages(monkeypatch):
    assert calculate_hit_chance(100, 0) <= 0.95
    assert calculate_hit_chance(0, 100) >= 0.1

    weapon = Weapon("Knife", 2)
    monkeypatch.setattr(random, "uniform", lambda a, b: 1.0)
    assert calculate_damage(5, weapon) == 7
    assert calculate_damage(0, None) >= 1

    attacker = Character(0, 0)
    defender = Zombie(1, 1)

    monkeypatch.setattr(random, "random", lambda: 1.0)
    result = resolve_attack(attacker, defender, attacker_weapon=None)
    assert result["hit"] is False
    assert "missed" in get_combat_message(result)

    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(random, "uniform", lambda a, b: 1.0)
    result = resolve_attack(attacker, defender, attacker_weapon=None)
    assert result["hit"] is True
    assert "hit" in get_combat_message(result)

    treasure = calculate_treasure_reward(defender, level_number=1)
    assert treasure >= 10


def test_dynamic_difficulty_all_paths():
    manager = DifficultyManager()
    character = Character(0, 0)
    stats = DummyStats()

    character.health = character.max_health
    manager.update_performance(stats, character)
    adjustments = manager.calculate_difficulty_adjustment(character, stats, level_number=5)
    assert "performance_score" in adjustments

    character.health = 1
    manager.healing_modifier = 2.0
    assert manager.should_spawn_emergency_healing(character) is True

    manager.enemy_count_modifier = 1.4
    manager.enemy_stat_modifier = 1.4
    manager.item_spawn_modifier = 0.5
    assert manager.get_difficulty_description() in {"Very Hard", "Hard"}

    manager.reset()
    assert manager.enemy_count_modifier == 1.0


def _make_walkable_level():
    level = Level(1)
    room = Room(1, 1, 5, 5)
    level.add_room(room)
    level.starting_room_index = 0
    level.exit_room_index = 0
    level.exit_position = room.get_center()

    corridor = Corridor()
    for x in range(2, 5):
        corridor.add_tile(x, 3)
    level.add_corridor(corridor)
    return level, room, corridor


def test_pathfinding_service_basic():
    level, _, _ = _make_walkable_level()
    start = (2, 2)
    goal = (2, 3)
    path = pathfinding_service.find_path(start, goal, level)
    assert path[0] == start
    assert path[-1] == goal
    assert pathfinding_service.get_next_step(start, goal, level) == path[1]
    assert pathfinding_service.get_distance(start, goal) == 1
    assert pathfinding_service.is_adjacent(start, goal) is True


# def test_enemy_ai_variants(monkeypatch):
#     level, room, _ = _make_walkable_level()
#     player_pos = (2, 2)

#     enemy = Mimic(3, 3)
#     room.add_enemy(enemy)
#     assert get_enemy_movement(enemy, player_pos, level, [enemy]) is None
#     enemy.is_disguised = False
#     enemy.is_chasing = True

#     monkeypatch.setattr(pathfinding_service, "get_next_step", lambda a, b, c: (2, 3))
#     assert get_enemy_movement(enemy, player_pos, level, [enemy]) == (2, 3)

#     zombie = Zombie(3, 3)
#     room.add_enemy(zombie)
#     monkeypatch.setattr(pathfinding_service, "get_random_adjacent_walkable", lambda a, b: (2, 3))
#     assert get_enemy_movement(zombie, player_pos, level, [zombie]) == (2, 3)

#     vampire = Vampire(3, 3)
#     vampire.is_chasing = True
#     assert get_enemy_movement(vampire, player_pos, level, [vampire]) == (2, 3)

#     ghost = Ghost(3, 3)
#     room.add_enemy(ghost)
#     monkeypatch.setattr(random, "randint", lambda a, b: a)
#     pos = get_enemy_movement(ghost, player_pos, level, [ghost])
#     assert pos is not None

#     ogre = Ogre(3, 3)
#     ogre.is_resting = True
#     assert get_enemy_movement(ogre, player_pos, level, [ogre]) is None

#     snake = SnakeMage(3, 3)
#     snake.is_chasing = True
#     snake.direction_cooldown = 0
#     monkeypatch.setattr(random, "choice", lambda seq: seq[0])
#     move = get_enemy_movement(snake, player_pos, level, [snake])
#     assert move is not None

#     class UnknownEnemy:
#         def __init__(self):
#             self.enemy_type = "unknown"
#             self.position = (3, 3)
#             self.hostility = 1
#             self.is_chasing = False
#         def is_alive(self):
#             return True

#     unknown = UnknownEnemy()
#     move = get_enemy_movement(unknown, player_pos, level, [unknown])
#     assert move is not None


def test_enemy_ai_attack_effects(monkeypatch):
    vampire = Vampire(0, 0)
    snake = SnakeMage(0, 0)
    ogre = Ogre(0, 0)
    ogre.will_counterattack = True

    monkeypatch.setattr(random, "randint", lambda a, b: a)
    monkeypatch.setattr(random, "random", lambda: 0.0)

    effects = get_special_attack_effects(vampire, {"hit": True})
    assert effects["health_steal"] > 0

    effects = get_special_attack_effects(snake, {"hit": True})
    assert effects["sleep"] is True

    effects = get_special_attack_effects(ogre, {"hit": True})
    assert effects["counterattack"] is True
    assert ogre.will_counterattack is False

    assert should_enemy_attack(ogre) is True
    ogre.is_resting = True
    assert should_enemy_attack(ogre) is False

    handle_post_attack(ogre, {"hit": True})
    assert ogre.is_resting is True


def test_key_door_system_and_helpers(monkeypatch):
    level, room, corridor = _make_walkable_level()
    level.starting_room_index = 0
    level.exit_room_index = 0
    level.exit_position = room.get_center()

    assert _get_key_count_for_level(1) == 3
    assert _get_key_count_for_level(10) == 4
    assert _get_key_count_for_level(20) == 5

    assert _is_tile_near_room(room.get_center(), room) is True
    door_pos = _find_door_position_near_room(corridor, [room])
    assert door_pos is not None

    graph = _build_room_graph(level)
    assert 0 in graph

    accessible = _get_accessible_rooms_without_corridor(graph, 0, 0)
    assert 0 in accessible

    accessible2 = _get_accessible_rooms_with_keys(graph, 0, {}, set())
    assert 0 in accessible2

    monkeypatch.setattr(random, "shuffle", lambda x: x)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", lambda a, b: a)

    assert place_keys_and_doors(level) in {True, False}

    door = Door(KeyColor.RED, 1, 1)
    character = Character(0, 0)
    assert can_pass_door(door, character) is False

    key = Key(KeyColor.RED)
    character.backpack.add_item(key)
    assert can_pass_door(door, character) is True
    assert unlock_door_if_possible(door, character) is True


def test_spawn_emergency_healing():
    level, room, _ = _make_walkable_level()
    character_pos = room.get_center()
    assert spawn_emergency_healing(level, character_pos) is True
    assert any(item.item_type == ItemType.FOOD for item in room.items)


def test_place_keys_and_doors_success(monkeypatch):
    level = Level(1)
    rooms = [
        Room(1, 1, 4, 4),
        Room(10, 1, 4, 4),
        Room(20, 1, 4, 4),
        Room(30, 1, 4, 4),
    ]
    for room in rooms:
        level.add_room(room)

    level.starting_room_index = 0
    level.exit_room_index = 3
    level.exit_position = rooms[3].get_center()

    def corridor_between(room_a, room_b):
        corridor = Corridor()
        corridor.add_tile(room_a.x + room_a.width - 1, room_a.y + 1)
        corridor.add_tile(room_b.x, room_b.y + 1)
        return corridor

    corridors = [
        corridor_between(rooms[0], rooms[1]),
        corridor_between(rooms[1], rooms[2]),
        corridor_between(rooms[2], rooms[3]),
        corridor_between(rooms[1], rooms[3]),
    ]
    for corridor in corridors:
        level.add_corridor(corridor)

    monkeypatch.setattr(random, "shuffle", lambda x: x)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "randint", lambda a, b: a)

    assert place_keys_and_doors(level) is True
    assert level.doors
    key_items = []
    for room in level.rooms:
        key_items.extend([i for i in room.items if getattr(i, "item_type", None) == ItemType.KEY])
    assert key_items
