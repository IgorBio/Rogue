"""
Save and load game state persistence.
"""

import json
import os
from datetime import datetime

from domain.game_session import GameSession
from domain.entities.character import Character, Backpack
from domain.entities.level import Level
from domain.entities.room import Room
from domain.entities.corridor import Corridor
from domain.entities.enemy import create_enemy
from domain.entities.item import Food, Weapon, Elixir, Scroll
from domain.key_door_system import Key, Door, KeyColor
from domain.fog_of_war import FogOfWar
from domain.dynamic_difficulty import DifficultyManager
from data.statistics import Statistics
from config.game_config import ItemType
from presentation.camera import Camera
from presentation.camera import CameraController

# Save file configuration
DEFAULT_SAVE_DIR = 'saves'
AUTOSAVE_FILENAME = 'autosave.json'
SAVE_VERSION = '1.1'  # Incremented for new fields


class SaveManager:
    """
    Manages game state persistence to disk.
    """

    def __init__(self, save_dir=DEFAULT_SAVE_DIR):
        """
        Initialize save manager and create save directory if needed.

        Args:
            save_dir (str): Directory for save files
        """
        self.save_dir = save_dir
        self.autosave_file = os.path.join(save_dir, AUTOSAVE_FILENAME)
        os.makedirs(save_dir, exist_ok=True)

    def save_game(self, game_session, filename=None):
        """
        Save complete game session to file.

        Args:
            game_session: GameSession instance to save
            filename (str): Optional custom filename (defaults to autosave)

        Returns:
            bool: True if save succeeded, False otherwise
        """
        if filename is None:
            filename = self.autosave_file
        else:
            filename = os.path.join(self.save_dir, filename)

        try:
            save_data = {
                # Version and metadata
                'version': SAVE_VERSION,
                'timestamp': datetime.now().isoformat(),

                # Core game state
                'current_level_number': game_session.current_level_number,
                'character': self._serialize_character(game_session.character),
                'level': self._serialize_level(game_session.level),
                'fog_of_war': self._serialize_fog_of_war(game_session.fog_of_war),
                'statistics': game_session.stats.to_dict(),

                'rendering_mode': game_session.rendering_mode,
                'player_asleep': game_session.player_asleep,
                'game_over': game_session.game_over,
                'victory': game_session.victory,
                'message': game_session.message,
                'death_reason': game_session.death_reason,

                'pending_selection': (
                    game_session.pending_selection.to_dict()
                    if game_session.pending_selection is not None else None
                ),

                'difficulty_manager': self._serialize_difficulty_manager(
                    game_session.difficulty_manager
                ),

                'camera': self._serialize_camera(game_session.camera),

                # Test mode flags
                'test_mode': game_session.test_mode,
                'test_fog_of_war_enabled': game_session.test_fog_of_war_enabled,
            }

            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, filename=None):
        """
        Load game session data from file.

        Args:
            filename (str): Optional custom filename (defaults to autosave)

        Returns:
            dict: Save data dictionary or None if load failed
        """
        if filename is None:
            filename = self.autosave_file
        else:
            filename = os.path.join(self.save_dir, filename)

        if not os.path.exists(filename):
            return None

        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading game: {e}")
            return None

    def save_exists(self, filename=None):
        """
        Check if save file exists.

        Args:
            filename (str): Optional custom filename (defaults to autosave)

        Returns:
            bool: True if save file exists
        """
        if filename is None:
            filename = self.autosave_file
        else:
            filename = os.path.join(self.save_dir, filename)

        return os.path.exists(filename)

    def restore_game_session(self, save_data):
        """
        Restore complete GameSession from saved data.

        Args:
            save_data (dict): Dictionary loaded from save file

        Returns:
            GameSession: Restored game session instance
        """
        # Create new session with test mode flags and required factories
        test_mode = save_data.get('test_mode', False)
        test_fog = save_data.get('test_fog_of_war_enabled', False)
        # Camera factories removed - ViewManager now handles camera creation via events
        game_session = GameSession(
            test_mode=test_mode,
            test_fog_of_war=test_fog,
            statistics_factory=Statistics,
            save_manager_factory=lambda: self
        )

        # Restore level number
        game_session.current_level_number = save_data['current_level_number']

        # Restore character
        char_data = save_data['character']
        character = Character(char_data['position'][0], char_data['position'][1])
        character.health = char_data['health']
        character.max_health = char_data['max_health']
        character.strength = char_data['strength']
        character.dexterity = char_data['dexterity']
        character.active_elixirs = char_data['active_elixirs']

        # Restore equipped weapon
        if char_data['current_weapon']:
            weapon_data = char_data['current_weapon']
            character.current_weapon = Weapon(
                weapon_data['name'],
                weapon_data['strength_bonus']
            )

        # Restore backpack with all items
        character.backpack = Backpack()
        character.backpack.treasure_value = char_data['backpack']['treasure_value']
        self._restore_backpack_items(character.backpack, char_data['backpack']['items'])

        game_session.character = character

        # Restore level
        level_data = save_data['level']
        level = Level(level_data['level_number'])
        level.starting_room_index = level_data['starting_room_index']
        level.exit_room_index = level_data['exit_room_index']
        level.exit_position = tuple(level_data['exit_position']) if level_data['exit_position'] else None

        # Restore rooms with enemies and items
        self._restore_rooms(level, level_data['rooms'])

        # Restore corridors
        for corridor_data in level_data['corridors']:
            corridor = Corridor()
            for tile in corridor_data['tiles']:
                corridor.add_tile(tile[0], tile[1])
            level.add_corridor(corridor)

        # Restore doors
        if 'doors' in level_data:
            self._restore_doors(level, level_data['doors'])

        game_session.level = level

        # Restore fog of war
        fog_of_war = FogOfWar(level)
        if 'fog_of_war' in save_data and save_data['fog_of_war'] is not None:
            self._restore_fog_of_war(fog_of_war, save_data['fog_of_war'])
        game_session.fog_of_war = fog_of_war

        # Restore statistics
        game_session.stats = Statistics.from_dict(save_data['statistics'])

        game_session.rendering_mode = save_data.get('rendering_mode', '2d')
        # Do not assign via property setters that trigger transitions. Instead
        # determine saved state and restore it directly at the end of restoration.
        saved_player_asleep = save_data.get('player_asleep', False)
        saved_game_over = save_data.get('game_over', False)
        saved_victory = save_data.get('victory', False)
        game_session.message = save_data.get('message', '')
        game_session.death_reason = save_data.get('death_reason', '')

        from domain.services.item_selection import SelectionRequest
        pending_data = save_data.get('pending_selection', None)
        game_session.pending_selection = SelectionRequest.from_dict(pending_data)

        # Determine final saved GameState (priority: VICTORY > GAME_OVER > PLAYER_ASLEEP > ITEM_SELECTION > PLAYING)
        from domain.services.game_states import GameState
        if saved_victory:
            _saved_state = GameState.VICTORY
        elif saved_game_over:
            _saved_state = GameState.GAME_OVER
        elif saved_player_asleep:
            _saved_state = GameState.PLAYER_ASLEEP
        elif game_session.pending_selection is not None:
            _saved_state = GameState.ITEM_SELECTION
        else:
            _saved_state = GameState.PLAYING
        if 'difficulty_manager' in save_data and save_data['difficulty_manager'] is not None:
            game_session.difficulty_manager = self._deserialize_difficulty_manager(
                save_data['difficulty_manager']
            )
        else:
            # Fallback for old saves or explicit None
            game_session.difficulty_manager = DifficultyManager()

        if 'camera' in save_data and save_data['camera'] is not None:
            camera_data = save_data['camera']
            game_session.camera = Camera(
                camera_data['x'],
                camera_data['y'],
                angle=camera_data.get('angle', 0.0),
                fov=camera_data.get('fov', 60.0)
            )

            # Recreate camera controller
            from presentation.camera import CameraController
            game_session.camera_controller = CameraController(
                game_session.camera,
                game_session.level
            )
        else:
            # Create camera if needed (e.g., switching to 3D after load)
            game_session.camera = None
            game_session.camera_controller = None

        # Finally: restore state machine to saved state without validating transitions
        try:
            game_session.state_machine.restore_state(_saved_state)
        except Exception:
            # As a final safety net, leave session in PLAYING if restore fails
            try:
                game_session.state_machine.restore_state(GameState.PLAYING)
            except Exception:
                pass

        return game_session

    # ========================================================================
    # SERIALIZATION METHODS
    # ========================================================================

    def _serialize_character(self, character):
        """Serialize character to dictionary."""
        return {
            'position': list(character.position),
            'health': character.health,
            'max_health': character.max_health,
            'strength': character.strength,
            'dexterity': character.dexterity,
            'current_weapon': self._serialize_weapon(character.current_weapon),
            'backpack': {
                'treasure_value': character.backpack.treasure_value,
                'items': {
                    'food': [self._serialize_item(item) for item in character.backpack.get_items(ItemType.FOOD)],
                    'elixir': [self._serialize_item(item) for item in character.backpack.get_items(ItemType.ELIXIR)],
                    'scroll': [self._serialize_item(item) for item in character.backpack.get_items(ItemType.SCROLL)],
                    'weapon': [self._serialize_item(item) for item in character.backpack.get_items(ItemType.WEAPON)],
                    'key': [self._serialize_item(item) for item in character.backpack.get_items(ItemType.KEY)],
                }
            },
            'active_elixirs': character.active_elixirs
        }

    def _serialize_weapon(self, weapon):
        """Serialize weapon to dictionary."""
        if weapon is None:
            return None
        return {
            'name': weapon.name,
            'strength_bonus': weapon.strength_bonus
        }

    def _serialize_item(self, item):
        """Serialize item to dictionary with type-specific data."""
        data = {'item_type': item.item_type}

        if item.item_type == ItemType.FOOD:
            data['health_restoration'] = item.health_restoration
        elif item.item_type == ItemType.WEAPON:
            data['name'] = item.name
            data['strength_bonus'] = item.strength_bonus
        elif item.item_type == ItemType.ELIXIR:
            data['stat_type'] = item.stat_type
            data['bonus'] = item.bonus
            data['duration'] = item.duration
        elif item.item_type == ItemType.SCROLL:
            data['stat_type'] = item.stat_type
            data['bonus'] = item.bonus
        elif item.item_type == ItemType.KEY:
            data['color'] = item.color.value

        return data

    def _serialize_level(self, level):
        """Serialize complete level to dictionary."""
        return {
            'level_number': level.level_number,
            'starting_room_index': level.starting_room_index,
            'exit_room_index': level.exit_room_index,
            'exit_position': list(level.exit_position) if level.exit_position else None,
            'rooms': [self._serialize_room(room) for room in level.rooms],
            'corridors': [self._serialize_corridor(c) for c in level.corridors],
            'doors': [self._serialize_door(door) for door in level.doors]
        }

    def _serialize_room(self, room):
        """Serialize room with enemies and items."""
        return {
            'x': room.x,
            'y': room.y,
            'width': room.width,
            'height': room.height,
            'enemies': [self._serialize_enemy(e) for e in room.enemies],
            'items': [self._serialize_item_with_pos(i) for i in room.items]
        }

    def _serialize_corridor(self, corridor):
        """Serialize corridor tile list."""
        return {
            'tiles': [list(tile) for tile in corridor.tiles]
        }

    def _serialize_door(self, door):
        """Serialize door with color and lock state."""
        return {
            'color': door.color.value,
            'position': list(door.position),
            'is_locked': door.is_locked
        }

    def _serialize_enemy(self, enemy):
        """Serialize enemy with all attributes and state."""
        return {
            'enemy_type': enemy.enemy_type,
            'position': list(enemy.position),
            'health': enemy.health,
            'max_health': enemy.max_health,
            'strength': enemy.strength,
            'dexterity': enemy.dexterity,
            'is_chasing': enemy.is_chasing
        }

    def _serialize_item_with_pos(self, item):
        """Serialize item with world position."""
        data = self._serialize_item(item)
        data['position'] = list(item.position) if item.position else None
        return data

    def _serialize_fog_of_war(self, fog_of_war):
        """Serialize fog of war visibility state."""
        return {
            'discovered_rooms': list(fog_of_war.discovered_rooms),
            'discovered_corridors': list(fog_of_war.discovered_corridors),
            'current_room_index': fog_of_war.current_room_index,
            'current_corridor_index': fog_of_war.current_corridor_index,
            'visible_tiles': [list(tile) for tile in fog_of_war.visible_tiles]
        }

    def _serialize_difficulty_manager(self, dm):
        """
        Serialize difficulty manager with all modifiers and performance data.

        Args:
            dm: DifficultyManager instance

        Returns:
            dict: Serialized difficulty manager data
        """
        return {
            # Performance tracking
            'levels_completed': dm.levels_completed,
            'total_damage_taken': dm.total_damage_taken,
            'total_damage_dealt': dm.total_damage_dealt,
            'deaths_this_session': dm.deaths_this_session,
            'average_health_per_level': dm.average_health_per_level,
            'time_per_level': dm.time_per_level,

            # Difficulty modifiers
            'enemy_count_modifier': dm.enemy_count_modifier,
            'enemy_stat_modifier': dm.enemy_stat_modifier,
            'item_spawn_modifier': dm.item_spawn_modifier,
            'healing_modifier': dm.healing_modifier,

            # Configuration constants
            'min_modifier': dm.MIN_MODIFIER,
            'max_modifier': dm.MAX_MODIFIER,
            'adjustment_rate': dm.ADJUSTMENT_RATE,
        }

    def _serialize_camera(self, camera):
        """
        Serialize camera with position and orientation.

        Args:
            camera: Camera instance or None

        Returns:
            dict or None: Serialized camera data
        """
        if camera is None:
            return None

        return {
            'x': camera.x,
            'y': camera.y,
            'angle': camera.angle,
            'fov': camera.fov
        }

    # ========================================================================
    # DESERIALIZATION METHODS
    # ========================================================================

    def _restore_backpack_items(self, backpack, items_data):
        """Restore all items in backpack from saved data."""
        # Restore food items
        for food_data in items_data['food']:
            food = Food(food_data['health_restoration'])
            backpack.add_item(food)

        # Restore weapons
        for weapon_data in items_data['weapon']:
            weapon = Weapon(weapon_data['name'], weapon_data['strength_bonus'])
            backpack.add_item(weapon)

        # Restore elixirs
        for elixir_data in items_data['elixir']:
            elixir = Elixir(
                elixir_data['stat_type'],
                elixir_data['bonus'],
                elixir_data['duration']
            )
            backpack.add_item(elixir)

        # Restore scrolls
        for scroll_data in items_data['scroll']:
            scroll = Scroll(scroll_data['stat_type'], scroll_data['bonus'])
            backpack.add_item(scroll)

        # Restore keys
        if 'key' in items_data:
            for key_data in items_data['key']:
                color = KeyColor(key_data['color'])
                key = Key(color)
                backpack.add_item(key)

    def _restore_rooms(self, level, rooms_data):
        """Restore all rooms with enemies and items."""
        for room_data in rooms_data:
            room = Room(
                room_data['x'],
                room_data['y'],
                room_data['width'],
                room_data['height']
            )

            # Restore enemies
            for enemy_data in room_data['enemies']:
                enemy = create_enemy(
                    enemy_data['enemy_type'],
                    enemy_data['position'][0],
                    enemy_data['position'][1]
                )
                enemy.health = enemy_data['health']
                enemy.max_health = enemy_data['max_health']
                enemy.strength = enemy_data['strength']
                enemy.dexterity = enemy_data['dexterity']
                enemy.is_chasing = enemy_data['is_chasing']
                room.add_enemy(enemy)

            # Restore items
            for item_data in room_data['items']:
                item = self._create_item_from_data(item_data)
                if item and item_data['position']:
                    item.position = tuple(item_data['position'])
                    room.add_item(item)

            level.add_room(room)

    def _create_item_from_data(self, item_data):
        """Create item instance from serialized data."""
        item_type = item_data['item_type']

        if item_type == ItemType.FOOD:
            return Food(item_data['health_restoration'])
        elif item_type == ItemType.WEAPON:
            return Weapon(item_data['name'], item_data['strength_bonus'])
        elif item_type == ItemType.ELIXIR:
            return Elixir(
                item_data['stat_type'],
                item_data['bonus'],
                item_data['duration']
            )
        elif item_type == ItemType.SCROLL:
            return Scroll(item_data['stat_type'], item_data['bonus'])
        elif item_type == ItemType.KEY:
            color = KeyColor(item_data['color'])
            return Key(color)

        return None

    def _restore_doors(self, level, doors_data):
        """Restore all doors with colors and lock states."""
        for door_data in doors_data:
            color = KeyColor(door_data['color'])
            door = Door(color, door_data['position'][0], door_data['position'][1])
            door.is_locked = door_data['is_locked']
            level.doors.append(door)

    def _restore_fog_of_war(self, fog_of_war, fog_data):
        """Restore fog of war visibility state."""
        fog_of_war.discovered_rooms = set(fog_data.get('discovered_rooms', []))
        fog_of_war.discovered_corridors = set(fog_data.get('discovered_corridors', []))
        fog_of_war.current_room_index = fog_data.get('current_room_index')
        fog_of_war.current_corridor_index = fog_data.get('current_corridor_index')

        visible_tiles_list = fog_data.get('visible_tiles', [])
        fog_of_war.visible_tiles = set(tuple(tile) for tile in visible_tiles_list)

    def _deserialize_difficulty_manager(self, dm_data):
        """
        Deserialize difficulty manager from saved data.

        Args:
            dm_data: Dictionary with serialized difficulty manager

        Returns:
            DifficultyManager: Restored difficulty manager instance
        """
        dm = DifficultyManager()

        # Restore performance tracking
        dm.levels_completed = dm_data.get('levels_completed', 0)
        dm.total_damage_taken = dm_data.get('total_damage_taken', 0)
        dm.total_damage_dealt = dm_data.get('total_damage_dealt', 0)
        dm.deaths_this_session = dm_data.get('deaths_this_session', 0)
        dm.average_health_per_level = dm_data.get('average_health_per_level', [])
        dm.time_per_level = dm_data.get('time_per_level', [])

        # Restore difficulty modifiers
        dm.enemy_count_modifier = dm_data.get('enemy_count_modifier', 1.0)
        dm.enemy_stat_modifier = dm_data.get('enemy_stat_modifier', 1.0)
        dm.item_spawn_modifier = dm_data.get('item_spawn_modifier', 1.0)
        dm.healing_modifier = dm_data.get('healing_modifier', 1.0)

        # Restore configuration (in case it changed)
        dm.MIN_MODIFIER = dm_data.get('min_modifier', 0.5)
        dm.MAX_MODIFIER = dm_data.get('max_modifier', 1.5)
        dm.ADJUSTMENT_RATE = dm_data.get('adjustment_rate', 0.1)

        return dm
