"""
Advanced AI behaviors for different enemy types.

This module implements unique movement patterns and special abilities
for each enemy type, providing varied and challenging gameplay.
"""
import random
from typing import TYPE_CHECKING, Tuple, Optional, List, Dict, Any

from config.game_config import EnemyType
from utils.pathfinding import (
    get_distance,
    get_next_step,
    get_random_adjacent_walkable
)

if TYPE_CHECKING:
    from domain.entities.enemy import Enemy
    from domain.entities.level import Level
    from domain.entities.room import Room


# AI behavior constants
GHOST_TELEPORT_COOLDOWN_MIN: int = 3
GHOST_TELEPORT_COOLDOWN_MAX: int = 5
GHOST_INVISIBILITY_COOLDOWN_MIN: int = 4
GHOST_INVISIBILITY_COOLDOWN_MAX: int = 7

SNAKE_MAGE_DIRECTION_COOLDOWN_MIN: int = 3
SNAKE_MAGE_DIRECTION_COOLDOWN_MAX: int = 6
SNAKE_MAGE_SLEEP_CHANCE: float = 0.3

VAMPIRE_HEALTH_STEAL_MIN: int = 2
VAMPIRE_HEALTH_STEAL_MAX: int = 5


def get_enemy_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy']
) -> Optional[Tuple[int, int]]:
    """
    Get the next move for an enemy based on its type and AI.
    
    Each enemy type has unique movement behavior and special abilities.
    
    Args:
        enemy: Enemy instance
        player_pos: (x, y) player position
        level: Level object for pathfinding
        all_enemies: All enemies for collision avoidance
    
    Returns:
        (x, y) for new position, or None if no move
    """
    if enemy.enemy_type == EnemyType.MIMIC:
        return _mimic_movement(enemy, player_pos, level, all_enemies, 0)
    
    distance = get_distance(enemy.position, player_pos)
    
    if distance <= enemy.hostility:
        enemy.is_chasing = True
    
    movement_handlers = {
        EnemyType.ZOMBIE: _zombie_movement,
        EnemyType.VAMPIRE: _vampire_movement,
        EnemyType.GHOST: _ghost_movement,
        EnemyType.OGRE: _ogre_movement,
        EnemyType.SNAKE_MAGE: _snake_mage_movement,
    }
    
    handler = movement_handlers.get(enemy.enemy_type, _default_movement)
    return handler(enemy, player_pos, level, all_enemies, distance)


def _mimic_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy'],
    distance: int
) -> Optional[Tuple[int, int]]:
    """
    Mimic: Stays stationary while disguised.
    Once revealed, behaves like a standard enemy.
    """
    if hasattr(enemy, 'is_disguised') and enemy.is_disguised:
        return None
    
    if enemy.is_chasing and distance > 1:
        next_pos = get_next_step(enemy.position, player_pos, level)
        if next_pos and not _is_position_blocked(next_pos, all_enemies, enemy, player_pos):
            return next_pos
    
    return None


def _zombie_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy'],
    distance: int
) -> Optional[Tuple[int, int]]:
    """
    Zombie: Standard chasing behavior.
    Low dexterity, medium strength, high health.
    """
    if enemy.is_chasing and distance > 1:
        next_pos = get_next_step(enemy.position, player_pos, level)
        if next_pos and not _is_position_blocked(next_pos, all_enemies, enemy, player_pos):
            return next_pos
    
    if not enemy.is_chasing:
        new_pos = get_random_adjacent_walkable(enemy.position, level)
        if new_pos and not _is_position_blocked(new_pos, all_enemies, enemy, player_pos):
            return new_pos
    
    return None


def _vampire_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy'],
    distance: int
) -> Optional[Tuple[int, int]]:
    """
    Vampire: Standard chasing with special combat mechanics.
    High dexterity, steals max health on hit.
    First attack against vampire always misses.
    """
    if enemy.is_chasing and distance > 1:
        next_pos = get_next_step(enemy.position, player_pos, level)
        if next_pos and not _is_position_blocked(next_pos, all_enemies, enemy, player_pos):
            return next_pos
    
    if not enemy.is_chasing:
        new_pos = get_random_adjacent_walkable(enemy.position, level)
        if new_pos and not _is_position_blocked(new_pos, all_enemies, enemy, player_pos):
            return new_pos
    
    return None


def _ghost_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy'],
    distance: int
) -> Optional[Tuple[int, int]]:
    """
    Ghost: Teleports within room and can become invisible.
    High dexterity, low strength, low health.
    """
    if not hasattr(enemy, 'invisibility_cooldown'):
        enemy.invisibility_cooldown = 0
    
    if not hasattr(enemy, 'teleport_cooldown'):
        enemy.teleport_cooldown = 0
    
    if enemy.teleport_cooldown <= 0:
        room = _get_enemy_room(enemy, level)
        if room:
            new_pos = room.get_random_floor_position()
            if new_pos != player_pos:
                enemy.teleport_cooldown = random.randint(
                    GHOST_TELEPORT_COOLDOWN_MIN,
                    GHOST_TELEPORT_COOLDOWN_MAX
                )
                return new_pos
    
    enemy.teleport_cooldown -= 1
    
    if enemy.invisibility_cooldown <= 0:
        enemy.is_invisible = not getattr(enemy, 'is_invisible', False)
        enemy.invisibility_cooldown = random.randint(
            GHOST_INVISIBILITY_COOLDOWN_MIN,
            GHOST_INVISIBILITY_COOLDOWN_MAX
        )
    
    enemy.invisibility_cooldown -= 1
    
    if distance == 1:
        enemy.is_invisible = False
    
    if enemy.is_chasing and distance > 1:
        next_pos = get_next_step(enemy.position, player_pos, level)
        if next_pos and not _is_position_blocked(next_pos, all_enemies, enemy, player_pos):
            return next_pos
    
    return None


def _ogre_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy'],
    distance: int
) -> Optional[Tuple[int, int]]:
    """
    Ogre: Moves TWO tiles per turn. Rests after attacking.
    Very high strength, low dexterity.
    Guaranteed counterattack after resting.
    """
    if not hasattr(enemy, 'is_resting'):
        enemy.is_resting = False
    
    if not hasattr(enemy, 'will_counterattack'):
        enemy.will_counterattack = False
    
    if enemy.is_resting:
        enemy.is_resting = False
        enemy.will_counterattack = True
        return None
    
    if enemy.is_chasing and distance > 1:
        next_pos = get_next_step(enemy.position, player_pos, level)
        if next_pos and not _is_position_blocked(next_pos, all_enemies, enemy, player_pos):
            first_distance = abs(next_pos[0] - player_pos[0]) + abs(next_pos[1] - player_pos[1])
            if first_distance == 1:
                return next_pos
            
            second_pos = get_next_step(next_pos, player_pos, level)
            if second_pos and not _is_position_blocked(second_pos, all_enemies, enemy, player_pos):
                return second_pos
            else:
                return next_pos
    
    if not enemy.is_chasing:
        new_pos = get_random_adjacent_walkable(enemy.position, level)
        if new_pos and not _is_position_blocked(new_pos, all_enemies, enemy, player_pos):
            second_pos = get_random_adjacent_walkable(new_pos, level)
            if second_pos and not _is_position_blocked(second_pos, all_enemies, enemy, player_pos):
                return second_pos
            return new_pos
    
    return None


def _snake_mage_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy'],
    distance: int
) -> Optional[Tuple[int, int]]:
    """
    Snake Mage: Moves diagonally and switches direction.
    Very high dexterity. Can put player to sleep.
    """
    if not hasattr(enemy, 'diagonal_direction'):
        enemy.diagonal_direction = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    if not hasattr(enemy, 'direction_cooldown'):
        enemy.direction_cooldown = random.randint(
            SNAKE_MAGE_DIRECTION_COOLDOWN_MIN,
            SNAKE_MAGE_DIRECTION_COOLDOWN_MAX
        )
    
    enemy.direction_cooldown -= 1
    if enemy.direction_cooldown <= 0:
        enemy.diagonal_direction = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        enemy.direction_cooldown = random.randint(
            SNAKE_MAGE_DIRECTION_COOLDOWN_MIN,
            SNAKE_MAGE_DIRECTION_COOLDOWN_MAX
        )
    
    if enemy.is_chasing and distance > 1:
        dx = 1 if player_pos[0] > enemy.position[0] else -1
        dy = 1 if player_pos[1] > enemy.position[1] else -1
        
        diagonal_pos = (enemy.position[0] + dx, enemy.position[1] + dy)
        
        if level.is_walkable(diagonal_pos[0], diagonal_pos[1]):
            if not _is_position_blocked(diagonal_pos, all_enemies, enemy, player_pos):
                return diagonal_pos
        
        alt_pos = (
            enemy.position[0] + enemy.diagonal_direction[0],
            enemy.position[1] + enemy.diagonal_direction[1]
        )
        
        if level.is_walkable(alt_pos[0], alt_pos[1]):
            if not _is_position_blocked(alt_pos, all_enemies, enemy, player_pos):
                return alt_pos
    
    if not enemy.is_chasing:
        new_pos = (
            enemy.position[0] + enemy.diagonal_direction[0],
            enemy.position[1] + enemy.diagonal_direction[1]
        )
        
        if level.is_walkable(new_pos[0], new_pos[1]):
            if not _is_position_blocked(new_pos, all_enemies, enemy, player_pos):
                return new_pos
    
    return None


def _default_movement(
    enemy: 'Enemy',
    player_pos: Tuple[int, int],
    level: 'Level',
    all_enemies: List['Enemy'],
    distance: int
) -> Optional[Tuple[int, int]]:
    """Default movement behavior (fallback)."""
    
    if enemy.is_chasing and distance > 1:
        next_pos = get_next_step(enemy.position, player_pos, level)
        if next_pos and not _is_position_blocked(next_pos, all_enemies, enemy, player_pos):
            return next_pos
    
    if not enemy.is_chasing:
        new_pos = get_random_adjacent_walkable(enemy.position, level)
        if new_pos and not _is_position_blocked(new_pos, all_enemies, enemy, player_pos):
            return new_pos
    
    return None


def _is_position_blocked(
    pos: Tuple[int, int],
    all_enemies: List['Enemy'],
    current_enemy: 'Enemy',
    player_pos: Tuple[int, int]
) -> bool:
    """Check if position is blocked by another enemy or player."""
    if pos == player_pos:
        return False
    
    for enemy in all_enemies:
        if enemy != current_enemy and enemy.is_alive() and enemy.position == pos:
            return True
    
    return False


def _get_enemy_room(enemy: 'Enemy', level: 'Level') -> Optional['Room']:
    """Get the room that contains the enemy."""
    for room in level.rooms:
        if enemy in room.enemies:
            return room
    return None


def should_enemy_attack(enemy: 'Enemy') -> bool:
    """
    Check if enemy should attack this turn.
    
    Some enemies have special attack patterns.
    
    Args:
        enemy: Enemy instance
    
    Returns:
        True if enemy should attack
    """
    if enemy.enemy_type == EnemyType.OGRE:
        return not getattr(enemy, 'is_resting', False)
    
    return True


def get_special_attack_effects(enemy: 'Enemy', combat_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply special effects from enemy attacks.
    
    Args:
        enemy: Enemy that attacked
        combat_result: Result from resolve_attack
    
    Returns:
        Special effects containing:
            - health_steal (int): For vampire
            - sleep (bool): For snake mage
            - counterattack (bool): For ogre
    """
    effects: Dict[str, Any] = {
        'health_steal': 0,
        'sleep': False,
        'counterattack': False
    }
    
    if not combat_result.get('hit', False):
        return effects
    
    if enemy.enemy_type == EnemyType.VAMPIRE:
        effects['health_steal'] = random.randint(
            VAMPIRE_HEALTH_STEAL_MIN,
            VAMPIRE_HEALTH_STEAL_MAX
        )
    
    if enemy.enemy_type == EnemyType.SNAKE_MAGE:
        if random.random() < SNAKE_MAGE_SLEEP_CHANCE:
            effects['sleep'] = True
    
    if enemy.enemy_type == EnemyType.OGRE:
        if getattr(enemy, 'will_counterattack', False):
            effects['counterattack'] = True
            enemy.will_counterattack = False
    
    return effects


def handle_post_attack(enemy: 'Enemy', combat_result: Dict[str, Any]) -> None:
    """
    Handle post-attack state changes for enemies.
    
    Args:
        enemy: Enemy that attacked
        combat_result: Result from resolve_attack
    """
    if enemy.enemy_type == EnemyType.OGRE:
        if combat_result.get('hit', False):
            enemy.is_resting = True
