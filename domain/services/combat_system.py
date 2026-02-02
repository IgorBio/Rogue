"""CombatSystem service to encapsulate combat resolution and statistics.

This module wraps the procedural functions in `domain.combat` and
provides a single place to extend combat behaviour (logging, stats,
effects) without changing callers.

Statistics are now tracked via events published to the EventBus,
eliminating direct coupling between CombatSystem and Statistics.
"""
from typing import Optional, Any

from domain import combat as _combat
from domain.event_bus import event_bus
from domain.events import (
    AttackPerformedEvent,
    EnemyDefeatedEvent,
    DamageTakenEvent,
)


class CombatSystem:
    def __init__(self, statistics: Optional[object] = None):
        """
        Initialize CombatSystem.

        Args:
            statistics: Statistics tracker (optional, kept for compatibility)
        """
        self.statistics = statistics

    def resolve_player_attack(self, player, enemy, attacker_weapon=None):
        """Resolve an attack initiated by the player against an enemy.

        Returns a dict compatible with `domain.combat.resolve_attack`.
        Publishes AttackPerformedEvent for statistics tracking.
        """
        result = _combat.resolve_attack(player, enemy, attacker_weapon)

        # Publish attack event for statistics tracking
        try:
            event_bus.publish(AttackPerformedEvent(
                attacker_type='player',
                target_type='enemy',
                hit=result.get('hit', False),
                damage=result.get('damage', 0),
                killed=result.get('killed', False)
            ))
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
        Publishes DamageTakenEvent when player is hit.
        """
        result = _combat.resolve_attack(enemy, player, attacker_weapon)

        # Publish damage taken event for statistics tracking
        if result.get('hit', False):
            try:
                enemy_type = getattr(enemy, 'enemy_type', 'unknown')
                event_bus.publish(DamageTakenEvent(
                    damage=result.get('damage', 0),
                    enemy_type=str(enemy_type)
                ))
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
                # Publish enemy defeated event for statistics tracking
                try:
                    enemy_type = getattr(enemy, 'enemy_type', 'unknown')
                    enemy_level = getattr(enemy, 'level', 1)
                    position = getattr(enemy, 'position', (0, 0))
                    event_bus.publish(EnemyDefeatedEvent(
                        enemy_type=str(enemy_type),
                        enemy_level=enemy_level,
                        position=position if isinstance(position, tuple) else (0, 0)
                    ))
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

