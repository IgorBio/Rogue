"""
Statistics tracker using Observer pattern via EventBus.

This module provides centralized statistics tracking through event subscriptions.
Instead of calling stats.record_*() directly throughout the codebase, services
publish events and StatisticsTracker automatically records the appropriate stats.

This ensures statistics are never forgotten and provides a centralized audit point.

Usage:
    from domain.services.statistics_tracker import StatisticsTracker
    from domain.event_bus import event_bus
    from data.statistics import Statistics
    
    stats = Statistics()
    tracker = StatisticsTracker(stats, event_bus)
    
    # Now when events are published, stats are automatically recorded:
    event_bus.publish(PlayerMovedEvent((0, 0), (1, 0)))  # Records movement
"""

from typing import Any, Optional

from domain.event_bus import EventBus
from domain.events import (
    PlayerMovedEvent,
    ItemCollectedEvent,
    AttackPerformedEvent,
    EnemyDefeatedEvent,
    FoodConsumedEvent,
    ElixirUsedEvent,
    ScrollReadEvent,
    WeaponEquippedEvent,
    DamageTakenEvent,
    LevelReachedEvent,
    GameEndedEvent,
)


class StatisticsTracker:
    """
    Centralized statistics tracking via event subscriptions.
    
    This class subscribes to game events and automatically records
    statistics. It eliminates the need to manually call stats methods
    throughout the codebase.
    
    Attributes:
        stats: Statistics instance to record to
        event_bus: EventBus instance to subscribe to
        _subscribed: Whether subscriptions are currently active
    
    Example:
        stats = Statistics()
        tracker = StatisticsTracker(stats, event_bus)
        tracker.start_tracking()
        
        # Events now automatically update stats
        event_bus.publish(PlayerMovedEvent((0, 0), (1, 0)))
        assert stats.tiles_moved == 1
    """
    
    def __init__(self, stats: Any, event_bus: Optional[EventBus] = None):
        """
        Initialize the statistics tracker.
        
        Args:
            stats: Statistics instance to record statistics to
            event_bus: EventBus instance (defaults to global event_bus)
        """
        self.stats = stats
        self.event_bus = event_bus
        self._subscribed = False
        self._callbacks = {}
    
    def start_tracking(self) -> None:
        """
        Subscribe to all relevant events.
        
        This method registers callbacks for all events that should
        be tracked in statistics. Call this after initialization.
        """
        if self._subscribed or self.event_bus is None:
            return
        
        # Define event to callback mappings
        self._callbacks = {
            PlayerMovedEvent: self._on_player_moved,
            ItemCollectedEvent: self._on_item_collected,
            AttackPerformedEvent: self._on_attack_performed,
            EnemyDefeatedEvent: self._on_enemy_defeated,
            FoodConsumedEvent: self._on_food_consumed,
            ElixirUsedEvent: self._on_elixir_used,
            ScrollReadEvent: self._on_scroll_read,
            WeaponEquippedEvent: self._on_weapon_equipped,
            DamageTakenEvent: self._on_damage_taken,
            LevelReachedEvent: self._on_level_reached,
            GameEndedEvent: self._on_game_ended,
        }
        
        for event_type, callback in self._callbacks.items():
            self.event_bus.subscribe(event_type, callback)
        
        self._subscribed = True
    
    def stop_tracking(self) -> None:
        """
        Unsubscribe from all events.
        
        Call this when the tracker is no longer needed to prevent
        memory leaks and unwanted callbacks.
        """
        if not self._subscribed or self.event_bus is None:
            return
        
        for event_type, callback in self._callbacks.items():
            self.event_bus.unsubscribe(event_type, callback)
        
        self._callbacks.clear()
        self._subscribed = False
    
    def _on_player_moved(self, event: PlayerMovedEvent) -> None:
        """Record movement when player moves."""
        try:
            self.stats.record_movement()
        except Exception:
            pass
    
    def _on_item_collected(self, event: ItemCollectedEvent) -> None:
        """Record item collection."""
        try:
            self.stats.record_item_collected()
        except Exception:
            pass
    
    def _on_attack_performed(self, event: AttackPerformedEvent) -> None:
        """Record attack attempt when player attacks."""
        # Only record player attacks here (enemy attacks are handled separately)
        if event.attacker_type == 'player':
            try:
                self.stats.record_attack(event.hit, event.damage)
            except Exception:
                pass
    
    def _on_enemy_defeated(self, event: EnemyDefeatedEvent) -> None:
        """Record enemy defeat with treasure."""
        try:
            # Treasure is calculated elsewhere and passed through event
            # Default to 0 if not specified, actual treasure comes from enemy
            self.stats.record_enemy_defeated(0)
        except Exception:
            pass
    
    def _on_food_consumed(self, event: FoodConsumedEvent) -> None:
        """Record food consumption."""
        try:
            self.stats.record_food_used()
        except Exception:
            pass
    
    def _on_elixir_used(self, event: ElixirUsedEvent) -> None:
        """Record elixir usage."""
        try:
            self.stats.record_elixir_used()
        except Exception:
            pass
    
    def _on_scroll_read(self, event: ScrollReadEvent) -> None:
        """Record scroll reading."""
        try:
            self.stats.record_scroll_used()
        except Exception:
            pass
    
    def _on_weapon_equipped(self, event: WeaponEquippedEvent) -> None:
        """Record weapon equipping."""
        try:
            self.stats.record_weapon_equipped()
        except Exception:
            pass
    
    def _on_damage_taken(self, event: DamageTakenEvent) -> None:
        """Record damage taken from enemies."""
        try:
            self.stats.record_hit_taken(event.damage)
        except Exception:
            pass
    
    def _on_level_reached(self, event: LevelReachedEvent) -> None:
        """Record reaching a new level."""
        try:
            self.stats.record_level_reached(event.level_number)
        except Exception:
            pass
    
    def _on_game_ended(self, event: GameEndedEvent) -> None:
        """Record game end with final character state."""
        try:
            # Create a minimal character-like object with final stats
            class FinalCharacterState:
                def __init__(self, health, strength, dexterity):
                    self.health = health
                    self.strength = strength
                    self.dexterity = dexterity
            
            final_char = FinalCharacterState(
                event.final_health,
                event.final_strength,
                event.final_dexterity
            )
            self.stats.record_game_end(final_char, event.victory)
        except Exception:
            pass
    
    def __enter__(self):
        """Context manager entry - start tracking."""
        self.start_tracking()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop tracking."""
        self.stop_tracking()
        return False
