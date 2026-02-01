"""
Tests for the event bus system.
"""

import pytest
from domain.event_bus import EventBus, event_bus, reset_event_bus
from domain.events import (
    LevelGeneratedEvent,
    CharacterMovedEvent,
    ItemCollectedEvent,
    AttackPerformedEvent,
)


class TestEventBusBasic:
    """Test basic EventBus functionality."""
    
    def test_subscribe_and_publish(self):
        """Test subscribing and publishing events."""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(LevelGeneratedEvent, handler)
        event = LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1)
        bus.publish(event)
        
        assert len(received) == 1
        assert received[0] == event
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers for same event type."""
        bus = EventBus()
        received1 = []
        received2 = []
        
        def handler1(event):
            received1.append(event)
        
        def handler2(event):
            received2.append(event)
        
        bus.subscribe(LevelGeneratedEvent, handler1)
        bus.subscribe(LevelGeneratedEvent, handler2)
        
        event = LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1)
        bus.publish(event)
        
        assert len(received1) == 1
        assert len(received2) == 1
    
    def test_different_event_types(self):
        """Test that events are only sent to their type's subscribers."""
        bus = EventBus()
        level_events = []
        move_events = []
        
        def level_handler(event):
            level_events.append(event)
        
        def move_handler(event):
            move_events.append(event)
        
        bus.subscribe(LevelGeneratedEvent, level_handler)
        bus.subscribe(CharacterMovedEvent, move_handler)
        
        level_event = LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1)
        move_event = CharacterMovedEvent(from_position=(0, 0), to_position=(1, 1))
        
        bus.publish(level_event)
        bus.publish(move_event)
        
        assert len(level_events) == 1
        assert len(move_events) == 1
        assert level_events[0] == level_event
        assert move_events[0] == move_event
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(LevelGeneratedEvent, handler)
        event = LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1)
        
        bus.publish(event)
        assert len(received) == 1
        
        bus.unsubscribe(LevelGeneratedEvent, handler)
        bus.publish(event)
        assert len(received) == 1  # Should not receive second event
    
    def test_unsubscribe_not_subscribed(self):
        """Test unsubscribing a handler that was never subscribed."""
        bus = EventBus()
        
        def handler(event):
            pass
        
        result = bus.unsubscribe(LevelGeneratedEvent, handler)
        assert result is False
    
    def test_clear_subscribers_for_type(self):
        """Test clearing all subscribers for a specific event type."""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(LevelGeneratedEvent, handler)
        bus.clear_subscribers(LevelGeneratedEvent)
        
        event = LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1)
        bus.publish(event)
        
        assert len(received) == 0
    
    def test_clear_all_subscribers(self):
        """Test clearing all subscribers."""
        bus = EventBus()
        received1 = []
        received2 = []
        
        def handler1(event):
            received1.append(event)
        
        def handler2(event):
            received2.append(event)
        
        bus.subscribe(LevelGeneratedEvent, handler1)
        bus.subscribe(CharacterMovedEvent, handler2)
        bus.clear_subscribers()
        
        bus.publish(LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1))
        bus.publish(CharacterMovedEvent(from_position=(0, 0), to_position=(1, 1)))
        
        assert len(received1) == 0
        assert len(received2) == 0
    
    def test_handler_exception_does_not_break_others(self):
        """Test that exception in one handler doesn't break others."""
        bus = EventBus()
        received = []
        
        def bad_handler(event):
            raise ValueError("Bad handler")
        
        def good_handler(event):
            received.append(event)
        
        bus.subscribe(LevelGeneratedEvent, bad_handler)
        bus.subscribe(LevelGeneratedEvent, good_handler)
        
        event = LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1)
        bus.publish(event)  # Should not raise
        
        assert len(received) == 1


class TestEventBusSubscriberCount:
    """Test subscriber counting."""
    
    def test_get_subscriber_count_for_type(self):
        """Test counting subscribers for a specific type."""
        bus = EventBus()
        
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        assert bus.get_subscriber_count(LevelGeneratedEvent) == 0
        
        bus.subscribe(LevelGeneratedEvent, handler1)
        assert bus.get_subscriber_count(LevelGeneratedEvent) == 1
        
        bus.subscribe(LevelGeneratedEvent, handler2)
        assert bus.get_subscriber_count(LevelGeneratedEvent) == 2
    
    def test_get_total_subscriber_count(self):
        """Test counting all subscribers."""
        bus = EventBus()
        
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        assert bus.get_subscriber_count() == 0
        
        bus.subscribe(LevelGeneratedEvent, handler1)
        bus.subscribe(CharacterMovedEvent, handler2)
        assert bus.get_subscriber_count() == 2


class TestGlobalEventBus:
    """Test global event bus instance."""
    
    def test_global_event_bus_exists(self):
        """Test that global event bus exists."""
        assert event_bus is not None
        assert isinstance(event_bus, EventBus)
    
    def test_reset_event_bus(self):
        """Test resetting the global event bus."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe(LevelGeneratedEvent, handler)
        event_bus.publish(LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1))
        assert len(received) == 1
        
        reset_event_bus()
        event_bus.publish(LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1))
        assert len(received) == 1  # Should not receive after reset


class TestEventDataclasses:
    """Test event dataclass definitions."""
    
    def test_level_generated_event(self):
        """Test LevelGeneratedEvent creation and attributes."""
        event = LevelGeneratedEvent(
            level="test_level",
            character_position=(10, 20),
            level_number=5
        )
        assert event.level == "test_level"
        assert event.character_position == (10, 20)
        assert event.level_number == 5
    
    def test_character_moved_event(self):
        """Test CharacterMovedEvent creation and attributes."""
        event = CharacterMovedEvent(
            from_position=(0, 0),
            to_position=(1, 1),
            is_transition=True
        )
        assert event.from_position == (0, 0)
        assert event.to_position == (1, 1)
        assert event.is_transition is True
    
    def test_character_moved_event_default(self):
        """Test CharacterMovedEvent with default is_transition."""
        event = CharacterMovedEvent(
            from_position=(0, 0),
            to_position=(1, 1)
        )
        assert event.is_transition is False
    
    def test_item_collected_event(self):
        """Test ItemCollectedEvent creation."""
        item = {"name": "sword", "damage": 10}
        event = ItemCollectedEvent(
            item_type="weapon",
            item=item,
            position=(5, 5)
        )
        assert event.item_type == "weapon"
        assert event.item == item
        assert event.position == (5, 5)
    
    def test_attack_performed_event(self):
        """Test AttackPerformedEvent creation."""
        event = AttackPerformedEvent(
            attacker_type="player",
            target_type="enemy",
            hit=True,
            damage=15,
            killed=True
        )
        assert event.attacker_type == "player"
        assert event.target_type == "enemy"
        assert event.hit is True
        assert event.damage == 15
        assert event.killed is True
    
    def test_attack_performed_event_default_killed(self):
        """Test AttackPerformedEvent with default killed."""
        event = AttackPerformedEvent(
            attacker_type="enemy",
            target_type="player",
            hit=False,
            damage=0
        )
        assert event.killed is False
    
    def test_events_are_frozen(self):
        """Test that events are immutable (frozen dataclasses)."""
        event = LevelGeneratedEvent(level=None, character_position=(1, 2), level_number=1)
        
        with pytest.raises(AttributeError):
            event.level_number = 2
