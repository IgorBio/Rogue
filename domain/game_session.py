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

        # Level manager service (extract level generation/progression)
        from domain.services.level_manager import LevelManager
        self.level_manager = LevelManager(self.difficulty_manager)
        
        self._generate_new_level()
        
        # Transition to PLAYING after initialization
        self.state_machine.transition_to(GameState.PLAYING)
    
    # ============================================================================
    # BACKWARD COMPATIBILITY PROPERTIES (During refactoring transition)
    # ============================================================================
    
    @property
    def game_over(self) -> bool:
        """Check if game is over (died). Uses state machine."""
        return self.state_machine.is_game_over()
    
    @game_over.setter
    def game_over(self, value: bool) -> None:
        """Set game over state (for backward compatibility)."""
        if value and not self.state_machine.is_game_over():
            if not self.state_machine.is_victory():
                self.state_machine.transition_to(GameState.GAME_OVER)
    
    @property
    def victory(self) -> bool:
        """Check if game is won. Uses state machine."""
        return self.state_machine.is_victory()
    
    @victory.setter
    def victory(self, value: bool) -> None:
        """Set victory state (for backward compatibility)."""
        if value and not self.state_machine.is_victory():
            if not self.state_machine.is_game_over():
                self.state_machine.transition_to(GameState.VICTORY)
    
    @property
    def player_asleep(self) -> bool:
        """Check if player is asleep. Uses state machine."""
        return self.state_machine.is_asleep()
    
    @player_asleep.setter
    def player_asleep(self, value: bool) -> None:
        """Set asleep state (for backward compatibility)."""
        if value and not self.state_machine.is_asleep():
            self.state_machine.transition_to(GameState.PLAYER_ASLEEP)
        elif not value and self.state_machine.is_asleep():
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
        
        # Check if player is asleep
        if self.state_machine.is_asleep():
            self.message = "You are asleep and cannot act this turn!"
            self.state_machine.transition_to(GameState.PLAYING)
            self._process_enemy_turns()
            return False
        
        # Check if game is over
        if self.state_machine.is_terminal():
            self.message = "Game is over!"
            return False
        
        self.message = ""
        
        if self.is_3d_mode():
            return self._process_action_3d(action_type, action_data)
        else:
            return self._process_action_2d(action_type, action_data)
    
    def _process_action_2d(self, action_type, action_data):
        """Process actions in 2D mode."""
        from presentation.input_handler import InputHandler
        
        if action_type == InputHandler.ACTION_MOVE:
            return self._handle_movement(action_data)
        elif action_type == InputHandler.ACTION_USE_FOOD:
            return self._request_food_selection()
        elif action_type == InputHandler.ACTION_USE_WEAPON:
            return self._request_weapon_selection()
        elif action_type == InputHandler.ACTION_USE_ELIXIR:
            return self._request_elixir_selection()
        elif action_type == InputHandler.ACTION_USE_SCROLL:
            return self._request_scroll_selection()
        elif action_type == InputHandler.ACTION_QUIT:
            self.set_game_over("Game quit by player")
            self.message = "Game quit by player."
            return True
        elif action_type == InputHandler.ACTION_NONE:
            return False
        else:
            self.message = "Action not yet implemented."
            return False
    
    def _process_action_3d(self, action_type, action_data):
        """Process actions in 3D mode."""
        from utils.input_handler_3d import InputHandler3D
        
        if action_type == InputHandler3D.ACTION_MOVE_FORWARD:
            return self._handle_3d_movement('forward')
        elif action_type == InputHandler3D.ACTION_MOVE_BACKWARD:
            return self._handle_3d_movement('backward')
        elif action_type == InputHandler3D.ACTION_STRAFE_LEFT:
            return self._handle_3d_movement('strafe_left')
        elif action_type == InputHandler3D.ACTION_STRAFE_RIGHT:
            return self._handle_3d_movement('strafe_right')
        elif action_type == InputHandler3D.ACTION_ROTATE_LEFT:
            self.camera_controller.rotate_left()
            self.message = f"Facing {self.camera_controller.get_direction_name()}"
            return True
        elif action_type == InputHandler3D.ACTION_ROTATE_RIGHT:
            self.camera_controller.rotate_right()
            self.message = f"Facing {self.camera_controller.get_direction_name()}"
            return True
        elif action_type == InputHandler3D.ACTION_INTERACT:
            return self._handle_3d_interact()
        elif action_type == InputHandler3D.ACTION_ATTACK:
            return self._handle_3d_attack()
        elif action_type == InputHandler3D.ACTION_PICKUP:
            return self._handle_3d_pickup()
        elif action_type == InputHandler3D.ACTION_USE_FOOD:
            return self._request_food_selection()
        elif action_type == InputHandler3D.ACTION_USE_WEAPON:
            return self._request_weapon_selection()
        elif action_type == InputHandler3D.ACTION_USE_ELIXIR:
            return self._request_elixir_selection()
        elif action_type == InputHandler3D.ACTION_USE_SCROLL:
            return self._request_scroll_selection()
        elif action_type == InputHandler3D.ACTION_QUIT:
            self.set_game_over("Game quit by player")
            self.message = "Game quit by player."
            return True
        elif action_type == InputHandler3D.ACTION_NONE:
            return False
        else:
            return False
    
    def _handle_3d_movement(self, direction):
        """
        Handle 3D movement and sync with character.

        Uses PositionSynchronizer to keep character synced with camera.
        """
        # Move camera
        if direction == "forward":
            success = self.camera_controller.move_forward()
        elif direction == "backward":
            success = self.camera_controller.move_backward()
        elif direction == "strafe_left":
            success = self.camera_controller.strafe_left()
        elif direction == "strafe_right":
            success = self.camera_controller.strafe_right()
        else:
            return False

        if not success:
            self.message = "Can't move there - blocked!"
            return False

        # Sync character to new camera position
        new_x, new_y = self.camera.grid_position
        self.character.move_to(new_x, new_y)

        if self.should_use_fog_of_war():
            self.fog_of_war.update_visibility(self.character.position)

        self.stats.record_movement()

        # Check for level exit
        if self.level.exit_position == (new_x, new_y):
            self.advance_level()
            return True

        self._check_automatic_pickup()
        self._process_enemy_turns()
        return True
    
    def _handle_3d_interact(self):
        """Handle smart interaction in 3D mode."""
        entity, entity_type, distance = self.camera_controller.get_entity_in_front(self.level)
        
        if entity_type == 'enemy':
            return self._handle_3d_attack()
        elif entity_type == 'item':
            return self._handle_3d_pickup()
        elif entity_type == 'exit':
            return self._handle_3d_movement('forward')
        else:
            success, message = self.camera_controller.try_open_door(self.character)
            self.message = message
            return success
    
    def _handle_3d_attack(self):
        """Handle attack in 3D mode."""
        success, message, result = self.camera_controller.attack_entity_in_front(
            self.character, self.level
        )
        
        self.message = message
        
        if success and result:
            self.stats.record_attack(result['hit'], result.get('damage', 0))
            
            if result['killed'] and result.get('treasure'):
                self.stats.record_enemy_defeated(result['treasure'])
            
            if not self.state_machine.is_terminal():
                self._process_enemy_turns()
        
        return success
    
    def _handle_3d_pickup(self):
        """Handle item pickup in 3D mode."""
        success, message, item = self.camera_controller.pickup_item_in_front(
            self.character, self.level
        )
        
        self.message = message
        
        if success:
            self.stats.record_item_collected()
        
        return success
    
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
        
        dx, dy = direction
        current_x, current_y = self.character.position
        new_x = current_x + dx
        new_y = current_y + dy
        
        door = self.level.get_door_at(new_x, new_y)
        if door and door.is_locked:
            from domain.key_door_system import unlock_door_if_possible
            
            if unlock_door_if_possible(door, self.character):
                self.message = f"Unlocked {door.color.value} door!"
                return True
            else:
                self.message = f"Locked {door.color.value} door - need {door.color.value} key!"
                return False
        
        if not self.level.is_walkable(new_x, new_y):
            self.message = "You can't move there - it's a wall!"
            return False
        
        mimic_at_pos = self._get_disguised_mimic_at(new_x, new_y)
        if mimic_at_pos:
            mimic_at_pos.reveal()
            mimic_at_pos.is_chasing = True
            self.message = "It's a MIMIC! The item was a trap!"
            
            combat_result = self._handle_combat(mimic_at_pos)
            
            if combat_result and not mimic_at_pos.is_alive():
                self.character.move_to(new_x, new_y)
                
                if self.is_3d_mode():
                    self.camera.x = new_x
                    self.camera.y = new_y
                
                if self.should_use_fog_of_war():
                    self.fog_of_war.update_visibility(self.character.position)
                
                self.stats.record_movement()
                
                item = self._get_item_at(new_x, new_y)
                if item:
                    pickup_message = self._pickup_item(item)
                    if pickup_message:
                        self.message += " | " + pickup_message
            
            if not self.state_machine.is_terminal():
                self._process_enemy_turns()
            
            return combat_result
        
        enemy = self._get_revealed_enemy_at(new_x, new_y)
        if enemy:
            combat_result = self._handle_combat(enemy)
            if combat_result and not self.state_machine.is_terminal():
                self._process_enemy_turns()
            return combat_result
        
        item = self._get_item_at(new_x, new_y)
        if item:
            pickup_message = self._pickup_item(item)
            if pickup_message:
                self.message = pickup_message
        
        self.character.move_to(new_x, new_y)
        
        if self.is_3d_mode():
            self.camera.x = new_x
            self.camera.y = new_y
        
        if self.should_use_fog_of_war():
            self.fog_of_war.update_visibility(self.character.position)
        
        self.stats.record_movement()
        
        if self.level.exit_position == (new_x, new_y):
            self._advance_level()
            return True
        
        self._process_enemy_turns()
        return True
    
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
        """Process all enemy turns after player action."""
        from utils.pathfinding import get_distance
        from domain.combat import get_combat_message
        from domain.enemy_ai import (
            get_enemy_movement, 
            get_special_attack_effects, 
            handle_post_attack, 
            should_enemy_attack
        )
        
        elixir_messages = self.character.update_elixirs()
        if elixir_messages:
            if self.message:
                self.message += " | " + " ".join(elixir_messages)
            else:
                self.message = " ".join(elixir_messages)
        
        combat_messages = []
        enemies = [e for e in self.level.get_all_enemies() if e.is_alive()]
        
        player_pos = (int(self.character.position[0]), int(self.character.position[1]))
        
        for enemy in enemies:
            enemy_pos = enemy.position
            distance = get_distance(enemy_pos, player_pos)
            
            if distance == 1:
                if enemy.enemy_type == EnemyType.MIMIC and hasattr(enemy, 'is_disguised') and enemy.is_disguised:
                    continue
                
                if should_enemy_attack(enemy):
                    result = self.combat_system.resolve_enemy_attack(enemy, self.character)
                    special_effects = get_special_attack_effects(enemy, result)
                    combat_messages.append(get_combat_message(result))

                    if result.get('hit'):
                        # health steal / sleep / counterattack effects
                        if special_effects['health_steal'] > 0:
                            self.character.max_health -= special_effects['health_steal']
                            if self.character.max_health < 1:
                                self.character.max_health = 1
                            if self.character.health > self.character.max_health:
                                self.character.health = self.character.max_health
                            combat_messages.append(f"Vampire stole {special_effects['health_steal']} max health!")

                        if special_effects['sleep']:
                            self.set_player_asleep()
                            combat_messages.append("Snake Mage puts you to sleep!")

                        if special_effects['counterattack']:
                            combat_messages.append("Ogre counterattacks!")

                    handle_post_attack(enemy, result)

                    if result.get('killed'):
                        self.set_game_over(f"Killed by {enemy.enemy_type}")
                        combat_messages.append("You have died!")
                        break
                else:
                    if enemy.enemy_type == EnemyType.OGRE:
                        enemy.is_resting = False
                        enemy.will_counterattack = True
            else:
                new_pos = get_enemy_movement(enemy, player_pos, self.level, enemies)
                if new_pos:
                    enemy.move_to(new_pos[0], new_pos[1])
        
        if combat_messages:
            if self.message:
                self.message += " | " + " ".join(combat_messages)
            else:
                self.message = " ".join(combat_messages)
    
    def _request_food_selection(self):
        """Request food selection from presentation layer."""
        
        food_items = self.character.backpack.get_items(ItemType.FOOD)
        if not food_items:
            self.message = "No food in backpack!"
            return False
        
        self.pending_selection = {
            'type': 'food',
            'items': food_items,
            'title': 'Select Food to Consume',
            'allow_zero': False
        }
        self.request_item_selection()
        return True
    
    def _request_weapon_selection(self):
        """Request weapon selection from presentation layer."""
        
        weapon_items = self.character.backpack.get_items(ItemType.WEAPON)
        
        if not weapon_items and not self.character.current_weapon:
            self.message = "No weapons available!"
            return False
        
        self.pending_selection = {
            'type': 'weapon',
            'items': weapon_items,
            'title': 'Select Weapon to Equip (0 to unequip current)',
            'allow_zero': True
        }
        self.request_item_selection()
        return True
    
    def _request_elixir_selection(self):
        """Request elixir selection from presentation layer."""
        
        elixir_items = self.character.backpack.get_items(ItemType.ELIXIR)
        if not elixir_items:
            self.message = "No elixirs in backpack!"
            return False
        
        self.pending_selection = {
            'type': 'elixir',
            'items': elixir_items,
            'title': 'Select Elixir to Drink',
            'allow_zero': False
        }
        self.request_item_selection()
        return True
    
    def _request_scroll_selection(self):
        """Request scroll selection from presentation layer."""
        
        scroll_items = self.character.backpack.get_items(ItemType.SCROLL)
        if not scroll_items:
            self.message = "No scrolls in backpack!"
            return False
        
        self.pending_selection = {
            'type': 'scroll',
            'items': scroll_items,
            'title': 'Select Scroll to Read',
            'allow_zero': False
        }
        self.request_item_selection()
        return True
    
    def complete_item_selection(self, selected_idx):
        """Complete a pending item selection."""
        if self.pending_selection is None:
            return False
        
        selection_type = self.pending_selection['type']
        
        if selected_idx is None:
            self.message = f"Cancelled {selection_type} selection."
            self.pending_selection = None
            self.return_from_selection()
            return False
        
        if selection_type == 'food':
            result = self._complete_food_selection(selected_idx)
        elif selection_type == 'weapon':
            result = self._complete_weapon_selection(selected_idx)
        elif selection_type == 'elixir':
            result = self._complete_elixir_selection(selected_idx)
        elif selection_type == 'scroll':
            result = self._complete_scroll_selection(selected_idx)
        else:
            result = False
        
        self.pending_selection = None
        self.return_from_selection()
        
        if result and not self.state_machine.is_terminal():
            self._process_enemy_turns()
        
        return result
    
    def _complete_food_selection(self, selected_idx):
        """Complete food usage."""
        
        food_items = self.character.backpack.get_items(ItemType.FOOD)
        if selected_idx >= len(food_items):
            self.message = "Invalid selection!"
            return False
        
        food = food_items[selected_idx]
        message = self.character.use_food(food)
        self.character.backpack.remove_item(ItemType.FOOD, selected_idx)
        self.stats.record_food_used()
        self.message = message
        return True
    
    def _complete_weapon_selection(self, selected_idx):
        """Complete weapon equipping with drop logic."""
        
        weapon_items = self.character.backpack.get_items(ItemType.WEAPON)
        
        if selected_idx == -1:
            old_weapon, message, should_drop = self.character.unequip_weapon()
            
            if old_weapon and should_drop:
                drop_success = self._drop_weapon_on_ground(old_weapon)
                if drop_success:
                    self.message = f"{message} - dropped on ground"
                else:
                    self.message = f"{message} - no space to drop!"
            else:
                self.message = message
            
            return True
        
        if selected_idx < 0 or selected_idx >= len(weapon_items):
            self.message = "Invalid weapon selection!"
            return False
        
        weapon = weapon_items[selected_idx]
        old_weapon, message = self.character.equip_weapon(weapon)
        self.character.backpack.remove_item(ItemType.WEAPON, selected_idx)
        
        if old_weapon:
            success = self.character.backpack.add_item(old_weapon)
            if not success:
                drop_success = self._drop_weapon_on_ground(old_weapon)
                if drop_success:
                    self.message = f"{message} - old weapon dropped (backpack full)"
                else:
                    self.message = f"{message} - old weapon vanished (no space)!"
            else:
                self.message = message
        else:
            self.message = message
        
        self.stats.record_weapon_equipped()
        return True
    
    def _drop_weapon_on_ground(self, weapon):
        """Drop a weapon onto a neighboring tile."""
        player_x, player_y = int(self.character.position[0]), int(self.character.position[1])
        
        player_room, player_room_idx = self.level.get_room_at(player_x, player_y)
        
        for dx, dy in ADJACENT_OFFSETS:
            pos_x, pos_y = player_x + dx, player_y + dy
            
            if not self.level.is_walkable(pos_x, pos_y):
                continue
            
            if self._get_revealed_enemy_at(pos_x, pos_y):
                continue
            
            if self._get_item_at(pos_x, pos_y):
                continue
            
            weapon.position = (pos_x, pos_y)
            
            drop_room, drop_room_idx = self.level.get_room_at(pos_x, pos_y)
            
            if drop_room:
                drop_room.add_item(weapon)
            else:
                if player_room:
                    player_room.add_item(weapon)
            
            return True
        
        return False
    
    def _complete_elixir_selection(self, selected_idx):
        """Complete elixir usage."""
        
        elixir_items = self.character.backpack.get_items(ItemType.ELIXIR)
        if selected_idx >= len(elixir_items):
            self.message = "Invalid selection!"
            return False
        
        elixir = elixir_items[selected_idx]
        message = self.character.use_elixir(elixir)
        self.character.backpack.remove_item(ItemType.ELIXIR, selected_idx)
        self.stats.record_elixir_used()
        self.message = message
        return True
    
    def _complete_scroll_selection(self, selected_idx):
        """Complete scroll usage."""
        
        scroll_items = self.character.backpack.get_items(ItemType.SCROLL)
        if selected_idx >= len(scroll_items):
            self.message = "Invalid selection!"
            return False
        
        scroll = scroll_items[selected_idx]
        message = self.character.use_scroll(scroll)
        self.character.backpack.remove_item(ItemType.SCROLL, selected_idx)
        self.stats.record_scroll_used()
        self.message = message
        return True
    
    def has_pending_selection(self):
        """Check if there's a pending item selection."""
        return self.pending_selection is not None
    
    def get_pending_selection(self):
        """Get the pending selection request."""
        return self.pending_selection
    
    def _handle_combat(self, enemy):
        """Handle combat with an enemy."""
        from domain.combat import resolve_attack, calculate_treasure_reward, get_combat_message
        
        messages = []
        
        player_will_miss = False
        if enemy.enemy_type == EnemyType.VAMPIRE and getattr(enemy, 'first_attack_against', True):
            player_will_miss = True
            enemy.first_attack_against = False
        
        if player_will_miss:
            player_result = {
                'hit': False,
                'damage': 0,
                'killed': False,
                'attacker_name': 'You',
                'defender_name': enemy.enemy_type.capitalize()
            }
            messages.append("Your first attack against the vampire misses! (Vampire ability)")
        else:
            player_result = self.combat_system.resolve_player_attack(self.character, enemy, self.character.current_weapon)
            messages.append(get_combat_message(player_result))
        
        self.stats.record_attack(player_result['hit'], player_result.get('damage', 0))
        
        if player_result['killed']:
            treasure = calculate_treasure_reward(enemy, self.current_level_number)
            self.character.backpack.treasure_value += treasure
            self.stats.record_enemy_defeated(treasure)
            messages.append(f"Gained {treasure} treasure!")
            
            enemy_room = self._get_enemy_room(enemy)
            if enemy_room:
                enemy_room.remove_enemy(enemy)
            
            self.character.move_to(enemy.position[0], enemy.position[1])
            
            if self.is_3d_mode():
                self.camera.x = enemy.position[0]
                self.camera.y = enemy.position[1]
            
            if self.should_use_fog_of_war():
                self.fog_of_war.update_visibility(self.character.position)
            
            item = self._get_item_at(enemy.position[0], enemy.position[1])
            if item:
                pickup_message = self._pickup_item(item)
                if pickup_message:
                    messages.append(pickup_message)
            
            self.message = " ".join(messages)
            return True
        
        self.message = " ".join(messages)
        return True
    
    def _get_enemy_room(self, enemy):
        """Get the room that contains the specified enemy."""
        for room in self.level.rooms:
            if enemy in room.enemies:
                return room
        return None
    
    def _pickup_item(self, item):
        """Pick up an item and add it to the backpack."""
        
        success = self.character.backpack.add_item(item)
        
        if success:
            self.stats.record_item_collected()
            
            item_room = self._get_item_room(item)
            if item_room:
                item_room.remove_item(item)
            
            if item.item_type == ItemType.TREASURE:
                return f"Picked up {item.value} treasure!"
            elif item.item_type == ItemType.FOOD:
                return f"Picked up food (heals {item.health_restoration} HP)"
            elif item.item_type == ItemType.WEAPON:
                return f"Picked up {item.name}"
            elif item.item_type == ItemType.ELIXIR:
                return f"Picked up elixir ({item.stat_type} +{item.bonus})"
            elif item.item_type == ItemType.SCROLL:
                return f"Picked up scroll ({item.stat_type} +{item.bonus})"
            elif item.item_type == ItemType.KEY:
                return f"Picked up {item.color.value} key!"
            else:
                return "Picked up item"
        else:
            return f"Backpack full! Can't pick up item."
    
    def _get_item_room(self, item):
        """Get the room that contains the specified item."""
        for room in self.level.rooms:
            if item in room.items:
                return room
        return None
    
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
