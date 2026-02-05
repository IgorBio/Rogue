"""
Tests for PositionSynchronizer (domain-only).
"""

import pytest
from domain.entities.character import Character
from domain.entities.position import Position
from domain.services.position_synchronizer import (
    PositionSynchronizer,
    PositionSyncValidator,
    quick_sync_character_to_camera_coords,
    quick_sync_camera_coords_to_position,
)


class TestPositionSynchronizerInit:
    def test_default_init(self):
        sync = PositionSynchronizer()
        assert sync.center_offset == 0.5
        assert sync._last_character_pos is None

    def test_custom_offset(self):
        sync = PositionSynchronizer(center_offset=0.25)
        assert sync.center_offset == 0.25


class TestCharacterSync:
    def test_sync_character_to_position(self):
        char = Character(0, 0)
        sync = PositionSynchronizer()
        sync.sync_character_to_position(char, Position(10, 20))
        assert char.position == (10, 20)
        assert sync._last_character_pos == (10, 20)

    def test_is_character_moved_initial(self):
        char = Character(5, 5)
        sync = PositionSynchronizer()
        assert sync.is_character_moved(char) is True

    def test_is_character_moved_after_sync(self):
        char = Character(5, 5)
        sync = PositionSynchronizer()
        sync.sync_character_to_position(char, Position(5, 5))
        assert sync.is_character_moved(char) is False

    def test_is_character_moved_after_move(self):
        char = Character(5, 5)
        sync = PositionSynchronizer()
        sync.sync_character_to_position(char, Position(5, 5))
        char.move_to(6, 7)
        assert sync.is_character_moved(char) is True


class TestAlignmentAndOffsets:
    def test_get_character_offset(self):
        char = Character(10, 20)
        sync = PositionSynchronizer()
        offset = sync.get_character_offset(char, (10.5, 20.7))
        assert offset == pytest.approx((0.5, 0.7))

    def test_are_positions_aligned_true(self):
        char = Character(10, 20)
        sync = PositionSynchronizer()
        assert sync.are_positions_aligned(char, (10.5, 20.5)) is True

    def test_are_positions_aligned_false(self):
        char = Character(10, 20)
        sync = PositionSynchronizer()
        assert sync.are_positions_aligned(char, (15.5, 25.5)) is False

    def test_reset_tracking(self):
        char = Character(10, 20)
        sync = PositionSynchronizer()
        sync.sync_character_to_position(char, Position(10, 20))
        sync.reset_tracking()
        assert sync._last_character_pos is None


class TestValidator:
    def test_validate_sync_synced(self):
        char = Character(10, 20)
        result = PositionSyncValidator.validate_sync(char, (10.5, 20.5))
        assert result['is_synced'] is True
        assert result['character_pos'] == (10, 20)
        assert result['camera_grid_pos'] == (10, 20)
        assert len(result['issues']) == 0

    def test_validate_sync_not_synced(self):
        char = Character(10, 20)
        result = PositionSyncValidator.validate_sync(char, (15.5, 25.5))
        assert result['is_synced'] is False
        assert result['character_pos'] == (10, 20)
        assert result['camera_grid_pos'] == (15, 25)
        assert len(result['issues']) > 0

    def test_validate_sync_large_offset(self):
        char = Character(10, 20)
        result = PositionSyncValidator.validate_sync(char, (15.5, 25.5))
        issues_str = ' '.join(result['issues'])
        assert 'offset' in issues_str.lower()

    def test_suggest_sync_direction_none(self):
        char = Character(10, 20)
        direction = PositionSyncValidator.suggest_sync_direction(char, (10.5, 20.5))
        assert direction == 'none'

    def test_suggest_sync_direction_camera_centered(self):
        char = Character(10, 20)
        direction = PositionSyncValidator.suggest_sync_direction(char, (15.5, 25.5))
        assert direction == 'camera_to_character'

    def test_suggest_sync_direction_default(self):
        char = Character(10, 20)
        direction = PositionSyncValidator.suggest_sync_direction(char, (15.2, 25.8))
        assert direction == 'character_to_camera'


class TestConvenienceFunctions:
    def test_quick_sync_character_to_camera_coords(self):
        char = Character(0, 0)
        quick_sync_character_to_camera_coords(char, (10.5, 20.5))
        assert char.position == (10, 20)

    def test_quick_sync_camera_coords_to_position(self):
        coords = quick_sync_camera_coords_to_position((10.5, 20.5))
        assert coords == (10.5, 20.5)
