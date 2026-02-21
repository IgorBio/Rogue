import random
import types


class DummyWeapon:
    def __init__(self, strength_bonus=0):
        self.strength_bonus = strength_bonus


class DummyStats:
    def __init__(self):
        self.attacks = []
        self.hits_taken = []

    def record_attack(self, hit, damage):
        self.attacks.append((hit, damage))

    def record_hit_taken(self, damage):
        self.hits_taken.append(damage)


def test_player_attack_hit_and_kill(monkeypatch):
    # deterministic randomness: always hit, no randomness in damage
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Zombie
    from domain.event_bus import EventBus
    from domain.events import AttackPerformedEvent

    # Set up event capture
    event_bus = EventBus()
    captured_events = []
    event_bus.subscribe(AttackPerformedEvent, lambda e: captured_events.append(e))

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)
    # Override the event bus in combat to use our test instance
    from domain import services
    original_event_bus = services.combat_system.event_bus
    services.combat_system.event_bus = event_bus

    try:
        player = Character(0, 0)
        player.strength = 1000

        enemy = Zombie(0, 1)
        enemy.health = 1

        result = combat.resolve_player_attack(player, enemy)

        assert result['hit'] is True
        assert result['killed'] is True
        assert 'treasure' in result and result['treasure'] is not None
        # Verify event was published instead of direct stats call
        assert len(captured_events) == 1
        assert captured_events[0].attacker_type == 'player'
        assert captured_events[0].hit is True
    finally:
        services.combat_system.event_bus = original_event_bus


def test_player_attack_miss(monkeypatch):
    # force miss by making random above max hit chance
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Zombie
    from domain.event_bus import EventBus
    from domain.events import AttackPerformedEvent

    # Set up event capture
    event_bus = EventBus()
    captured_events = []
    event_bus.subscribe(AttackPerformedEvent, lambda e: captured_events.append(e))

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)
    # Override the event bus in combat to use our test instance
    from domain import services
    original_event_bus = services.combat_system.event_bus
    services.combat_system.event_bus = event_bus

    try:
        player = Character(0, 0)
        player.strength = 5

        enemy = Zombie(0, 1)
        enemy.health = 10

        result = combat.resolve_player_attack(player, enemy)

        assert result['hit'] is False
        assert result['killed'] is False
        # Verify event was published instead of direct stats call
        assert len(captured_events) == 1
        assert captured_events[0].attacker_type == 'player'
        assert captured_events[0].hit is False
    finally:
        services.combat_system.event_bus = original_event_bus


def test_player_attack_hit_not_kill(monkeypatch):
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Zombie

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)

    player = Character(0, 0)
    player.strength = 5

    enemy = Zombie(0, 1)
    enemy.health = 100

    result = combat.resolve_player_attack(player, enemy)

    assert result['hit'] is True
    assert result['killed'] is False
    assert ('treasure' not in result) or (result['treasure'] is None)


def test_enemy_attack_records_hit(monkeypatch):
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Zombie
    from domain.event_bus import EventBus
    from domain.events import DamageTakenEvent

    # Set up event capture
    event_bus = EventBus()
    captured_events = []
    event_bus.subscribe(DamageTakenEvent, lambda e: captured_events.append(e))

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)
    # Override the event bus in combat to use our test instance
    from domain import services
    original_event_bus = services.combat_system.event_bus
    services.combat_system.event_bus = event_bus

    try:
        player = Character(0, 0)
        player.health = 100

        enemy = Zombie(0, 1)
        enemy.strength = 10

        result = combat.resolve_enemy_attack(enemy, player)

        assert result['hit'] is True
        # Verify DamageTakenEvent was published instead of direct stats call
        assert len(captured_events) == 1
        assert captured_events[0].damage > 0
        assert captured_events[0].enemy_type == 'zombie'
    finally:
        services.combat_system.event_bus = original_event_bus


def test_weapon_bonus_applied(monkeypatch):
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Zombie

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)

    player = Character(0, 0)
    player.strength = 5
    weapon = DummyWeapon(strength_bonus=3)

    enemy = Zombie(0, 1)
    enemy.health = 100

    result = combat.resolve_player_attack(player, enemy, attacker_weapon=weapon)

    assert result['hit'] is True
    # With uniform=1.0, damage should equal strength + weapon bonus
    assert result['damage'] >= (player.strength + weapon.strength_bonus)


def test_vampire_first_incoming_attack_always_misses(monkeypatch):
    # Even with guaranteed hit randomness, first hit against vampire must miss.
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Vampire

    combat = CombatSystem(statistics=DummyStats())
    player = Character(0, 0)
    player.strength = 50
    vampire = Vampire(0, 1)
    start_hp = vampire.health

    first = combat.resolve_player_attack(player, vampire)
    second = combat.resolve_player_attack(player, vampire)

    assert first['hit'] is False
    assert first['damage'] == 0
    assert vampire.first_attack_against is False
    assert second['hit'] is True
    assert vampire.health < start_hp


def test_vampire_first_miss_has_specific_message(monkeypatch):
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Vampire
    from domain.combat import get_combat_message

    combat = CombatSystem(statistics=DummyStats())
    player = Character(0, 0)
    vampire = Vampire(0, 1)

    result = combat.resolve_player_attack(player, vampire)
    message = get_combat_message(result)

    assert result['hit'] is False
    assert message == "Your first attack against a Vampire always misses!"
