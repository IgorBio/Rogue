"""
Event bus for publish-subscribe communication between layers.

The EventBus enables loose coupling between domain, presentation,
and infrastructure layers. Domain publishes events without knowing
who consumes them, and other layers subscribe to relevant events.

Usage:
    from domain.event_bus import event_bus
    from domain.events import LevelGeneratedEvent
    
    # Subscribe to events
    def on_level_generated(event):
        print(f"Level {event.level_number} generated!")
    
    event_bus.subscribe(LevelGeneratedEvent, on_level_generated)
    
    # Publish events
    event_bus.publish(LevelGeneratedEvent(level, (x, y), level_num))
"""

from typing import Type, Callable, List, Dict, Any
from collections import defaultdict
import threading


class EventBus:
    """
    Thread-safe publish-subscribe event bus.
    
    Allows loose coupling between components by enabling
    event-driven communication without direct dependencies.
    
    Attributes:
        _subscribers: Mapping of event types to subscriber callbacks
        _lock: Thread lock for safe concurrent access
    """
    
    def __init__(self):
        """Initialize the event bus with empty subscriber mapping."""
        self._subscribers: Dict[Type, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def subscribe(self, event_type: Type, callback: Callable) -> None:
        """
        Subscribe a callback to a specific event type.
        
        Args:
            event_type: The type of event to subscribe to (class)
            callback: Function to call when event is published
        
        Example:
            def on_level_generated(event):
                print(event.level_number)
            
            event_bus.subscribe(LevelGeneratedEvent, on_level_generated)
        """
        with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: Type, callback: Callable) -> bool:
        """
        Unsubscribe a callback from a specific event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        
        Returns:
            True if callback was found and removed, False otherwise
        
        Example:
            event_bus.unsubscribe(LevelGeneratedEvent, on_level_generated)
        """
        with self._lock:
            if event_type in self._subscribers:
                if callback in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(callback)
                    return True
        return False
    
    def publish(self, event: Any) -> None:
        """
        Publish an event to all subscribers.
        
        All callbacks subscribed to the event's type will be called
        with the event as the argument. Subscribers are called
        synchronously in the order they were subscribed.
        
        Args:
            event: The event instance to publish
        
        Example:
            event_bus.publish(LevelGeneratedEvent(level, (x, y), 1))
        """
        with self._lock:
            event_type = type(event)
            callbacks = list(self._subscribers.get(event_type, []))
        
        # Call subscribers outside the lock to avoid deadlocks
        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                # Suppress errors in subscribers to prevent one subscriber
                # from breaking others. In a real app, you might want logging.
                pass
    
    def clear_subscribers(self, event_type: Type = None) -> None:
        """
        Clear all subscribers for an event type, or all subscribers.
        
        Args:
            event_type: If specified, only clear subscribers for this type.
                       If None, clear all subscribers for all types.
        
        Example:
            event_bus.clear_subscribers(LevelGeneratedEvent)
            event_bus.clear_subscribers()  # Clear everything
        """
        with self._lock:
            if event_type is not None:
                if event_type in self._subscribers:
                    del self._subscribers[event_type]
            else:
                self._subscribers.clear()
    
    def get_subscriber_count(self, event_type: Type = None) -> int:
        """
        Get the number of subscribers.
        
        Args:
            event_type: If specified, count only subscribers for this type.
                       If None, count all subscribers.
        
        Returns:
            Number of subscribers
        """
        with self._lock:
            if event_type is not None:
                return len(self._subscribers.get(event_type, []))
            else:
                return sum(len(callbacks) for callbacks in self._subscribers.values())


# Global event bus instance for application-wide use
# This is a singleton pattern - all components share the same bus
event_bus = EventBus()


def reset_event_bus() -> None:
    """
    Reset the global event bus by clearing all subscribers.
    
    Useful for testing to ensure clean state between tests.
    """
    event_bus.clear_subscribers()
