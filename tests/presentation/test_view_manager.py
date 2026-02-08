"""
Tests for the view manager.
"""

import pytest
from unittest.mock import Mock, MagicMock
from presentation.view_manager import ViewManager, view_manager, reset_view_manager
from config.game_config import CameraConfig
from domain.events import LevelGeneratedEvent, CharacterMovedEvent
from domain.event_bus import event_bus, reset_event_bus


class MockCamera:
    """Mock camera for testing."""
    def __init__(self, x=0.0, y=0.0, angle=0.0, fov=60.0):
        self.x = float(x)
        self.y = float(y)
        self.angle = angle
        self.fov = fov
    
    def set_position(self, x, y):
        self.x = float(x)
        self.y = float(y)


class MockLevel:
    """Mock level for testing."""
    pass


class MockCharacter:
    """Mock character for testing."""
    def __init__(self, x=0, y=0):
        self._position = (x, y)
    
    @property
    def position(self):
        return self._position
    
    def move_to(self, x, y):
        self._position = (x, y)


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state before each test."""
    reset_event_bus()
    reset_view_manager()
    yield


class TestViewManagerBasic:
    """Test basic ViewManager functionality."""
    
    def test_init_creates_empty_views(self):
        """Test that ViewManager initializes with None views."""
        vm = ViewManager(auto_subscribe=False)
        assert vm.camera is None
        assert vm.camera_controller is None
    
    def test_init_factories(self):
        """Test initializing camera factories."""
        camera_factory = Mock()
        controller_factory = Mock()
        vm = ViewManager(
            auto_subscribe=False,
            camera_factory=camera_factory,
            camera_controller_factory=controller_factory
        )
        
        assert vm._camera_factory is camera_factory
        assert vm._camera_controller_factory is controller_factory


class TestViewManagerCameraCreation:
    """Test camera creation functionality."""
    
    def test_create_camera_for_level_2d_mode(self):
        """Test camera creation in 2D mode returns None."""
        vm = ViewManager(auto_subscribe=False)
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='2d')
        
        assert camera is None
        assert controller is None
    
    def test_create_camera_for_level_3d_no_factory(self):
        """Test camera creation without factory returns None."""
        vm = ViewManager(auto_subscribe=False)
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='3d')
        
        assert camera is None
        assert controller is None
    
    def test_create_camera_for_level_3d_with_factory(self):
        """Test camera creation with factory."""
        # Factory that creates MockCamera with provided arguments
        def camera_factory(x, y, angle=0.0, fov=60.0):
            return MockCamera(x, y, angle, fov)
        
        vm = ViewManager(
            auto_subscribe=False,
            camera_factory=camera_factory,
            camera_controller_factory=None
        )
        
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='3d')
        
        assert camera is not None
        assert controller is None  # No controller factory
        # Camera positioned at character position + offset
        assert camera.x == 10 + CameraConfig.CAMERA_OFFSET
        assert camera.y == 20 + CameraConfig.CAMERA_OFFSET
    
    def test_create_camera_factory_exception(self):
        """Test handling of camera factory exception."""
        camera_factory = Mock(side_effect=Exception("Camera error"))
        vm = ViewManager(
            auto_subscribe=False,
            camera_factory=camera_factory,
            camera_controller_factory=None
        )
        
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='3d')
        
        assert camera is None
        assert controller is None
    
    def test_create_camera_and_controller(self):
        """Test creation of both camera and controller."""
        mock_camera = MockCamera()
        mock_controller = Mock()
        
        camera_factory = Mock(return_value=mock_camera)
        controller_factory = Mock(return_value=mock_controller)
        
        vm = ViewManager(
            auto_subscribe=False,
            camera_factory=camera_factory,
            camera_controller_factory=controller_factory
        )
        
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='3d')
        
        assert camera is mock_camera
        assert controller is mock_controller
        controller_factory.assert_called_once_with(mock_camera, level)


class TestViewManagerSync:
    """Test camera synchronization."""
    
    def test_sync_camera_to_character(self):
        """Test syncing camera to character position."""
        vm = ViewManager(auto_subscribe=False)
        mock_camera = MockCamera()
        vm.camera = mock_camera
        character = MockCharacter(10, 20)
        
        vm.sync_camera_to_character(character)
        
        # Camera should be at character position + offset
        assert mock_camera.x == 10 + CameraConfig.CAMERA_OFFSET
        assert mock_camera.y == 20 + CameraConfig.CAMERA_OFFSET

    def test_sync_camera_to_character_coords_preserves_angle(self):
        """Test syncing camera to grid coords preserves angle."""
        vm = ViewManager(auto_subscribe=False)
        mock_camera = MockCamera(angle=30.0)
        vm.camera = mock_camera

        vm.sync_camera_to_character_coords(10, 20, preserve_angle=True)

        assert mock_camera.x == 10 + CameraConfig.CAMERA_OFFSET
        assert mock_camera.y == 20 + CameraConfig.CAMERA_OFFSET
        assert mock_camera.angle == 30.0

    def test_sync_camera_to_character_coords_no_camera(self):
        """Test syncing grid coords when camera is None does nothing."""
        vm = ViewManager(auto_subscribe=False)
        vm.camera = None

        # Should not raise
        vm.sync_camera_to_character_coords(10, 20)


class TestViewManagerEventHandling:
    """Test event-based camera management."""
    
    def test_level_generated_event_creates_camera(self):
        """Test that LevelGeneratedEvent triggers camera creation."""
        mock_camera = MockCamera()
        camera_factory = Mock(return_value=mock_camera)
        vm = ViewManager(
            auto_subscribe=True,
            camera_factory=camera_factory,
            camera_controller_factory=None
        )
        
        level = MockLevel()
        event = LevelGeneratedEvent(
            level=level,
            character_position=(10, 20),
            level_number=1
        )
        event_bus.publish(event)
        
        assert vm.camera is mock_camera
        assert vm._level is level
    
    def test_character_moved_event_syncs_camera(self):
        """Test that CharacterMovedEvent triggers camera sync."""
        vm = ViewManager(auto_subscribe=True)
        mock_camera = MockCamera()
        vm.camera = mock_camera
        
        event = CharacterMovedEvent(
            from_position=(0, 0),
            to_position=(10, 20)
        )
        event_bus.publish(event)
        
        # Camera should be synced to new position + offset
        assert mock_camera.x == 10 + CameraConfig.CAMERA_OFFSET
        assert mock_camera.y == 20 + CameraConfig.CAMERA_OFFSET
    
    def test_character_moved_no_camera_does_nothing(self):
        """Test that CharacterMovedEvent does nothing if no camera."""
        vm = ViewManager(auto_subscribe=True)
        vm.camera = None
        
        event = CharacterMovedEvent(
            from_position=(0, 0),
            to_position=(10, 20)
        )
        # Should not raise
        event_bus.publish(event)


class TestViewManagerReset:
    """Test view manager reset functionality."""
    
    def test_reset_clears_views(self):
        """Test that reset clears camera and controller."""
        vm = ViewManager(auto_subscribe=False)
        vm.camera = MockCamera()
        vm.camera_controller = Mock()
        vm._level = MockLevel()
        
        vm.reset()
        
        assert vm.camera is None
        assert vm.camera_controller is None
        assert vm._level is None


class TestViewManagerGridPosition:
    """Test camera grid position helper."""

    def test_get_camera_grid_position_none(self):
        """Test grid position when no camera."""
        vm = ViewManager(auto_subscribe=False)
        vm.camera = None

        assert vm.get_camera_grid_position() is None

    def test_get_camera_grid_position(self):
        """Test grid position with camera."""
        vm = ViewManager(auto_subscribe=False)
        vm.camera = MockCamera(10.7, 20.3)

        assert vm.get_camera_grid_position() == (10, 20)


class TestViewManagerApplyCameraState:
    """Test apply_camera_state behavior."""

    def test_apply_camera_state_creates_camera_and_controller(self):
        """Test applying camera state creates camera and controller."""
        mock_camera = MockCamera()
        mock_controller = Mock()

        camera_factory = Mock(return_value=mock_camera)
        controller_factory = Mock(return_value=mock_controller)
        vm = ViewManager(
            auto_subscribe=False,
            camera_factory=camera_factory,
            camera_controller_factory=controller_factory
        )

        level = MockLevel()
        state = {"x": 5.5, "y": 6.5, "angle": 10.0, "fov": 70.0}

        vm.apply_camera_state(state, level)

        assert vm.camera is mock_camera
        assert vm.camera_controller is mock_controller
        camera_factory.assert_called_once_with(5.5, 6.5, 10.0, 70.0)
        controller_factory.assert_called_once_with(mock_camera, level)

    def test_apply_camera_state_no_factory(self):
        """Test applying camera state without factory does nothing."""
        vm = ViewManager(
            auto_subscribe=False,
            camera_factory=None,
            camera_controller_factory=None
        )

        level = MockLevel()
        state = {"x": 5.5, "y": 6.5, "angle": 10.0, "fov": 70.0}

        vm.apply_camera_state(state, level)

        assert vm.camera is None
        assert vm.camera_controller is None


class TestGlobalViewManager:
    """Test global view manager instance."""
    
    def test_global_view_manager_exists(self):
        """Test that global view manager exists."""
        assert view_manager is not None
        assert isinstance(view_manager, ViewManager)
    
    def test_reset_view_manager(self):
        """Test resetting the global view manager."""
        view_manager.camera = MockCamera()
        view_manager.camera_controller = Mock()
        
        reset_view_manager()
        
        assert view_manager.camera is None
        assert view_manager.camera_controller is None


class TestViewManagerUnsubscribe:
    """Test unsubscription from events."""
    
    def test_unsubscribe_stops_receiving_events(self):
        """Test that unsubscribe stops event handling."""
        mock_camera = MockCamera()
        camera_factory = Mock(return_value=mock_camera)
        vm = ViewManager(
            auto_subscribe=True,
            camera_factory=camera_factory,
            camera_controller_factory=None
        )
        
        # First event should create camera
        event1 = LevelGeneratedEvent(
            level=MockLevel(),
            character_position=(10, 20),
            level_number=1
        )
        event_bus.publish(event1)
        assert vm.camera is mock_camera
        
        # Reset and unsubscribe
        vm.camera = None
        vm.unsubscribe()
        
        # Second event should not create camera
        mock_camera2 = MockCamera()
        camera_factory.return_value = mock_camera2
        event2 = LevelGeneratedEvent(
            level=MockLevel(),
            character_position=(30, 40),
            level_number=2
        )
        event_bus.publish(event2)
        assert vm.camera is None  # Should not have been updated
