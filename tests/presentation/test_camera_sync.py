"""
Tests for CameraSync presentation layer component.
"""

import pytest
from unittest.mock import Mock
from presentation.camera.sync import CameraSync, camera_sync
from domain.entities.position import Position
from config.game_config import CameraConfig


class MockCamera:
    """Mock camera for testing."""
    def __init__(self, x=0.0, y=0.0, angle=0.0):
        self.x = x
        self.y = y
        self.angle = angle
    
    def set_position(self, x, y):
        self.x = x
        self.y = y


class MockCharacter:
    """Mock character for testing."""
    def __init__(self, x=0, y=0):
        self._position = (x, y)
    
    @property
    def position(self):
        return self._position
    
    def move_to(self, x, y):
        self._position = (x, y)


class TestCameraSyncBasic:
    """Test basic CameraSync functionality."""
    
    def test_init_default_offset(self):
        """Test default center offset."""
        sync = CameraSync()
        assert sync.center_offset == CameraConfig.CAMERA_OFFSET
    
    def test_init_custom_offset(self):
        """Test custom center offset."""
        sync = CameraSync(center_offset=0.3)
        assert sync.center_offset == 0.3
    
    def test_init_tracking_none(self):
        """Test that last position is None initially."""
        sync = CameraSync()
        assert sync._last_position is None


class TestCameraSyncToPosition:
    """Test sync_camera_to_position method."""
    
    def test_sync_to_position_default_offset(self):
        """Test syncing camera to position with default offset."""
        sync = CameraSync()
        camera = MockCamera()
        position = Position(10, 20)
        
        sync.sync_camera_to_position(camera, position)
        
        assert camera.x == 10 + CameraConfig.CAMERA_OFFSET
        assert camera.y == 20 + CameraConfig.CAMERA_OFFSET
    
    def test_sync_to_position_custom_offset(self):
        """Test syncing camera to position with custom offset."""
        sync = CameraSync(center_offset=0.3)
        camera = MockCamera()
        position = Position(10, 20)
        
        sync.sync_camera_to_position(camera, position)
        
        assert camera.x == 10.3
        assert camera.y == 20.3
    
    def test_sync_preserves_angle(self):
        """Test that sync preserves camera angle."""
        sync = CameraSync()
        camera = MockCamera(angle=45.0)
        position = Position(10, 20)
        
        sync.sync_camera_to_position(camera, position, preserve_angle=True)
        
        assert camera.angle == 45.0
    
    def test_sync_can_update_angle(self):
        """Test that sync can update angle."""
        sync = CameraSync()
        camera = MockCamera(angle=45.0)
        position = Position(10, 20)
        
        sync.sync_camera_to_position(camera, position, preserve_angle=False)
        
        # Position updated, angle may change or stay
        assert camera.x == 10 + CameraConfig.CAMERA_OFFSET
        assert camera.y == 20 + CameraConfig.CAMERA_OFFSET


class TestCameraSyncToCharacter:
    """Test sync_camera_to_character method."""
    
    def test_sync_to_character(self):
        """Test syncing camera to character."""
        sync = CameraSync()
        camera = MockCamera()
        character = MockCharacter(10, 20)
        
        sync.sync_camera_to_character(camera, character)
        
        assert camera.x == 10 + CameraConfig.CAMERA_OFFSET
        assert camera.y == 20 + CameraConfig.CAMERA_OFFSET


class TestCameraSyncFromCamera:
    """Test sync_character_from_camera method."""
    
    def test_sync_from_camera_floor_mode(self):
        """Test syncing character from camera with floor mode."""
        sync = CameraSync()
        camera = MockCamera(10.7, 20.3)
        character = MockCharacter(0, 0)
        
        sync.sync_character_from_camera(character, camera, snap_mode='floor')
        
        assert character.position == (10, 20)
    
    def test_sync_from_camera_round_mode(self):
        """Test syncing character from camera with round mode."""
        sync = CameraSync()
        camera = MockCamera(10.7, 20.3)
        character = MockCharacter(0, 0)
        
        sync.sync_character_from_camera(character, camera, snap_mode='round')
        
        assert character.position == (11, 20)


class TestCameraSyncGetGridPosition:
    """Test get_camera_grid_position method."""
    
    def test_get_grid_position_floor(self):
        """Test getting grid position from camera."""
        sync = CameraSync()
        camera = MockCamera(10.7, 20.3)
        
        grid_pos = sync.get_camera_grid_position(camera)
        
        assert grid_pos == (10, 20)


class TestCameraSyncIsAtPosition:
    """Test is_camera_at_position method."""
    
    def test_is_at_position_true(self):
        """Test when camera is at expected position."""
        sync = CameraSync()
        camera = MockCamera(10 + CameraConfig.CAMERA_OFFSET, 20 + CameraConfig.CAMERA_OFFSET)  # Center of (10, 20)
        position = Position(10, 20)
        
        result = sync.is_camera_at_position(camera, position)
        
        assert result is True
    
    def test_is_at_position_false(self):
        """Test when camera is not at expected position."""
        sync = CameraSync()
        camera = MockCamera(10 + CameraConfig.CAMERA_OFFSET, 20.7)  # Different Y offset
        position = Position(10, 20)
        
        result = sync.is_camera_at_position(camera, position)
        
        assert result is False
    
    def test_is_at_position_with_tolerance(self):
        """Test with custom tolerance."""
        sync = CameraSync()
        camera = MockCamera(10.6, 20.6)  # Slightly off
        position = Position(10, 20)
        
        result = sync.is_camera_at_position(camera, position, tolerance=0.2)
        
        assert result is True


class TestCameraSyncCalculateOffset:
    """Test calculate_offset method."""
    
    def test_calculate_offset(self):
        """Test calculating offset between camera and position."""
        sync = CameraSync()
        camera = MockCamera(10.7, 20.8)
        position = Position(10, 20)
        
        offset_x, offset_y = sync.calculate_offset(camera, position)
        
        # Expected: camera_pos - (position + offset)
        assert offset_x == pytest.approx(10.7 - (10 + CameraConfig.CAMERA_OFFSET))
        assert offset_y == pytest.approx(20.8 - (20 + CameraConfig.CAMERA_OFFSET))


class TestCameraSyncReset:
    """Test reset method."""
    
    def test_reset_clears_tracking(self):
        """Test that reset clears tracking."""
        sync = CameraSync()
        camera = MockCamera()
        position = Position(10, 20)
        
        sync.sync_camera_to_position(camera, position)
        assert sync._last_position is not None
        
        sync.reset()
        assert sync._last_position is None


class TestGlobalCameraSync:
    """Test global camera_sync instance."""
    
    def test_global_instance_exists(self):
        """Test that global instance exists."""
        assert camera_sync is not None
        assert isinstance(camera_sync, CameraSync)
