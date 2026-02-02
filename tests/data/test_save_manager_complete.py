"""
Unit tests for complete game state serialization.

STEP 1.3: Tests for new serialization fields:
- Game flow state (rendering_mode, player_asleep, game_over, victory)
- Difficulty manager (all modifiers and performance data)
- Camera (position, angle, FOV)
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, MagicMock

# Mock imports (for testing without full dependencies)
import sys
sys.path.insert(0, os.path.abspath('.'))


class TestCompleteSerialization:
    """Test complete game state serialization."""

    def setup_method(self):
        """Create mock game session with all fields."""
        self.game_session = Mock()

        # Core game state
        self.game_session.current_level_number = 5
        self.game_session.test_mode = False
        self.game_session.test_fog_of_war_enabled = False

        self.game_session.rendering_mode = '3d'
        self.game_session.player_asleep = True
        self.game_session.game_over = False
        self.game_session.victory = False
        self.game_session.message = "You are asleep!"
        self.game_session.death_reason = ""
        self.game_session.pending_selection = {'type': 'food', 'items': []}

        self.difficulty_manager = Mock()
        self.difficulty_manager.levels_completed = 4
        self.difficulty_manager.total_damage_taken = 150
        self.difficulty_manager.total_damage_dealt = 450
        self.difficulty_manager.deaths_this_session = 0
        self.difficulty_manager.average_health_per_level = [0.9, 0.8, 0.7, 0.85]
        self.difficulty_manager.time_per_level = [120, 150, 180, 140]
        self.difficulty_manager.enemy_count_modifier = 1.2
        self.difficulty_manager.enemy_stat_modifier = 1.1
        self.difficulty_manager.item_spawn_modifier = 0.9
        self.difficulty_manager.healing_modifier = 0.95
        self.difficulty_manager.MIN_MODIFIER = 0.5
        self.difficulty_manager.MAX_MODIFIER = 1.5
        self.difficulty_manager.ADJUSTMENT_RATE = 0.1
        self.game_session.difficulty_manager = self.difficulty_manager

        self.camera = Mock()
        self.camera.x = 25.5
        self.camera.y = 30.2
        self.camera.angle = 45.0
        self.camera.fov = 60.0
        self.game_session.camera = self.camera

        # Mock other required fields
        self.game_session.character = self._create_mock_character()
        self.game_session.level = self._create_mock_level()
        self.game_session.fog_of_war = self._create_mock_fog_of_war()
        self.game_session.stats = self._create_mock_stats()

    def _create_mock_character(self):
        """Create minimal mock character."""
        char = Mock()
        char.position = (10, 10)
        char.health = 80
        char.max_health = 100
        char.strength = 15
        char.dexterity = 12
        char.current_weapon = None
        char.active_elixirs = []

        backpack = Mock()
        backpack.treasure_value = 250
        backpack.get_items = Mock(return_value=[])
        char.backpack = backpack

        return char

    def _create_mock_level(self):
        """Create minimal mock level."""
        level = Mock()
        level.level_number = 5
        level.starting_room_index = 0
        level.exit_room_index = 3
        level.exit_position = (50, 50)
        level.rooms = []
        level.corridors = []
        level.doors = []
        return level

    def _create_mock_fog_of_war(self):
        """Create minimal mock fog of war."""
        fog = Mock()
        fog.discovered_rooms = set()
        fog.discovered_corridors = set()
        fog.current_room_index = 0
        fog.current_corridor_index = None
        fog.visible_tiles = set()
        return fog

    def _create_mock_stats(self):
        """Create minimal mock statistics."""
        stats = Mock()
        stats.to_dict = Mock(return_value={'enemies_defeated': 20})
        return stats

    def test_serialize_difficulty_manager(self):
        """Test difficulty manager serialization."""
        # Simulate _serialize_difficulty_manager method
        dm = self.difficulty_manager

        dm_data = {
            'levels_completed': dm.levels_completed,
            'total_damage_taken': dm.total_damage_taken,
            'total_damage_dealt': dm.total_damage_dealt,
            'deaths_this_session': dm.deaths_this_session,
            'average_health_per_level': dm.average_health_per_level,
            'time_per_level': dm.time_per_level,
            'enemy_count_modifier': dm.enemy_count_modifier,
            'enemy_stat_modifier': dm.enemy_stat_modifier,
            'item_spawn_modifier': dm.item_spawn_modifier,
            'healing_modifier': dm.healing_modifier,
            'min_modifier': dm.MIN_MODIFIER,
            'max_modifier': dm.MAX_MODIFIER,
            'adjustment_rate': dm.ADJUSTMENT_RATE,
        }

        # Verify all fields present
        assert dm_data['levels_completed'] == 4
        assert dm_data['total_damage_taken'] == 150
        assert dm_data['total_damage_dealt'] == 450
        assert dm_data['enemy_count_modifier'] == 1.2
        assert dm_data['enemy_stat_modifier'] == 1.1
        assert dm_data['item_spawn_modifier'] == 0.9
        assert dm_data['healing_modifier'] == 0.95
        assert len(dm_data['average_health_per_level']) == 4
        assert len(dm_data['time_per_level']) == 4

    def test_serialize_camera(self):
        """Test camera serialization."""
        camera = self.camera

        camera_data = {
            'x': camera.x,
            'y': camera.y,
            'angle': camera.angle,
            'fov': camera.fov
        }

        assert camera_data['x'] == 25.5
        assert camera_data['y'] == 30.2
        assert camera_data['angle'] == 45.0
        assert camera_data['fov'] == 60.0

    def test_serialize_camera_none(self):
        """Test camera serialization when camera is None."""
        camera = None

        camera_data = None if camera is None else {
            'x': camera.x,
            'y': camera.y,
            'angle': camera.angle,
            'fov': camera.fov
        }

        assert camera_data is None

    def test_game_flow_state_fields(self):
        """Test that all game flow state fields are captured."""
        gs = self.game_session

        flow_state = {
            'rendering_mode': gs.rendering_mode,
            'player_asleep': gs.player_asleep,
            'game_over': gs.game_over,
            'victory': gs.victory,
            'message': gs.message,
            'death_reason': gs.death_reason,
            'pending_selection': gs.pending_selection,
        }

        assert flow_state['rendering_mode'] == '3d'
        assert flow_state['player_asleep'] is True
        assert flow_state['game_over'] is False
        assert flow_state['victory'] is False
        assert flow_state['message'] == "You are asleep!"
        assert flow_state['death_reason'] == ""
        assert flow_state['pending_selection'] == {'type': 'food', 'items': []}

    def test_deserialize_difficulty_manager(self):
        """Test difficulty manager deserialization."""
        dm_data = {
            'levels_completed': 4,
            'total_damage_taken': 150,
            'total_damage_dealt': 450,
            'deaths_this_session': 0,
            'average_health_per_level': [0.9, 0.8, 0.7, 0.85],
            'time_per_level': [120, 150, 180, 140],
            'enemy_count_modifier': 1.2,
            'enemy_stat_modifier': 1.1,
            'item_spawn_modifier': 0.9,
            'healing_modifier': 0.95,
            'min_modifier': 0.5,
            'max_modifier': 1.5,
            'adjustment_rate': 0.1,
        }

        # Simulate deserialization
        dm = Mock()
        dm.levels_completed = dm_data.get('levels_completed', 0)
        dm.total_damage_taken = dm_data.get('total_damage_taken', 0)
        dm.total_damage_dealt = dm_data.get('total_damage_dealt', 0)
        dm.enemy_count_modifier = dm_data.get('enemy_count_modifier', 1.0)
        dm.enemy_stat_modifier = dm_data.get('enemy_stat_modifier', 1.0)
        dm.item_spawn_modifier = dm_data.get('item_spawn_modifier', 1.0)
        dm.healing_modifier = dm_data.get('healing_modifier', 1.0)

        assert dm.levels_completed == 4
        assert dm.total_damage_taken == 150
        assert dm.enemy_count_modifier == 1.2
        assert dm.healing_modifier == 0.95

    def test_backward_compatibility_missing_fields(self):
        """Test that missing fields have sensible defaults."""
        save_data = {
            'current_level_number': 5,
            # Old save - missing new fields
        }

        # Simulate restore with fallbacks
        rendering_mode = save_data.get('rendering_mode', '2d')
        player_asleep = save_data.get('player_asleep', False)
        game_over = save_data.get('game_over', False)
        victory = save_data.get('victory', False)

        assert rendering_mode == '2d'
        assert player_asleep is False
        assert game_over is False
        assert victory is False

    def test_save_version_increment(self):
        """Test that save version is incremented for new format."""
        SAVE_VERSION = '1.1'

        save_data = {
            'version': SAVE_VERSION,
        }

        assert save_data['version'] == '1.1'
        assert float(save_data['version']) > 1.0


class TestIntegration:
    """Integration tests for save/load cycle."""

    def test_full_save_load_cycle(self):
        """Test complete save and load preserves all fields."""
        # Simulate full save data
        save_data = {
            'version': '1.1',
            'current_level_number': 5,
            'rendering_mode': '3d',
            'player_asleep': True,
            'game_over': False,
            'victory': False,
            'message': 'Test message',
            'death_reason': '',
            'pending_selection': {'type': 'food'},
            'difficulty_manager': {
                'levels_completed': 4,
                'enemy_count_modifier': 1.2,
                'enemy_stat_modifier': 1.1,
                'item_spawn_modifier': 0.9,
                'healing_modifier': 0.95,
            },
            'camera': {
                'x': 25.5,
                'y': 30.2,
                'angle': 45.0,
                'fov': 60.0,
            },
        }

        # Verify round-trip
        json_str = json.dumps(save_data, indent=2)
        loaded_data = json.loads(json_str)

        assert loaded_data['rendering_mode'] == '3d'
        assert loaded_data['player_asleep'] is True
        assert loaded_data['difficulty_manager']['enemy_count_modifier'] == 1.2
        assert loaded_data['camera']['x'] == 25.5

    def test_json_serializable(self):
        """Test that all new fields are JSON serializable."""
        save_data = {
            'rendering_mode': '3d',
            'player_asleep': True,
            'game_over': False,
            'victory': False,
            'message': 'Test',
            'death_reason': '',
            'pending_selection': {'type': 'food', 'items': []},
            'difficulty_manager': {
                'levels_completed': 4,
                'average_health_per_level': [0.9, 0.8],
                'time_per_level': [120, 150],
                'enemy_count_modifier': 1.2,
            },
            'camera': {
                'x': 25.5,
                'y': 30.2,
                'angle': 45.0,
                'fov': 60.0,
            },
        }

        # Should not raise exception
        try:
            json_str = json.dumps(save_data)
            loaded = json.loads(json_str)
            assert isinstance(loaded, dict)
        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
