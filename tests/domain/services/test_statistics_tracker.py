"""
Tests for StatisticsTracker event-based statistics tracking.

This module tests that StatisticsTracker correctly subscribes to events
and records statistics via the Statistics class.
"""
import pytest
from unittest.mock import MagicMock

from domain.services.statistics_tracker import StatisticsTracker
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


class MockStatistics:
    """Mock Statistics class for testing."""
    
    def __init__(self):
        self.tiles_moved = 0
        self.items_collected = 0
        self.attacks_made = 0
        self.damage_dealt = 0
        self.enemies_defeated = 0
        self.treasure_collected = 0
        self.food_consumed = 0
        self.elixirs_used = 0
        self.scrolls_read = 0
        self.weapons_equipped = 0
        self.hits_taken = 0
        self.damage_received = 0
        self.level_reached = 1
        self.victory = False
        self.deaths = 0
        self.final_health = 0
        self.final_strength = 0
        self.final_dexterity = 0
    
    def record_movement(self):
        self.tiles_moved += 1
    
    def record_item_collected(self):
        self.items_collected += 1
    
    def record_attack(self, hit, damage):
        self.attacks_made += 1
        if hit:
            self.damage_dealt += damage
    
    def record_enemy_defeated(self, treasure_reward):
        self.enemies_defeated += 1
        self.treasure_collected += treasure_reward
    
    def record_food_used(self):
        self.food_consumed += 1
    
    def record_elixir_used(self):
        self.elixirs_used += 1
    
    def record_scroll_used(self):
        self.scrolls_read += 1
    
    def record_weapon_equipped(self):
        self.weapons_equipped += 1
    
    def record_hit_taken(self, damage):
        self.hits_taken += 1
        self.damage_received += damage
    
    def record_level_reached(self, level):
        self.level_reached = max(self.level_reached, level)
    
    def record_game_end(self, character, victory=False):
        self.victory = victory
        self.final_health = character.health
        self.final_strength = character.strength
        self.final_dexterity = character.dexterity
        if not victory:
            self.deaths = 1


class MockCharacter:
    """Mock Character for testing game end."""
    def __init__(self):
        self.health = 50
        self.strength = 10
        self.dexterity = 8


@pytest.fixture
def event_bus():
    """Provide a fresh EventBus for each test."""
    return EventBus()


@pytest.fixture
def stats():
    """Provide a MockStatistics instance for each test."""
    return MockStatistics()


@pytest.fixture
def tracker(stats, event_bus):
    """Provide a configured StatisticsTracker for each test."""
    tracker = StatisticsTracker(stats, event_bus)
    tracker.start_tracking()
    yield tracker
    tracker.stop_tracking()


class TestStatisticsTracker:
    """Test suite for StatisticsTracker."""
    
    def test_initialization(self, stats, event_bus):
        """Test that tracker initializes correctly."""
        tracker = StatisticsTracker(stats, event_bus)
        assert tracker.stats == stats
        assert tracker.event_bus == event_bus
        assert not tracker._subscribed
        
        tracker.start_tracking()
        assert tracker._subscribed
        
        tracker.stop_tracking()
        assert not tracker._subscribed
    
    def test_player_movement_tracked(self, tracker, stats, event_bus):
        """Test that PlayerMovedEvent records movement."""
        assert stats.tiles_moved == 0
        
        event_bus.publish(PlayerMovedEvent(from_pos=(0, 0), to_pos=(1, 0)))
        
        assert stats.tiles_moved == 1
    
    def test_multiple_movements_tracked(self, tracker, stats, event_bus):
        """Test that multiple movements are all recorded."""
        for i in range(5):
            event_bus.publish(PlayerMovedEvent(from_pos=(i, 0), to_pos=(i+1, 0)))
        
        assert stats.tiles_moved == 5
    
    def test_item_collected_tracked(self, tracker, stats, event_bus):
        """Test that ItemCollectedEvent records item collection."""
        assert stats.items_collected == 0
        
        event_bus.publish(ItemCollectedEvent(
            item_type='weapon',
            item=None,
            position=(1, 1)
        ))
        
        assert stats.items_collected == 1
    
    def test_attack_performed_player_hit(self, tracker, stats, event_bus):
        """Test that player attack hit is recorded."""
        assert stats.attacks_made == 0
        assert stats.damage_dealt == 0
        
        event_bus.publish(AttackPerformedEvent(
            attacker_type='player',
            target_type='enemy',
            hit=True,
            damage=15,
            killed=False
        ))
        
        assert stats.attacks_made == 1
        assert stats.damage_dealt == 15
    
    def test_attack_performed_player_miss(self, tracker, stats, event_bus):
        """Test that player attack miss is recorded without damage."""
        event_bus.publish(AttackPerformedEvent(
            attacker_type='player',
            target_type='enemy',
            hit=False,
            damage=0,
            killed=False
        ))
        
        assert stats.attacks_made == 1
        assert stats.damage_dealt == 0
    
    def test_attack_performed_enemy_not_recorded(self, tracker, stats, event_bus):
        """Test that enemy attacks are not recorded as player attacks."""
        event_bus.publish(AttackPerformedEvent(
            attacker_type='enemy',
            target_type='player',
            hit=True,
            damage=10,
            killed=False
        ))
        
        # Player attack stats should not change
        assert stats.attacks_made == 0
        assert stats.damage_dealt == 0
    
    def test_enemy_defeated_tracked(self, tracker, stats, event_bus):
        """Test that EnemyDefeatedEvent records enemy defeat."""
        assert stats.enemies_defeated == 0
        
        event_bus.publish(EnemyDefeatedEvent(
            enemy_type='goblin',
            enemy_level=1,
            position=(2, 3)
        ))
        
        assert stats.enemies_defeated == 1
    
    def test_food_consumed_tracked(self, tracker, stats, event_bus):
        """Test that FoodConsumedEvent records food usage."""
        assert stats.food_consumed == 0
        
        event_bus.publish(FoodConsumedEvent(
            health_restored=20,
            food_item=None
        ))
        
        assert stats.food_consumed == 1
    
    def test_elixir_used_tracked(self, tracker, stats, event_bus):
        """Test that ElixirUsedEvent records elixir usage."""
        assert stats.elixirs_used == 0
        
        event_bus.publish(ElixirUsedEvent(
            stat_boosted='strength',
            boost_amount=2
        ))
        
        assert stats.elixirs_used == 1
    
    def test_scroll_read_tracked(self, tracker, stats, event_bus):
        """Test that ScrollReadEvent records scroll usage."""
        assert stats.scrolls_read == 0
        
        event_bus.publish(ScrollReadEvent(
            scroll_type='teleport',
            effect_description='Teleports player'
        ))
        
        assert stats.scrolls_read == 1
    
    def test_weapon_equipped_tracked(self, tracker, stats, event_bus):
        """Test that WeaponEquippedEvent records weapon equipping."""
        assert stats.weapons_equipped == 0
        
        event_bus.publish(WeaponEquippedEvent(
            weapon_name='Sword',
            damage_bonus=5
        ))
        
        assert stats.weapons_equipped == 1
    
    def test_damage_taken_tracked(self, tracker, stats, event_bus):
        """Test that DamageTakenEvent records damage taken."""
        assert stats.hits_taken == 0
        assert stats.damage_received == 0
        
        event_bus.publish(DamageTakenEvent(
            damage=12,
            enemy_type='orc'
        ))
        
        assert stats.hits_taken == 1
        assert stats.damage_received == 12
    
    def test_level_reached_tracked(self, tracker, stats, event_bus):
        """Test that LevelReachedEvent records level progression."""
        assert stats.level_reached == 1
        
        event_bus.publish(LevelReachedEvent(level_number=5))
        
        assert stats.level_reached == 5
    
    def test_level_reached_does_not_decrease(self, tracker, stats, event_bus):
        """Test that level reached only increases."""
        event_bus.publish(LevelReachedEvent(level_number=10))
        event_bus.publish(LevelReachedEvent(level_number=5))
        
        assert stats.level_reached == 10
    
    def test_game_ended_victory_tracked(self, tracker, stats, event_bus):
        """Test that GameEndedEvent with victory records correctly."""
        event_bus.publish(GameEndedEvent(
            victory=True,
            final_health=80,
            final_strength=15,
            final_dexterity=12,
            level_reached=21
        ))
        
        assert stats.victory is True
        assert stats.deaths == 0
        assert stats.final_health == 80
        assert stats.final_strength == 15
        assert stats.final_dexterity == 12
    
    def test_game_ended_defeat_tracked(self, tracker, stats, event_bus):
        """Test that GameEndedEvent with defeat records correctly."""
        event_bus.publish(GameEndedEvent(
            victory=False,
            final_health=0,
            final_strength=10,
            final_dexterity=8,
            level_reached=5
        ))
        
        assert stats.victory is False
        assert stats.deaths == 1
        assert stats.final_health == 0
        assert stats.final_strength == 10
        assert stats.final_dexterity == 8
    
    def test_stop_tracking_unsubscribes(self, tracker, stats, event_bus):
        """Test that stop_tracking removes event subscriptions."""
        tracker.stop_tracking()
        
        # Publish events after stopping
        event_bus.publish(PlayerMovedEvent(from_pos=(0, 0), to_pos=(1, 0)))
        event_bus.publish(ItemCollectedEvent(item_type='food', item=None, position=(1, 1)))
        
        # Stats should not have changed
        assert stats.tiles_moved == 0
        assert stats.items_collected == 0
    
    def test_context_manager(self, stats, event_bus):
        """Test that tracker works as a context manager."""
        with StatisticsTracker(stats, event_bus) as tracker:
            event_bus.publish(PlayerMovedEvent(from_pos=(0, 0), to_pos=(1, 0)))
            assert stats.tiles_moved == 1
        
        # After exiting context, events should not be tracked
        event_bus.publish(PlayerMovedEvent(from_pos=(1, 0), to_pos=(2, 0)))
        assert stats.tiles_moved == 1  # Still 1, not 2
    
    def test_exception_in_callback_does_not_break(self, tracker, stats, event_bus):
        """Test that exceptions in stats methods don't break event handling."""
        # Make a stats method that raises an exception
        stats.record_movement = MagicMock(side_effect=Exception("Test error"))
        
        # Should not raise
        event_bus.publish(PlayerMovedEvent(from_pos=(0, 0), to_pos=(1, 0)))
    
    def test_no_event_bus_does_not_crash(self, stats):
        """Test that tracker handles missing event bus gracefully."""
        tracker = StatisticsTracker(stats, None)
        tracker.start_tracking()  # Should not crash
        tracker.stop_tracking()  # Should not crash
