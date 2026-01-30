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

    def process_player_attack(self, session, enemy):
        """High-level handling of a player attack against an enemy.

        This wraps resolve_player_attack and applies session-side effects:
        - record stats
        - handle enemy death (treasure, remove enemy, move player)
        - update camera/fog
        - pickup any item on death tile
        - set session.message to a composed combat message

        Returns True if attack was processed (player attempted attack),
        otherwise False.
        """
        messages = []

        result = self.resolve_player_attack(session.character, enemy, session.character.current_weapon)

        # Compose messages using combat helper if available
        try:
            from domain.combat import get_combat_message

            messages.append(get_combat_message(result))
        except Exception:
            messages.append('You attack.')

        if result.get('killed'):
            treasure = result.get('treasure')
            if treasure:
                try:
                    session.character.backpack.treasure_value += treasure
                except Exception:
                    pass
                try:
                    if self.statistics is not None:
                        self.statistics.record_enemy_defeated(treasure)
                except Exception:
                    pass

            # Remove enemy from its room
            enemy_room = None
            for room in session.level.rooms:
                if enemy in room.enemies:
                    enemy_room = room
                    break

            if enemy_room:
                try:
                    enemy_room.remove_enemy(enemy)
                except Exception:
                    pass

            # Move player onto enemy tile
            try:
                session.character.move_to(enemy.position[0], enemy.position[1])
            except Exception:
                pass

            # Sync camera in 3D mode
            if session.is_3d_mode():
                try:
                    session.camera.x = enemy.position[0]
                    session.camera.y = enemy.position[1]
                except Exception:
                    pass

            if session.should_use_fog_of_war():
                try:
                    session.fog_of_war.update_visibility(session.character.position)
                except Exception:
                    pass

            # Pickup item if present
            try:
                item = session._get_item_at(enemy.position[0], enemy.position[1])
                if item:
                    pickup_message = session._pickup_item(item)
                    if pickup_message:
                        messages.append(pickup_message)
            except Exception:
                pass

        session.message = " ".join(messages)
        return True

    def finalize_attack_result(self, session, result):
        """Apply session-level effects for an attack result coming from
        external callers (e.g. 3D camera controller).

        This centralizes stat recording and end-of-attack flow so callers
        (GameSession) remain thin.
        """
        if not result:
            return

        # Record attack stats if available
        if self.statistics is not None:
            try:
                self.statistics.record_attack(result.get('hit', False), result.get('damage', 0))
            except Exception:
                pass

        # Record enemy defeated / treasure
        if result.get('killed') and result.get('treasure'):
            try:
                if self.statistics is not None:
                    self.statistics.record_enemy_defeated(result.get('treasure'))
            except Exception:
                pass

        # Allow session to progress enemy turns if still running
        try:
            if not session.state_machine.is_terminal():
                session._process_enemy_turns()
        except Exception:
            pass


