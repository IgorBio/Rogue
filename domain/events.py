"""
Domain events for communication between layers.

This module defines events that are published by the domain layer
and consumed by other layers (presentation, infrastructure).
Events enable loose coupling between layers while maintaining
type safety through dataclasses.

Usage:
    from domain.events import LevelGeneratedEvent, CharacterMovedEvent
    from domain.event_bus import event_bus
    
    # Publish from domain
    event_bus.publish(LevelGeneratedEvent(level, (x, y)))
    
    # Subscribe in presentation
    event_bus.subscribe(LevelGeneratedEvent, on_level_generated)
"""

from dataclasses import dataclass
from typing import Tuple, Any, Optional


@dataclass(frozen=True)
class LevelGeneratedEvent:
    """
    Published when a new level is generated.
    
    Attributes:
        level: The newly generated Level instance
        character_position: Starting position (x, y) for the character
        level_number: The dungeon level number (1-21)
    """
    level: Any  # Level type
    character_position: Tuple[int, int]
    level_number: int


@dataclass(frozen=True)
class CharacterMovedEvent:
    """
    Published when the character moves to a new position.
    
    Attributes:
        from_position: Previous position (x, y)
        to_position: New position (x, y)
        is_transition: Whether this is a level transition (teleport)
        sync_camera: Whether presentation should sync camera to character
    """
    from_position: Tuple[int, int]
    to_position: Tuple[int, int]
    is_transition: bool = False
    sync_camera: bool = True


@dataclass(frozen=True)
class PlayerMovedEvent:
    """
    Alias for CharacterMovedEvent for statistics tracking.
    
    Attributes:
        from_pos: Previous position (x, y)
        to_pos: New position (x, y)
    """
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]


@dataclass(frozen=True)
class ItemCollectedEvent:
    """
    Published when the player collects an item.
    
    Attributes:
        item_type: Type of item ('food', 'weapon', 'elixir', 'scroll', 'treasure')
        item: The collected item instance
        position: Position where item was collected
    """
    item_type: str
    item: Any
    position: Tuple[int, int]


@dataclass(frozen=True)
class AttackPerformedEvent:
    """
    Published when an attack is performed (player or enemy).
    
    Attributes:
        attacker_type: 'player' or 'enemy'
        target_type: 'enemy' or 'player'
        hit: Whether the attack hit
        damage: Damage dealt (0 if missed)
        killed: Whether the target was killed
    """
    attacker_type: str
    target_type: str
    hit: bool
    damage: int
    killed: bool = False


@dataclass(frozen=True)
class GameStateChangedEvent:
    """
    Published when the game state changes.
    
    Attributes:
        old_state: Previous game state name
        new_state: New game state name
        reason: Optional reason for state change
    """
    old_state: str
    new_state: str
    reason: Optional[str] = None


@dataclass(frozen=True)
class EnemyDefeatedEvent:
    """
    Published when an enemy is defeated.
    
    Attributes:
        enemy_type: Type of defeated enemy
        enemy_level: Level of defeated enemy
        position: Position where enemy was defeated
    """
    enemy_type: str
    enemy_level: int
    position: Tuple[int, int]


@dataclass(frozen=True)
class FoodConsumedEvent:
    """
    Published when food is consumed.
    
    Attributes:
        health_restored: Amount of health restored
        food_item: The consumed food item
    """
    health_restored: int
    food_item: Any


@dataclass(frozen=True)
class ElixirUsedEvent:
    """
    Published when an elixir is used.
    
    Attributes:
        stat_boosted: Which stat was boosted ('strength' or 'dexterity')
        boost_amount: Amount of the boost
    """
    stat_boosted: str
    boost_amount: int


@dataclass(frozen=True)
class ScrollReadEvent:
    """
    Published when a scroll is read.
    
    Attributes:
        scroll_type: Type of scroll effect
        effect_description: Description of the effect
    """
    scroll_type: str
    effect_description: str


@dataclass(frozen=True)
class WeaponEquippedEvent:
    """
    Published when a weapon is equipped.
    
    Attributes:
        weapon_name: Name of the equipped weapon
        damage_bonus: Damage bonus from the weapon
    """
    weapon_name: str
    damage_bonus: int


@dataclass(frozen=True)
class DamageTakenEvent:
    """
    Published when the player takes damage from an enemy.
    
    Attributes:
        damage: Amount of damage taken
        enemy_type: Type of enemy that dealt the damage
    """
    damage: int
    enemy_type: str = 'unknown'


@dataclass(frozen=True)
class LevelReachedEvent:
    """
    Published when the player reaches a new dungeon level.
    
    Attributes:
        level_number: The dungeon level number reached
    """
    level_number: int


@dataclass(frozen=True)
class GameEndedEvent:
    """
    Published when the game ends (victory or defeat).
    
    Attributes:
        victory: Whether the player won
        final_health: Player's health at game end
        final_strength: Player's strength at game end
        final_dexterity: Player's dexterity at game end
        level_reached: Deepest level reached
    """
    victory: bool
    final_health: int
    final_strength: int
    final_dexterity: int
    level_reached: int
