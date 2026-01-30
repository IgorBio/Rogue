"""
Game session management and core game loop logic.

REFACTORING NOTE (Step 2.1):
- Replaced boolean flags (game_over, victory, player_asleep) with StateMachine
- All state management now goes through state_machine.transition_to()
- Added helper properties for backward compatibility during refactoring
- State is now explicit and type-safe
- Integrated position synchronizer for 2D ↔ 3D coordinate synchronization
"""

from domain.level_generator import generate_level, spawn_emergency_healing
from domain.entities.character import Character
from domain.fog_of_war import FogOfWar
from domain.dynamic_difficulty import DifficultyManager
from domain.services.position_synchronizer import PositionSynchronizer
from domain.services.game_states import GameState, StateMachine
from utils.constants import LEVEL_COUNT, EnemyType, ItemType
from utils.raycasting import Camera
from utils.camera_controller import CameraController

# Test mode constants
TEST_MODE_HEALTH = 999
TEST_MODE_MAX_HEALTH = 999
TEST_MODE_STRENGTH = 999
TEST_MODE_DEXTERITY = 999

# Adjacent tile offsets for item dropping
ADJACENT_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (1, -1), (-1, 1), (1, 1)]

# Camera defaults
DEFAULT_CAMERA_ANGLE = 0.0
DEFAULT_CAMERA_FOV = 60.0


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
        camera: Camera instance for 3D mode
        camera_controller: CameraController instance for 3D mode
        difficulty_manager: DifficultyManager instance
        stats: Statistics instance
        state_machine: StateMachine for explicit state management
        position_sync: PositionSynchronizer for coordinate sync
    
    NEW in Step 2.1:
        state_machine: Replaces game_over, victory, player_asleep flags
    """
    
    def __init__(self, test_mode=False, test_level=1, test_fog_of_war=False):
        """
        Initialize a new game session.
        
        Args:
            test_mode (bool): Enable test mode with boosted stats
            test_level (int): Starting level for test mode
            test_fog_of_war (bool): Enable fog of war in test mode
        """
        self.test_mode = test_mode
        self.test_fog_of_war_enabled = test_fog_of_war
        
        if test_mode:
            self.current_level_number = max(1, min(LEVEL_COUNT, test_level))
        else:
            self.current_level_number = 1
        
        self.level = None
        self.character = None
        self.fog_of_war = None
        self.message = ""
        self.death_reason = ""
        self.pending_selection = None
        
        self.rendering_mode = '2d'
        self.camera = None
        self.camera_controller = None

        # NEW: State machine for explicit state management (Step 2.1)
        self.state_machine = StateMachine()
        
        # Position synchronizer for 2D ↔ 3D coordinate sync
        self.position_sync = PositionSynchronizer(center_offset=0.5)
        
        self.difficulty_manager = DifficultyManager()
        
        from data.statistics import Statistics
        self.stats = Statistics()
        # Combat system service (extract combat resolution)
        from domain.services.combat_system import CombatSystem
        self.combat_system = CombatSystem(self.stats)

        # Action processor (extract player action handling)
        from domain.services.action_processor import ActionProcessor
        self.action_processor = ActionProcessor(self)

        # Level manager service (extract level generation/progression)
        from domain.services.level_manager import LevelManager
        self.level_manager = LevelManager(self.difficulty_manager)
        from domain.services.movement_handler import MovementHandler
        self.movement_handler = MovementHandler(self)
        from domain.services.enemy_turn_processor import EnemyTurnProcessor
        self.enemy_turn_processor = EnemyTurnProcessor(self)
        from domain.services.inventory_manager import InventoryManager
        self.inventory_manager = InventoryManager(self)
        
        self._generate_new_level()
        
        # Transition to PLAYING after initialization
        self.state_machine.transition_to(GameState.PLAYING)
    
    # (Backward-compatibility properties removed — refactor completed)
    
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
        self.stats.record_game_end(self.character, victory=False)
    
    def set_victory(self) -> None:
        """Set victory state (won the game)."""
        self.state_machine.transition_to(GameState.VICTORY)
        self.stats.record_game_end(self.character, victory=True)
    
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
        """Complete level transition, return to playing."""
        self.state_machine.transition_to(GameState.PLAYING)
    
    # ============================================================================
    # CORE GAME METHODS
    # ============================================================================
    
    def _generate_new_level(self):
        """Generate a new level and place the character."""
        # Delegate generation to LevelManager to centralize generation logic
        self.level = self.level_manager.generate_level(
            self.current_level_number,
            character=self.character,
            stats=self.stats,
            test_mode=self.test_mode,
        )
        self.fog_of_war = FogOfWar(self.level)

        starting_room = self.level.get_starting_room()
        start_x, start_y = starting_room.get_center()

        # Initialize or update character position
        if self.character is None:
            self.character = Character(start_x, start_y)
            if self.test_mode:
                self.character.health = TEST_MODE_HEALTH
                self.character.max_health = TEST_MODE_MAX_HEALTH
                self.character.strength = TEST_MODE_STRENGTH
                self.character.dexterity = TEST_MODE_DEXTERITY
        else:
            self.character.move_to(start_x, start_y)

        # Initialize or update camera
        if self.camera is None:
            self.camera = Camera(
                start_x + 0.5, 
                start_y + 0.5,
                angle=DEFAULT_CAMERA_ANGLE,
                fov=DEFAULT_CAMERA_FOV
            )
            self.camera_controller = CameraController(self.camera, self.level)
        else:
            # Sync camera to new character position
            self.position_sync.sync_camera_to_character(
                self.camera, 
                self.character, 
                preserve_angle=True
            )
            self.camera_controller.level = self.level

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

        Uses PositionSynchronizer for type-safe coordinate conversion.
        """
        if self.rendering_mode == "2d":
            # Switching to 3D: sync camera to character
            self.rendering_mode = "3d"
            self.position_sync.sync_camera_to_character(
                self.camera, 
                self.character, 
                preserve_angle=True
            )
            self.message = "Switched to 3D view"
        else:
            # Switching to 2D: sync character to camera
            self.rendering_mode = "2d"
            self.position_sync.sync_character_to_camera(
                self.character, 
                self.camera, 
                snap_to_grid=True
            )
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
        
        # Delegate to the action processor service
        return self.action_processor.process_action(action_type, action_data)

    # Backwards-compatible delegators used during refactor transition.
    # Tests and older call sites may patch these on the session, so keep
    # thin wrappers that forward to the ActionProcessor implementation.
    def _process_action_2d(self, action_type, action_data):
        return self.action_processor._process_action_2d(action_type, action_data)

    def _process_action_3d(self, action_type, action_data):
        return self.action_processor._process_action_3d(action_type, action_data)

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
    
    # 2D/3D action handlers moved to `ActionProcessor` (Step 2.4)
    
    def _check_automatic_pickup(self):
        """Check and pick up items on current tile."""
        item = self._get_item_at(int(self.camera.x), int(self.camera.y))
        if item:
            pickup_message = self._pickup_item(item)
            if pickup_message:
                if self.message:
                    self.message += " | " + pickup_message
                else:
                    self.message = pickup_message
    
    def _handle_movement(self, direction):
        """Handle movement in 2D mode."""
        return self.movement_handler.handle_2d_movement(direction)
    
    def _get_disguised_mimic_at(self, x, y):
        """Get DISGUISED mimic at the specified position."""
        
        for room in self.level.rooms:
            for enemy in room.enemies:
                if (enemy.position == (x, y) and 
                    enemy.is_alive() and 
                    enemy.enemy_type == EnemyType.MIMIC and
                    hasattr(enemy, 'is_disguised') and
                    enemy.is_disguised):
                    return enemy
        return None
    
    def _get_revealed_enemy_at(self, x, y):
        """Get REVEALED enemy at the specified position."""
        
        for room in self.level.rooms:
            for enemy in room.enemies:
                if enemy.position == (x, y) and enemy.is_alive():
                    if (enemy.enemy_type == EnemyType.MIMIC and 
                        hasattr(enemy, 'is_disguised') and 
                        enemy.is_disguised):
                        continue
                    return enemy
        return None
    
    def _get_item_at(self, x, y):
        """Get item at the specified position, if any."""
        for room in self.level.rooms:
            for item in room.items:
                if item.position and item.position == (x, y):
                    return item
        return None
    
    def _process_enemy_turns(self):
        return self.enemy_turn_processor.process_enemy_turns()
    
    def _request_food_selection(self):
        return self.inventory_manager.request_food_selection()
    
    def _request_weapon_selection(self):
        return self.inventory_manager.request_weapon_selection()
    
    def _request_elixir_selection(self):
        return self.inventory_manager.request_elixir_selection()
    
    def _request_scroll_selection(self):
        return self.inventory_manager.request_scroll_selection()
    
    def complete_item_selection(self, selected_idx):
        return self.inventory_manager.complete_item_selection(selected_idx)
    
    def _complete_food_selection(self, selected_idx):
        return self.inventory_manager._complete_food_selection(selected_idx)
    
    def _complete_weapon_selection(self, selected_idx):
        return self.inventory_manager._complete_weapon_selection(selected_idx)
    
    def _drop_weapon_on_ground(self, weapon):
        return self.inventory_manager._drop_weapon_on_ground(weapon)
    
    def _complete_elixir_selection(self, selected_idx):
        return self.inventory_manager._complete_elixir_selection(selected_idx)
    
    def _complete_scroll_selection(self, selected_idx):
        return self.inventory_manager._complete_scroll_selection(selected_idx)
    
    def has_pending_selection(self):
        """Check if there's a pending item selection."""
        return self.inventory_manager.has_pending_selection()
    
    def get_pending_selection(self):
        """Get the pending selection request."""
        return self.inventory_manager.get_pending_selection()
    
    def _handle_combat(self, enemy):
        return self.combat_system.process_player_attack(self, enemy)
    
    def _get_enemy_room(self, enemy):
        """Get the room that contains the specified enemy."""
        for room in self.level.rooms:
            if enemy in room.enemies:
                return room
        return None
    
    def _pickup_item(self, item):
        return self.inventory_manager.pickup_item(item)
    
    def _get_item_room(self, item):
        return self.inventory_manager.get_item_room(item)
    
    def _advance_level(self):
        """Advance to the next level."""
        self.begin_level_transition()
        if self.current_level_number >= LEVEL_COUNT:
            self.set_victory()
            self.message = "Congratulations! You've completed all 21 levels!"
            return

        # Clear keys, advance via level manager and regenerate
        self.character.backpack.items[ItemType.KEY] = []

        new_level_num = self.level_manager.advance_to_next_level(LEVEL_COUNT)
        if new_level_num is None:
            self.set_victory()
            self.message = "Congratulations! You've completed all levels!"
            return

        self.current_level_number = new_level_num
        self.stats.record_level_reached(self.current_level_number)
        self._generate_new_level()
        self.complete_level_transition()

        if not self.test_mode:
            difficulty_desc = self.difficulty_manager.get_difficulty_description()
            self.message = f"Advanced to level {self.current_level_number}! (Difficulty: {difficulty_desc})"
        else:
            self.message = f"Advanced to level {self.current_level_number}!"

        if not self.test_mode:
            self.save_to_file()
    
    def advance_level(self):
        """Public method to advance to next level."""
        self._advance_level()
    
    def save_to_file(self, filename=None):
        """Save the current game state to file."""
        from data.save_manager import SaveManager
        save_manager = SaveManager()
        return save_manager.save_game(self, filename)
    
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
    
    def reset_game(self):
        """Reset the game to start a new run."""
        from data.statistics import Statistics
        
        self.current_level_number = 1
        self.message = ""
        self.death_reason = ""
        self.character = None
        self.stats = Statistics()
        self.difficulty_manager = DifficultyManager()
        self.camera = None
        self.camera_controller = None
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
    
    def get_camera(self):
        """Get the 3D camera."""
        return self.camera
    
    def get_camera_controller(self):
        """Get the camera controller."""
        return self.camera_controller
    
    def get_message(self):
        """Get the current message."""
        return self.message
    
    def get_state_machine(self):
        """Get the state machine (NEW in Step 2.1)."""
        return self.state_machine
