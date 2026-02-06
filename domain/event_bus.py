"""
Event bus for publish-subscribe communication between layers.
"""

from typing import Type, Callable, List, Dict, Any
from domain.logging_utils import log_exception


class EventBus:
    """Lightweight publish-subscribe event bus."""

    def __init__(self):
        self._subscribers: Dict[Type, List[Callable]] = {}

    def subscribe(self, event_type: Type, callback: Callable) -> None:
        """Subscribe a callback to a specific event type."""
        callbacks = self._subscribers.setdefault(event_type, [])
        if callback not in callbacks:
            callbacks.append(callback)

    def unsubscribe(self, event_type: Type, callback: Callable) -> bool:
        """Unsubscribe a callback from a specific event type."""
        callbacks = self._subscribers.get(event_type)
        if not callbacks:
            return False
        if callback in callbacks:
            callbacks.remove(callback)
            return True
        return False

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers."""
        callbacks = list(self._subscribers.get(type(event), []))
        for callback in callbacks:
            try:
                callback(event)
            except Exception as exc:
                log_exception(exc, f"EventBus {type(event).__name__} -> {getattr(callback, '__name__', repr(callback))}")

    def clear_subscribers(self, event_type: Type = None) -> None:
        """Clear all subscribers for an event type, or all subscribers."""
        if event_type is not None:
            self._subscribers.pop(event_type, None)
        else:
            self._subscribers.clear()

    def get_subscriber_count(self, event_type: Type = None) -> int:
        """Get the number of subscribers."""
        if event_type is not None:
            return len(self._subscribers.get(event_type, []))
        return sum(len(callbacks) for callbacks in self._subscribers.values())


# Global event bus instance for application-wide use
# This is a singleton pattern - all components share the same bus
event_bus = EventBus()


def reset_event_bus() -> None:
    """Reset the global event bus by clearing all subscribers."""
    event_bus.clear_subscribers()
