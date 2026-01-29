import random


def test_resolve_player_attack_kills_enemy(monkeypatch):
    """CombatSystem should resolve player attacks and attach treasure when enemy dies."""
    # Patch randomness to be deterministic
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'uniform', lambda a, b: 1.0)

    from domain.services.combat_system import CombatSystem
    from domain.entities.character import Character
    from domain.entities.enemy import Zombie

    # Minimal stats object with recording methods used by CombatSystem
    class DummyStats:
        def record_attack(self, hit, damage):
            self.last = (hit, damage)

    stats = DummyStats()
    combat = CombatSystem(statistics=stats)

    player = Character(0, 0)
    # Make player overwhelmingly strong so attack will kill when hit
    player.strength = 999

    enemy = Zombie(0, 1)
    enemy.health = 1

    result = combat.resolve_player_attack(player, enemy)

    assert isinstance(result, dict)
    assert 'hit' in result and 'damage' in result and 'killed' in result
    assert result['hit'] is True
    assert result['killed'] is True
    assert 'treasure' in result
