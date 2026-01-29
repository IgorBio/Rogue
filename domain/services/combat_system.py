"""CombatSystem service to encapsulate combat resolution and statistics.

This module wraps the procedural functions in `domain.combat` and
provides a single place to extend combat behaviour (logging, stats,
effects) without changing callers.
"""
from typing import Optional
from data import statistics as _stats_module  # type: ignore

from domain import combat as _combat


class CombatSystem:
    def __init__(self, statistics: Optional[object] = None):
        self.statistics = statistics

    def resolve_player_attack(self, player, enemy, attacker_weapon=None):
        """Resolve an attack initiated by the player against an enemy.

        Returns a dict compatible with `domain.combat.resolve_attack`.
        """
        result = _combat.resolve_attack(player, enemy, attacker_weapon)

        # Record stats if available (attack count and damage)
        if self.statistics is not None:
            try:
                self.statistics.record_attack(result.get('hit', False), result.get('damage', 0))
            except Exception:
                pass

        # If enemy died, attach treasure value for convenience
        if result.get('killed', False):
            try:
                treasure = _combat.calculate_treasure_reward(enemy)
                result['treasure'] = treasure
            except Exception:
                result['treasure'] = None

        return result

    def resolve_enemy_attack(self, enemy, player, attacker_weapon=None):
        """Resolve an attack initiated by an enemy against the player.

        Returns a dict compatible with `domain.combat.resolve_attack`.
        """
        result = _combat.resolve_attack(enemy, player, attacker_weapon)

        # Record damage taken / hits if statistics present
        if self.statistics is not None:
            try:
                if result.get('hit', False):
                    self.statistics.record_hit_taken(result.get('damage', 0))
            except Exception:
                pass

        return result

