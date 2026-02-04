"""
Domain layer for the roguelike game.

This package contains all core game logic and business rules.

The domain layer includes:
- Game entities (character, enemies, items, levels)
- Combat mechanics and damage calculation
- Enemy AI behaviors
- Level generation and procedural content
- Fog of war and visibility systems
- Key-door puzzle system
- Dynamic difficulty adjustment
"""

# Import key modules for convenient access
from domain.combat import (
    calculate_hit_chance,
    calculate_damage,
    resolve_attack,
    calculate_treasure_reward,
    get_combat_message
)

from domain.fog_of_war import FogOfWar

from domain.enemy_ai import (
    get_enemy_movement,
    should_enemy_attack,
    get_special_attack_effects,
    handle_post_attack
)

__all__ = [
    'calculate_hit_chance',
    'calculate_damage',
    'resolve_attack',
    'calculate_treasure_reward',
    'get_combat_message',
    'FogOfWar',
    'get_enemy_movement',
    'should_enemy_attack',
    'get_special_attack_effects',
    'handle_post_attack',
]