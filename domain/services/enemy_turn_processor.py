"""
Enemy turn processing delegated from GameSession.

Encapsulates enemy-turn logic so it can be tested and refactored
independently from `GameSession`.
"""

from domain.logging_utils import log_exception
from domain.enemy_ai import (
    get_enemy_movement,
    get_special_attack_effects,
    handle_post_attack,
    should_enemy_attack,
)
from domain.combat import get_combat_message
from domain.entities.position import Position
from config.game_config import EnemyType


class EnemyTurnProcessor:
    def __init__(self, session):
        self.session = session

    def process_enemy_turns(self):
        session = self.session

        elixir_messages = session.character.update_elixirs()
        if elixir_messages:
            if session.message:
                session.message += " | " + " ".join(elixir_messages)
            else:
                session.message = " ".join(elixir_messages)

        combat_messages = []
        enemies = [e for e in session.level.get_all_enemies() if e.is_alive()]

        player_pos = (int(session.character.position[0]), int(session.character.position[1]))

        for enemy in enemies:
            enemy_pos = enemy.position
            # Use Position.manhattan_distance_to to avoid dependency on utils.pathfinding
            if isinstance(enemy_pos, tuple):
                enemy_pos_obj = Position(enemy_pos[0], enemy_pos[1])
            else:
                enemy_pos_obj = enemy_pos

            distance = enemy_pos_obj.manhattan_distance_to(player_pos)

            if distance == 1:
                if enemy.enemy_type == EnemyType.MIMIC and enemy.is_disguised:
                    continue

                if should_enemy_attack(enemy):
                    result = session.combat_system.resolve_enemy_attack(enemy, session.character)
                    special_effects = get_special_attack_effects(enemy, result)
                    combat_messages.append(get_combat_message(result))

                    if result.get('hit'):
                        # CombatSystem.resolve_enemy_attack already records hits via statistics

                        if special_effects['health_steal'] > 0:
                            session.character.max_health -= special_effects['health_steal']
                            if session.character.max_health < 1:
                                session.character.max_health = 1
                            if session.character.health > session.character.max_health:
                                session.character.health = session.character.max_health
                            combat_messages.append(f"Vampire stole {special_effects['health_steal']} max health!")

                        if special_effects['sleep']:
                            session.set_player_asleep()
                            combat_messages.append("Snake Mage puts you to sleep!")

                        if special_effects['counterattack']:
                            combat_messages.append("Ogre counterattacks!")

                    handle_post_attack(enemy, result)

                    if result.get('killed'):
                        session.set_game_over(f"Killed by {enemy.enemy_type}")
                        combat_messages.append("You have died!")
                        break
                else:
                    if enemy.enemy_type == EnemyType.OGRE:
                        enemy.is_resting = False
                        enemy.will_counterattack = True
            else:
                new_pos = get_enemy_movement(enemy, player_pos, session.level, enemies)
                if new_pos:
                    enemy.move_to(new_pos[0], new_pos[1])

        if combat_messages:
            if session.message:
                session.message += " | " + " ".join(combat_messages)
            else:
                session.message = " ".join(combat_messages)