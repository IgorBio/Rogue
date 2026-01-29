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

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)

    player = Character(0, 0)
    player.strength = 1000

    enemy = Zombie(0, 1)
    enemy.health = 1

    result = combat.resolve_player_attack(player, enemy)

    assert result['hit'] is True
    assert result['killed'] is True
    assert 'treasure' in result and result['treasure'] is not None
    assert stats.attacks[-1][0] is True


def test_player_attack_miss(monkeypatch):
    # force miss by making random above max hit chance
    monkeypatch.setattr(random, 'random', lambda: 0.99)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Zombie

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)

    player = Character(0, 0)
    player.strength = 5

    enemy = Zombie(0, 1)
    enemy.health = 10

    result = combat.resolve_player_attack(player, enemy)

    assert result['hit'] is False
    assert result['killed'] is False
    assert stats.attacks[-1][0] is False


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

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)

    player = Character(0, 0)
    player.health = 100

    enemy = Zombie(0, 1)
    enemy.strength = 10

    result = combat.resolve_enemy_attack(enemy, player)

    assert result['hit'] is True
    # stats.record_hit_taken should have been called with damage
    assert stats.hits_taken


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
