"""
Session coordinator for managing game services.

This module provides the SessionCoordinator class that manages
the lifecycle and coordination of all game services, reducing
the complexity of GameSession.

Usage:
    from domain.session_coordinator import SessionCoordinator
    
    coordinator = SessionCoordinator(session, stats, difficulty_manager)
    coordinator.initialize_services()
    
    # Delegate actions to services
    coordinator.process_action(action_type, action_data)
"""

from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from domain.game_session import GameSession
    from data.statistics import Statistics
    from domain.dynamic_difficulty import DifficultyManager


class SessionCoordinator:
    """
    Coordinates all game services for a session.
    
    This class centralizes service management, reducing GameSession's
    responsibilities and breaking circular dependencies between
    GameSession and services.
    
    Attributes:
        session: Reference to GameSession for state access
        stats: Statistics instance
        difficulty_manager: DifficultyManager instance
        
        Services:
        - combat_system: CombatSystem for battle resolution
        - action_processor: ActionProcessor for player actions
        - level_manager: LevelManager for level generation
        - movement_handler: MovementHandler for movement logic
        - enemy_turn_processor: EnemyTurnProcessor for enemy AI
        - inventory_manager: InventoryManager for item handling
        - enemy_locator: EnemyLocator for finding enemies/items
    
    Example:
        coordinator = SessionCoordinator(session, stats, difficulty_manager)
        coordinator.initialize_services()
        coordinator.process_player_action('move', {'direction': 'north'})
    """
    
    def __init__(self, session: 'GameSession', 
                 stats: 'Statistics',
                 difficulty_manager: 'DifficultyManager'):
        """
        Initialize the coordinator.
        
        Args:
            session: GameSession instance for state access
            stats: Statistics instance
            difficulty_manager: DifficultyManager instance
        """
        self.session = session
        self.stats = stats
        self.difficulty_manager = difficulty_manager
        
        # Services initialized lazily
        self._combat_system: Optional[Any] = None
        self._action_processor: Optional[Any] = None
        self._level_manager: Optional[Any] = None
        self._movement_handler: Optional[Any] = None
        self._enemy_turn_processor: Optional[Any] = None
        self._inventory_manager: Optional[Any] = None
        self._enemy_locator: Optional[Any] = None
        
        # Statistics tracker for event-based stats
        self._statistics_tracker: Optional[Any] = None
    
    def initialize_services(self) -> None:
        """
        Initialize all services.
        
        This should be called after GameSession is fully constructed
        to avoid circular initialization issues.
        """
        from domain.services.combat_system import CombatSystem
        from domain.services.action_processor import ActionProcessor
        from domain.services.level_manager import LevelManager
        from domain.services.movement_handler import MovementHandler
        from domain.services.enemy_turn_processor import EnemyTurnProcessor
        from domain.services.inventory_manager import InventoryManager
        from domain.services.enemy_locator import EnemyLocator
        from domain.services.statistics_tracker import StatisticsTracker
        from domain.event_bus import event_bus
        
        self._combat_system = CombatSystem(self.stats)
        self._action_processor = ActionProcessor(self.session)
        self._level_manager = LevelManager(self.difficulty_manager)
        self._movement_handler = MovementHandler(self.session)
        self._enemy_turn_processor = EnemyTurnProcessor(self.session)
        self._inventory_manager = InventoryManager(self.session)
        self._enemy_locator = EnemyLocator()
        
        # Initialize and start statistics tracker
        self._statistics_tracker = StatisticsTracker(self.stats, event_bus)
        self._statistics_tracker.start_tracking()

    def update_stats(self, stats: Any) -> None:
        """Update stats reference and rewire dependent services."""
        self.stats = stats

        if self._combat_system is not None:
            self._combat_system.statistics = stats

        if self._statistics_tracker is not None:
            try:
                self._statistics_tracker.stop_tracking()
            except Exception:
                pass
            self._statistics_tracker.stats = stats
            try:
                self._statistics_tracker.start_tracking()
            except Exception:
                pass
    
    # ========================================================================
    # Service Access
    # ========================================================================
    
    @property
    def combat_system(self) -> Any:
        """Get combat system (lazy init if needed)."""
        if self._combat_system is None:
            from domain.services.combat_system import CombatSystem
            self._combat_system = CombatSystem(self.stats)
        return self._combat_system
    
    @property
    def action_processor(self) -> Any:
        """Get action processor (lazy init if needed)."""
        if self._action_processor is None:
            from domain.services.action_processor import ActionProcessor
            self._action_processor = ActionProcessor(self.session)
        return self._action_processor
    
    @property
    def level_manager(self) -> Any:
        """Get level manager (lazy init if needed)."""
        if self._level_manager is None:
            from domain.services.level_manager import LevelManager
            self._level_manager = LevelManager(self.difficulty_manager)
        return self._level_manager
    
    @property
    def movement_handler(self) -> Any:
        """Get movement handler (lazy init if needed)."""
        if self._movement_handler is None:
            from domain.services.movement_handler import MovementHandler
            self._movement_handler = MovementHandler(self.session)
        return self._movement_handler
    
    @property
    def enemy_turn_processor(self) -> Any:
        """Get enemy turn processor (lazy init if needed)."""
        if self._enemy_turn_processor is None:
            from domain.services.enemy_turn_processor import EnemyTurnProcessor
            self._enemy_turn_processor = EnemyTurnProcessor(self.session)
        return self._enemy_turn_processor
    
    @property
    def inventory_manager(self) -> Any:
        """Get inventory manager (lazy init if needed)."""
        if self._inventory_manager is None:
            from domain.services.inventory_manager import InventoryManager
            self._inventory_manager = InventoryManager(self.session)
        return self._inventory_manager
    
    @property
    def enemy_locator(self) -> Any:
        """Get enemy locator (lazy init if needed)."""
        if self._enemy_locator is None:
            from domain.services.enemy_locator import EnemyLocator
            self._enemy_locator = EnemyLocator()
        return self._enemy_locator
    
    # ========================================================================
    # Delegated Methods
    # ========================================================================
    
    def process_action(self, action_type: str, action_data: Any) -> bool:
        """
        Process a player action.
        
        Args:
            action_type: Type of action
            action_data: Action-specific data
            
        Returns:
            bool: Whether action was successful
        """
        return self.action_processor.process_action(action_type, action_data)
    
    def process_enemy_turns(self) -> None:
        """Process all enemy turns."""
        return self.enemy_turn_processor.process_enemy_turns()
    
    def generate_level(self, level_number: int, character: Any, 
                      test_mode: bool = False) -> Any:
        """
        Generate a new level.
        
        Args:
            level_number: Dungeon level number
            character: Character instance
            test_mode: Whether in test mode
            
        Returns:
            Level: Generated level
        """
        return self.level_manager.generate_level(
            level_number,
            character=character,
            stats=self.stats,
            test_mode=test_mode
        )
    
    def advance_level(self, session: 'GameSession', total_levels: int) -> bool:
        """
        Advance to next level.
        
        Args:
            session: GameSession instance
            total_levels: Total number of dungeon levels
            
        Returns:
            bool: True if advanced, False if game complete
        """
        return self.level_manager.advance_and_setup(session, total_levels)
    
    def handle_movement(self, direction) -> bool:
        """
        Handle movement action.

        Args:
            direction: Movement direction - tuple (dx, dy) for 2D or str ('forward', etc.) for 3D

        Returns:
            bool: Whether movement succeeded
        """
        if isinstance(direction, str):
            return self.movement_handler.handle_3d_movement(direction)
        return self.movement_handler.handle_2d_movement(direction)
    
    def handle_combat(self, enemy: Any) -> Any:
        """
        Handle combat with enemy.
        
        Args:
            enemy: Enemy to attack
            
        Returns:
            Combat result
        """
        return self.combat_system.process_player_attack(self.session, enemy)
    
    def pickup_item(self, item: Any) -> str:
        """
        Pick up an item.
        
        Args:
            item: Item to pick up
            
        Returns:
            str: Message about pickup
        """
        return self.inventory_manager.pickup_item(item)
    
    def complete_item_selection(self, selected_idx: int) -> Any:
        """
        Complete item selection.
        
        Args:
            selected_idx: Selected item index
            
        Returns:
            Selection result
        """
        return self.inventory_manager.complete_item_selection(selected_idx)
    
    def has_pending_selection(self) -> bool:
        """Check if there's a pending item selection."""
        return self.inventory_manager.has_pending_selection()
    
    def get_pending_selection(self) -> Any:
        """Get pending selection request."""
        return self.inventory_manager.get_pending_selection()
    
    # ========================================================================
    # Locator Methods
    # ========================================================================
    
    def get_disguised_mimic_at(self, level: Any, x: int, y: int) -> Any:
        """Get disguised mimic at position."""
        return self.enemy_locator.get_disguised_mimic_at(level, x, y)
    
    def get_revealed_enemy_at(self, level: Any, x: int, y: int) -> Any:
        """Get revealed enemy at position."""
        return self.enemy_locator.get_revealed_enemy_at(level, x, y)
    
    def get_item_at(self, level: Any, x: int, y: int) -> Any:
        """Get item at position."""
        return self.enemy_locator.get_item_at(level, x, y)
    
    def get_enemy_room(self, level: Any, enemy: Any) -> Any:
        """Get room containing enemy."""
        return self.enemy_locator.get_enemy_room(level, enemy)
    
    def get_item_room(self, item: Any) -> Any:
        """Get room containing item."""
        return self.inventory_manager.get_item_room(item)
    
    # ========================================================================
    # Selection Request Methods
    # ========================================================================
    
    def request_food_selection(self) -> Any:
        """Request food selection."""
        return self.inventory_manager.request_food_selection()
    
    def request_weapon_selection(self) -> Any:
        """Request weapon selection."""
        return self.inventory_manager.request_weapon_selection()
    
    def request_elixir_selection(self) -> Any:
        """Request elixir selection."""
        return self.inventory_manager.request_elixir_selection()
    
    def request_scroll_selection(self) -> Any:
        """Request scroll selection."""
        return self.inventory_manager.request_scroll_selection()
    
    def complete_food_selection(self, selected_idx: int) -> Any:
        """Complete food selection."""
        return self.inventory_manager._complete_food_selection(selected_idx)
    
    def complete_weapon_selection(self, selected_idx: int) -> Any:
        """Complete weapon selection."""
        return self.inventory_manager._complete_weapon_selection(selected_idx)
    
    def complete_elixir_selection(self, selected_idx: int) -> Any:
        """Complete elixir selection."""
        return self.inventory_manager._complete_elixir_selection(selected_idx)
    
    def complete_scroll_selection(self, selected_idx: int) -> Any:
        """Complete scroll selection."""
        return self.inventory_manager._complete_scroll_selection(selected_idx)
    
    def drop_weapon_on_ground(self, weapon: Any) -> Any:
        """Drop weapon on ground."""
        return self.inventory_manager._drop_weapon_on_ground(weapon)
