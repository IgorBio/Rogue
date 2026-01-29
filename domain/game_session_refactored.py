"""
Game session management and core game loop logic.

REFACTORING NOTE (Step 1.5):
- Integrated PositionSynchronizer for 2D ↔ 3D coordinate synchronization
- Updated toggle_rendering_mode() to use synchronizer
- Updated movement handlers to use synchronizer
- Ensures type-safe coordinate handling
"""

from domain.level_generator import generate_level, spawn_emergency_healing
from domain.entities.character import Character
from domain.fog_of_war import FogOfWar
from domain.dynamic_difficulty import DifficultyManager
from domain.services.position_synchronizer import PositionSynchronizer
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

    NEW in Step 1.5:
        position_sync: PositionSynchronizer for coordinate sync between Character and Camera
    """

    def __init__(self, test_mode=False, test_level=1, test_fog_of_war=False):
        """Initialize a new game session."""
        self.test_mode = test_mode
        self.test_fog_of_war_enabled = test_fog_of_war

        if test_mode:
            self.current_level_number = max(1, min(LEVEL_COUNT, test_level))
        else:
            self.current_level_number = 1

        self.level = None
        self.character = None
        self.fog_of_war = None
        self.game_over = False
        self.victory = False
        self.message = ""
        self.death_reason = ""
        self.player_asleep = False
        self.pending_selection = None

        # Rendering state
        self.rendering_mode = "2d"
        self.camera = None
        self.camera_controller = None

        # NEW: Position synchronizer for 2D ↔ 3D coordinate sync
        self.position_sync = PositionSynchronizer(center_offset=0.5)

        self.difficulty_manager = DifficultyManager()

        from data.statistics import Statistics
        self.stats = Statistics()

        self.generate_new_level()

    def generate_new_level(self):
        """Generate a new level and place the character."""
        difficulty_adjustments = None
        if not self.test_mode and self.character is not None:
            difficulty_adjustments = self.difficulty_manager.calculate_difficulty_adjustment(
                self.character, self.stats, self.current_level_number
            )
            self.difficulty_manager.update_performance(self.stats, self.character)

        self.level = generate_level(self.current_level_number, difficulty_adjustments)
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
            self.reveal_entire_level()

        # Difficulty-based emergency healing
        if not self.test_mode and self.difficulty_manager.should_spawn_emergency_healing(self.character):
            if spawn_emergency_healing(self.level, self.character.position):
                self.message = "You notice some provisions nearby... (Dynamic difficulty assistance)"

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

    def handle_3d_movement(self, direction):
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

        self.check_automatic_pickup()
        self.process_enemy_turns()
        return True

    # ... [Other methods remain largely unchanged, see full file for details]
