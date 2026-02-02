"""
Session Protocol - defines the interface that services need from GameSession.

This module provides an abstract interface (Protocol) that services can use
instead of tight coupling to GameSession. This enables:
1. Better testability - mock sessions can implement the protocol
2. Clear dependency documentation
3. Gradual migration toward full Dependency Injection

Usage:
    from domain.services.session_protocol import SessionProtocol
    
    def process_action(processor: ActionProcessor, session: SessionProtocol):
        # session has all required attributes
        pass
"""
from typing import Protocol, runtime_checkable, Any, Optional, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.character import Character
    from domain.entities.level import Level
    from domain.services.game_states import StateMachine


@runtime_checkable
class SessionProtocol(Protocol):
    """
    Protocol defining the interface services need from GameSession.
    
    This allows services to work with any object that provides these
    attributes, not just GameSession. Useful for testing and future
    architectural changes.
    
    Attributes:
        character: The player character
        level: The current dungeon level
        state_machine: Game state management
        message: Current UI message (read/write)
        stats: Game statistics
        camera: 3D camera (optional)
        camera_controller: Camera controller (optional)
        fog_of_war: Fog of war system (optional)
    """
    
    # Core entities
    character: 'Character'
    level: 'Level'
    state_machine: 'StateMachine'
    
    # Mutable state
    message: str
    stats: Any
    
    # Optional 3D components
    camera: Optional[Any]
    camera_controller: Optional[Any]
    fog_of_war: Optional[Any]
    
    # Methods services need
    def is_3d_mode(self) -> bool:
        """Check if game is in 3D mode."""
        ...
    
    def should_use_fog_of_war(self) -> bool:
        """Check if fog of war should be used."""
        ...
    
    def set_game_over(self, reason: str) -> None:
        """Set game over state."""
        ...
    
    def set_victory(self) -> None:
        """Set victory state."""
        ...
    
    def set_player_asleep(self) -> None:
        """Set player asleep state."""
        ...
    
    def request_item_selection(self) -> bool:
        """Request item selection from player."""
        ...


class SessionAdapter:
    """
    Adapter that wraps GameSession to provide explicit interface.
    
    This adapter makes dependencies explicit and can be used
    to gradually migrate services away from direct session access.
    
    Example:
        # Instead of:
        service = SomeService(session)
        
        # Use:
        adapter = SessionAdapter(session)
        service = SomeService(adapter)
    """
    
    def __init__(self, session: Any):
        self._session = session
    
    @property
    def character(self) -> Any:
        return self._session.character
    
    @property
    def level(self) -> Any:
        return self._session.level
    
    @property
    def state_machine(self) -> Any:
        return self._session.state_machine
    
    @property
    def message(self) -> str:
        return self._session.message
    
    @message.setter
    def message(self, value: str) -> None:
        self._session.message = value
    
    @property
    def stats(self) -> Any:
        return self._session.stats
    
    @property
    def camera(self) -> Optional[Any]:
        return getattr(self._session, 'camera', None)
    
    @property
    def camera_controller(self) -> Optional[Any]:
        return getattr(self._session, 'camera_controller', None)
    
    @property
    def fog_of_war(self) -> Optional[Any]:
        return getattr(self._session, 'fog_of_war', None)
    
    def is_3d_mode(self) -> bool:
        return self._session.is_3d_mode()
    
    def should_use_fog_of_war(self) -> bool:
        return self._session.should_use_fog_of_war()
    
    def set_game_over(self, reason: str) -> None:
        self._session.set_game_over(reason)
    
    def set_victory(self) -> None:
        self._session.set_victory()
    
    def set_player_asleep(self) -> None:
        self._session.set_player_asleep()
    
    def request_item_selection(self) -> bool:
        return self._session.request_item_selection()


# Type alias for backward compatibility
SessionLike = Any  # Can be GameSession, SessionAdapter, or mock for testing
