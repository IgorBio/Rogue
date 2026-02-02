"""
Service Container for Dependency Injection.

This module provides a centralized way to manage service dependencies,
reducing tight coupling between services and GameSession.

Usage:
    from domain.services.service_container import ServiceContainer
    
    container = ServiceContainer()
    container.register_character(character)
    container.register_level(level)
    
    action_processor = container.create_action_processor()
"""
from typing import TYPE_CHECKING, Optional, Any, Callable

if TYPE_CHECKING:
    from domain.entities.character import Character
    from domain.entities.level import Level
    from domain.services.game_states import StateMachine


class ServiceContainer:
    """
    Container for managing service dependencies.
    
    Instead of passing the entire GameSession to services,
    inject only the specific dependencies they need.
    
    Example:
        container = ServiceContainer()
        container.register_character(session.character)
        container.register_level(session.level)
        container.register_state_machine(session.state_machine)
        container.register_message_callback(lambda msg: setattr(session, 'message', msg))
        
        processor = container.create_enemy_turn_processor()
    """
    
    def __init__(self):
        # Core dependencies
        self._character: Optional['Character'] = None
        self._level: Optional['Level'] = None
        self._state_machine: Optional['StateMachine'] = None
        
        # Callbacks for session interaction
        self._message_callback: Optional[Callable[[str], None]] = None
        self._game_over_callback: Optional[Callable[[str], None]] = None
        self._victory_callback: Optional[Callable[[], None]] = None
        self._asleep_callback: Optional[Callable[[], None]] = None
        self._selection_callback: Optional[Callable[[Any], bool]] = None
        
        # Service references for inter-service communication
        self._combat_system: Optional[Any] = None
        self._inventory_manager: Optional[Any] = None
        self._movement_handler: Optional[Any] = None
        
        # Mode checks
        self._is_3d_mode: Callable[[], bool] = lambda: False
        self._should_use_fog: Callable[[], bool] = lambda: False
    
    # Registration methods
    def register_character(self, character: 'Character') -> 'ServiceContainer':
        """Register the player character."""
        self._character = character
        return self
    
    def register_level(self, level: 'Level') -> 'ServiceContainer':
        """Register the current level."""
        self._level = level
        return self
    
    def register_state_machine(self, state_machine: 'StateMachine') -> 'ServiceContainer':
        """Register the game state machine."""
        self._state_machine = state_machine
        return self
    
    def register_message_callback(self, callback: Callable[[str], None]) -> 'ServiceContainer':
        """Register callback for setting session message."""
        self._message_callback = callback
        return self
    
    def register_game_over_callback(self, callback: Callable[[str], None]) -> 'ServiceContainer':
        """Register callback for game over."""
        self._game_over_callback = callback
        return self
    
    def register_victory_callback(self, callback: Callable[[], None]) -> 'ServiceContainer':
        """Register callback for victory."""
        self._victory_callback = callback
        return self
    
    def register_asleep_callback(self, callback: Callable[[], None]) -> 'ServiceContainer':
        """Register callback for setting player asleep."""
        self._asleep_callback = callback
        return self
    
    def register_selection_callback(self, callback: Callable[[Any], bool]) -> 'ServiceContainer':
        """Register callback for item selection."""
        self._selection_callback = callback
        return self
    
    def register_mode_checks(
        self,
        is_3d_mode: Callable[[], bool],
        should_use_fog: Callable[[], bool]
    ) -> 'ServiceContainer':
        """Register mode checking functions."""
        self._is_3d_mode = is_3d_mode
        self._should_use_fog = should_use_fog
        return self
    
    def register_services(
        self,
        combat_system: Any = None,
        inventory_manager: Any = None,
        movement_handler: Any = None
    ) -> 'ServiceContainer':
        """Register other services for cross-service communication."""
        self._combat_system = combat_system
        self._inventory_manager = inventory_manager
        self._movement_handler = movement_handler
        return self
    
    # Property accessors for services
    @property
    def character(self) -> Optional['Character']:
        return self._character
    
    @property
    def level(self) -> Optional['Level']:
        return self._level
    
    @property
    def state_machine(self) -> Optional['StateMachine']:
        return self._state_machine
    
    @property
    def combat_system(self) -> Optional[Any]:
        return self._combat_system
    
    @property
    def inventory_manager(self) -> Optional[Any]:
        return self._inventory_manager
    
    @property
    def movement_handler(self) -> Optional[Any]:
        return self._movement_handler
    
    # Helper methods
    def set_message(self, message: str) -> None:
        """Set the session message via callback."""
        if self._message_callback:
            self._message_callback(message)
    
    def set_game_over(self, reason: str) -> None:
        """Trigger game over via callback."""
        if self._game_over_callback:
            self._game_over_callback(reason)
    
    def set_victory(self) -> None:
        """Trigger victory via callback."""
        if self._victory_callback:
            self._victory_callback()
    
    def set_player_asleep(self) -> None:
        """Set player asleep via callback."""
        if self._asleep_callback:
            self._asleep_callback()
    
    def request_item_selection(self, selection_request: Any) -> bool:
        """Request item selection via callback."""
        if self._selection_callback:
            return self._selection_callback(selection_request)
        return False
    
    def is_3d_mode(self) -> bool:
        """Check if in 3D mode."""
        return self._is_3d_mode()
    
    def should_use_fog_of_war(self) -> bool:
        """Check if fog of war should be used."""
        return self._should_use_fog()
    
    # Factory methods for creating services with injected dependencies
    def create_action_processor(self) -> Any:
        """Create ActionProcessor with injected dependencies."""
        from domain.services.action_processor import ActionProcessor
        return ActionProcessor(self)
    
    def create_inventory_manager(self) -> Any:
        """Create InventoryManager with injected dependencies."""
        from domain.services.inventory_manager import InventoryManager
        return InventoryManager(self)
    
    def create_enemy_turn_processor(self) -> Any:
        """Create EnemyTurnProcessor with injected dependencies."""
        from domain.services.enemy_turn_processor import EnemyTurnProcessor
        return EnemyTurnProcessor(self)
    
    def create_movement_handler(self) -> Any:
        """Create MovementHandler with injected dependencies."""
        from domain.services.movement_handler import MovementHandler
        return MovementHandler(self)


# Global container instance (can be reset for testing)
_global_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container."""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _global_container
    _global_container = ServiceContainer()
