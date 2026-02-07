"""
Game session management and core game loop logic.
"""

from common.logging_utils import log_exception
from domain.level_generator import generate_level, spawn_emergency_healing
from domain.entities.character import Character
from domain.fog_of_war import FogOfWar
from domain.dynamic_difficulty import DifficultyManager
from domain.services.game_states import GameState, StateMachine
from domain.events import LevelGeneratedEvent, CharacterMovedEvent, PlayerMovedEvent, GameEndedEvent
from domain.event_bus import event_bus
from config.game_config import GameConfig, PlayerConfig


class GameSession:
    """
    Manages the current game state and processes player actions in 2D and 3D.
    
    Attributes:
        test_mode (bool): Whether running in test mode
        test_fog_of_war_enabled (bool): Whether fog of war is enabled in test mode
        current_level_number (int): Current dungeon level (1-21)
        level: Current Level instance
        character: Player Character instance
        fog_of_war: FogOfWar instance
        message (str): Current message to display
        death_reason (str): Cause of death if game over
        pending_selection: Pending item selection data
        rendering_mode (str): Current rendering mode ('2d' or '3d')
        camera_provider: Provider of camera/controller (managed by ViewManager)
        difficulty_manager: DifficultyManager instance
        stats: Statistics instance
        state_machine: StateMachine for explicit state management
    """
    
    def __init__(self, test_mode=False, test_level=1, test_fog_of_war=False,
                 statistics_factory=None, save_manager_factory=None,
                 camera_provider=None):
        """
        Initialize a new game session.
        
        Args:
            test_mode (bool): Enable test mode with boosted stats
            test_level (int): Starting level for test mode
            test_fog_of_war (bool): Enable fog of war in test mode
            statistics_factory: Factory for creating Statistics instance
            save_manager_factory: Factory for creating SaveManager instance
            camera_provider: Provider for camera/controller (presentation layer)
        """
        self.test_mode = test_mode
        self.test_fog_of_war_enabled = test_fog_of_war
        
        if test_mode:
            self.current_level_number = max(1, min(GameConfig.TOTAL_LEVELS, test_level))
        else:
            self.current_level_number = 1
        
        self.level = None
        self.character = None
        self.fog_of_war = None
        self.message = ""
        self.death_reason = ""
        self.pending_selection = None
        
        self.rendering_mode = '2d'
        self._camera_provider = camera_provider

        self.state_machine = StateMachine()
        
        # Position synchronizer for 2D ↔ 3D coordinate sync
        
        self.difficulty_manager = DifficultyManager()

        # Dependency factories injected from outer layer to avoid direct
        # domain -> data/presentation imports. These factories are required
        # to enforce decoupling between domain and data/presentation.
        if not callable(statistics_factory):
            raise TypeError("statistics_factory is required and must be callable")
        if not callable(save_manager_factory):
            raise TypeError("save_manager_factory is required and must be callable")

        self._statistics_factory = statistics_factory
        self._save_manager_factory = save_manager_factory

        # Create statistics instance via factory
        try:
            self.stats = self._statistics_factory()
        except Exception:
            self.stats = None

        from domain.session_coordinator import SessionCoordinator
        self._coordinator = SessionCoordinator(self, self.stats, self.difficulty_manager)
        self._coordinator.initialize_services()
        
        self._generate_new_level()
        
        # Transition to PLAYING after initialization
        self.state_machine.transition_to(GameState.PLAYING)
    

    
    # ============================================================================
    # STATE MACHINE METHODS
    # ============================================================================
    
    def set_game_over(self, reason: str = "") -> None:
        """Set game over state with optional death reason.
        
        Args:
            reason: Cause of death
        """
        self.death_reason = reason
        self.state_machine.transition_to(GameState.GAME_OVER)
        # Publish game ended event for statistics tracking
        try:
            event_bus.publish(GameEndedEvent(
                victory=False,
                final_health=self.character.health,
                final_strength=self.character.strength,
                final_dexterity=self.character.dexterity,
                level_reached=self.current_level_number
            ))
        except Exception as exc:
                log_exception(exc, __name__)
    
    def set_victory(self) -> None:
        """Set victory state (won the game)."""
        self.state_machine.transition_to(GameState.VICTORY)
        # Publish game ended event for statistics tracking
        try:
            event_bus.publish(GameEndedEvent(
                victory=True,
                final_health=self.character.health,
                final_strength=self.character.strength,
                final_dexterity=self.character.dexterity,
                level_reached=self.current_level_number
            ))
        except Exception as exc:
                log_exception(exc, __name__)
    
    def set_player_asleep(self) -> None:
        """Put player to sleep (snake mage effect)."""
        self.state_machine.transition_to(GameState.PLAYER_ASLEEP)
    
    def wake_player(self) -> None:
        """Wake player from sleep."""
        if self.state_machine.is_asleep():
            self.state_machine.transition_to(GameState.PLAYING)
    
    def request_item_selection(self) -> None:
        """Transition to item selection state."""
        self.state_machine.transition_to(GameState.ITEM_SELECTION)
    
    def return_from_selection(self) -> None:
        """Return to playing from item selection."""
        if self.state_machine.is_waiting_for_selection():
            self.state_machine.transition_to(GameState.PLAYING)
    
    def begin_level_transition(self) -> None:
        """Begin level transition."""
        self.state_machine.transition_to(GameState.LEVEL_TRANSITION)
    
    def complete_level_transition(self) -> None:
        """Complete level transition, return to playing.

        Only performs the transition if the session is currently in
        `LEVEL_TRANSITION` to avoid invalid or unexpected transitions
        caused by out-of-order calls (e.g., during restore or corrupted saves).
        """
        if self.state_machine.is_transitioning_level():
            self.state_machine.transition_to(GameState.PLAYING)    
    # ============================================================================
    # CORE GAME METHODS
    # ============================================================================
    
    def _generate_new_level(self):
        """Generate a new level and place the character."""
        # Delegate generation to LevelManager via coordinator
        self.level = self._coordinator.generate_level(
            self.current_level_number,
            character=self.character,
            test_mode=self.test_mode,
        )
        self.fog_of_war = FogOfWar(self.level)

        starting_room = self.level.get_starting_room()
        start_x, start_y = starting_room.get_center()

        # Initialize or update character position
        if self.character is None:
            self.character = Character(start_x, start_y)
            if self.test_mode:
                tm = GameConfig.TEST_MODE_STATS
                self.character.health = tm['health']
                self.character.max_health = tm['max_health']
                self.character.strength = tm['strength']
                self.character.dexterity = tm['dexterity']
        else:
            self.character.move_to(start_x, start_y)

        event_bus.publish(LevelGeneratedEvent(
            level=self.level,
            character_position=(start_x, start_y),
            level_number=self.current_level_number
        ))

        self.fog_of_war.update_visibility(self.character.position)

        if self.test_mode and not self.test_fog_of_war_enabled:
            self._reveal_entire_level()

        # Difficulty-based emergency healing
        if not self.test_mode and self.difficulty_manager.should_spawn_emergency_healing(self.character):
            if spawn_emergency_healing(self.level, self.character.position):
                self.message = "You notice some provisions nearby... (Dynamic difficulty assistance)"
    
    def _reveal_entire_level(self):
        """Reveal the entire level (for test mode without fog of war)."""
        for i in range(len(self.level.rooms)):
            self.fog_of_war.discovered_rooms.add(i)
        
        for i in range(len(self.level.corridors)):
            self.fog_of_war.discovered_corridors.add(i)
        
        room, room_idx = self.level.get_room_at(
            self.character.position[0],
            self.character.position[1]
        )
        if room_idx is not None:
            self.fog_of_war.current_room_index = room_idx
    
    def toggle_rendering_mode(self):
        """
        Toggle between 2D and 3D rendering modes.

        Camera synchronization is handled by the presentation layer.
        """
        if self.rendering_mode == "2d":
            self.rendering_mode = "3d"
            self.message = "Switched to 3D view"
        else:
            self.rendering_mode = "2d"
            self.message = "Switched to 2D view"

        return self.rendering_mode

    def get_rendering_mode(self):
        """Get current rendering mode."""
        return self.rendering_mode
    
    def is_3d_mode(self):
        """Check if currently in 3D mode."""
        return self.rendering_mode == '3d'
    
    def should_use_fog_of_war(self):
        """Check if fog of war should be used for rendering."""
        if self.test_mode:
            return self.test_fog_of_war_enabled
        return True
    
    def process_player_action(self, action_type, action_data):
        """
        Process a player action (works for both 2D and 3D).
        
        Args:
            action_type (str): Type of action
            action_data: Action-specific data
            
        Returns:
            bool: Whether the action was successful
        """
        # Delegate to the coordinator
        return self._coordinator.process_action(action_type, action_data)

    def process_enemy_turns(self) -> None:
        """Process all enemy turns via coordinator."""
        return self._coordinator.process_enemy_turns()

    def handle_movement(self, direction):
        """Handle movement via coordinator."""
        return self._coordinator.handle_movement(direction)


    @property
    def game_over(self) -> bool:
        """Backward-compatible property: whether the game is over."""
        return self.state_machine.is_game_over()

    @game_over.setter
    def game_over(self, value: bool) -> None:
        if value and not self.state_machine.is_game_over():
            if not self.state_machine.is_victory():
                self.state_machine.transition_to(GameState.GAME_OVER)

    @property
    def victory(self) -> bool:
        """Backward-compatible property: whether the game is won."""
        return self.state_machine.is_victory()

    @victory.setter
    def victory(self, value: bool) -> None:
        if value and not self.state_machine.is_victory():
            if not self.state_machine.is_game_over():
                self.state_machine.transition_to(GameState.VICTORY)

    @property
    def player_asleep(self) -> bool:
        """Backward-compatible property: whether the player is asleep."""
        return self.state_machine.is_asleep()

    @player_asleep.setter
    def player_asleep(self, value: bool) -> None:
        if value and not self.state_machine.is_asleep():
            self.state_machine.transition_to(GameState.PLAYER_ASLEEP)
        elif not value and self.state_machine.is_asleep():
            self.state_machine.transition_to(GameState.PLAYING)
    
    
    def has_pending_selection(self):
        """Check if there's a pending item selection."""
        return self._coordinator.has_pending_selection()
    
    def get_pending_selection(self):
        """Get the pending selection request."""
        return self._coordinator.get_pending_selection()
    
    def complete_item_selection(self, selected_idx):
        """Complete item selection with chosen index."""
        return self._coordinator.complete_item_selection(selected_idx)

    def request_food_selection(self):
        """Request food selection via coordinator."""
        return self._coordinator.request_food_selection()

    def request_weapon_selection(self):
        """Request weapon selection via coordinator."""
        return self._coordinator.request_weapon_selection()

    def request_elixir_selection(self):
        """Request elixir selection via coordinator."""
        return self._coordinator.request_elixir_selection()

    def request_scroll_selection(self):
        """Request scroll selection via coordinator."""
        return self._coordinator.request_scroll_selection()
    
    def advance_level(self):
        """Advance to the next dungeon level."""
        return self._coordinator.advance_level(self, GameConfig.TOTAL_LEVELS)

    @property
    def combat_system(self):
        """Get combat system from coordinator."""
        return self._coordinator.combat_system

    def save_to_file(self, filename=None):
        """Save the current game state to file."""
        # Use injected save manager factory if available to avoid domain -> data import.
        try:
            save_manager = self._save_manager_factory()
            return save_manager.save_game(self, filename)
        except Exception:
            return False
    
    def get_game_stats(self):
        """Get game statistics for display."""
        stats_dict = {
            'level_reached': self.current_level_number,
            'treasure_collected': self.character.backpack.treasure_value,
            'final_health': self.character.health,
            'max_health': self.character.max_health,
            'strength': self.character.strength,
            'dexterity': self.character.dexterity,
            'enemies_defeated': self.stats.enemies_defeated,
            'items_collected': self.stats.items_collected,
            'food_consumed': self.stats.food_consumed,
            'tiles_moved': self.stats.tiles_moved,
            'attacks_made': self.stats.attacks_made,
            'hits_taken': self.stats.hits_taken,
            'damage_dealt': self.stats.damage_dealt,
            'damage_received': self.stats.damage_received,
            'elixirs_used': self.stats.elixirs_used,
            'scrolls_read': self.stats.scrolls_read,
            'victory': self.state_machine.is_victory(),
            'death_reason': self.death_reason if not self.state_machine.is_victory() else None
        }
        
        if not self.test_mode:
            stats_dict['difficulty'] = self.difficulty_manager.get_difficulty_description()
        
        return stats_dict

    def set_stats(self, stats) -> None:
        """Replace stats instance and rewire coordinator tracking."""
        self.stats = stats
        try:
            self._coordinator.update_stats(stats)
        except Exception:
            pass
    
    def reset_game(self):
        """Reset the game to start a new run."""
        # Recreate statistics via injected factory if available
        
        self.current_level_number = 1
        self.message = ""
        self.death_reason = ""
        self.character = None
        try:
            self.stats = self._statistics_factory()
        except Exception:
            self.stats = None
        self.difficulty_manager = DifficultyManager()
        # Camera and camera_controller are managed by ViewManager (via provider)
        # They will be reset via LevelGeneratedEvent when _generate_new_level is called
        self.rendering_mode = '2d'
        self.state_machine.reset_to_initial()
        self._generate_new_level()
        self.state_machine.transition_to(GameState.PLAYING)
    
    def is_game_over(self):
        """Check if the game is over (terminal state reached)."""
        return self.state_machine.is_terminal()
    
    def get_current_level(self):
        """Get the current level."""
        return self.level
    
    def get_character(self):
        """Get the character."""
        return self.character
    
    def get_fog_of_war(self):
        """Get the fog of war system."""
        return self.fog_of_war
    
    def set_camera_provider(self, provider) -> None:
        """Set camera provider (presentation layer)."""
        self._camera_provider = provider

    @property
    def camera(self):
        """Get the 3D camera (from provider)."""
        if self._camera_provider is None:
            return None
        return getattr(self._camera_provider, 'camera', None)

    @property
    def camera_controller(self):
        """Get the camera controller (from provider)."""
        if self._camera_provider is None:
            return None
        return getattr(self._camera_provider, 'camera_controller', None)

    def get_camera(self):
        """Get the 3D camera (compat)."""
        return self.camera
    
    def get_camera_controller(self):
        """Get the camera controller (compat)."""
        return self.camera_controller
    
    def get_message(self):
        """Get the current message."""
        return self.message
    
    def get_state_machine(self):
        """Get the state machine."""
        return self.state_machine

    # ============================================================================
    # Coordinator delegates (public API for services)
    # ============================================================================

    def get_item_at(self, x: int, y: int):
        """Get item at position via coordinator."""
        return self._coordinator.get_item_at(self.level, x, y)

    def get_revealed_enemy_at(self, x: int, y: int):
        """Get revealed enemy at position via coordinator."""
        return self._coordinator.get_revealed_enemy_at(self.level, x, y)

    def get_disguised_mimic_at(self, x: int, y: int):
        """Get disguised mimic at position via coordinator."""
        return self._coordinator.get_disguised_mimic_at(self.level, x, y)

    def handle_combat(self, enemy):
        """Handle combat via coordinator."""
        return self._coordinator.handle_combat(enemy)

    def pickup_item(self, item):
        """Pick up an item via coordinator."""
        return self._coordinator.pickup_item(item)

    def notify_character_moved(
        self,
        from_pos,
        to_pos,
        is_transition: bool = False,
        sync_camera: bool = True,
    ) -> None:
        """Publish movement events and update fog of war."""
        if self.should_use_fog_of_war() and self.fog_of_war is not None:
            try:
                self.fog_of_war.update_visibility(self.character.position)
            except Exception as exc:
                log_exception(exc, __name__)

        try:
            event_bus.publish(PlayerMovedEvent(from_pos=from_pos, to_pos=to_pos))
        except Exception as exc:
            log_exception(exc, __name__)

        try:
            event_bus.publish(CharacterMovedEvent(
                from_position=from_pos,
                to_position=to_pos,
                is_transition=is_transition,
                sync_camera=sync_camera,
            ))
        except Exception as exc:
            log_exception(exc, __name__)
