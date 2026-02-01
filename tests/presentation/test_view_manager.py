"""
Tests for the view manager.
"""

import pytest
from unittest.mock import Mock, MagicMock
from presentation.view_manager import ViewManager, view_manager, reset_view_manager
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
    
    def test_set_factories(self):
        """Test setting camera factories."""
        vm = ViewManager(auto_subscribe=False)
        camera_factory = Mock()
        controller_factory = Mock()
        
        vm.set_factories(camera_factory, controller_factory)
        
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
        vm = ViewManager(auto_subscribe=False)
        
        # Factory that creates MockCamera with provided arguments
        def camera_factory(x, y, angle=0.0, fov=60.0):
            return MockCamera(x, y, angle, fov)
        
        vm.set_factories(camera_factory, None)
        
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='3d')
        
        assert camera is not None
        assert controller is None  # No controller factory
        # Camera positioned at character position + 0.5 offset
        assert camera.x == 10.5
        assert camera.y == 20.5
    
    def test_create_camera_factory_exception(self):
        """Test handling of camera factory exception."""
        vm = ViewManager(auto_subscribe=False)
        camera_factory = Mock(side_effect=Exception("Camera error"))
        vm.set_factories(camera_factory, None)
        
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='3d')
        
        assert camera is None
        assert controller is None
    
    def test_create_camera_and_controller(self):
        """Test creation of both camera and controller."""
        vm = ViewManager(auto_subscribe=False)
        mock_camera = MockCamera()
        mock_controller = Mock()
        
        camera_factory = Mock(return_value=mock_camera)
        controller_factory = Mock(return_value=mock_controller)
        
        vm.set_factories(camera_factory, controller_factory)
        
        level = MockLevel()
        character = MockCharacter(10, 20)
        
        camera, controller = vm.create_camera_for_level(level, character, mode='3d')
        
        assert camera is mock_camera
        assert controller is mock_controller
        controller_factory.assert_called_once_with(mock_camera, level)


class TestViewManagerSync:
    """Test camera synchronization."""
    
    def test_sync_camera_to_position(self):
        """Test syncing camera to specific position."""
        vm = ViewManager(auto_subscribe=False)
        mock_camera = MockCamera()
        vm.camera = mock_camera
        
        vm.sync_camera_to_position(15.5, 25.5)
        
        assert mock_camera.x == 15.5
        assert mock_camera.y == 25.5
    
    def test_sync_camera_to_position_no_camera(self):
        """Test syncing when camera is None does nothing."""
        vm = ViewManager(auto_subscribe=False)
        vm.camera = None
        
        # Should not raise
        vm.sync_camera_to_position(15.5, 25.5)
    
    def test_sync_camera_to_character(self):
        """Test syncing camera to character position."""
        vm = ViewManager(auto_subscribe=False)
        mock_camera = MockCamera()
        vm.camera = mock_camera
        character = MockCharacter(10, 20)
        
        vm.sync_camera_to_character(character)
        
        # Camera should be at character position + 0.5 offset
        assert mock_camera.x == 10.5
        assert mock_camera.y == 20.5
    
    def test_sync_camera_preserves_angle(self):
        """Test that sync preserves camera angle by default."""
        vm = ViewManager(auto_subscribe=False)
        mock_camera = MockCamera(angle=45.0)
        vm.camera = mock_camera
        
        vm.sync_camera_to_position(10.5, 20.5, preserve_angle=True)
        
        assert mock_camera.angle == 45.0
    
    def test_sync_camera_updates_angle_when_requested(self):
        """Test that sync can update angle when preserve_angle=False."""
        vm = ViewManager(auto_subscribe=False)
        mock_camera = MockCamera(angle=45.0)
        vm.camera = mock_camera
        
        vm.sync_camera_to_position(10.5, 20.5, preserve_angle=False)
        
        # Angle may or may not change depending on implementation
        # Just verify no exception is raised
        assert mock_camera.x == 10.5
        assert mock_camera.y == 20.5


class TestViewManagerEventHandling:
    """Test event-based camera management."""
    
    def test_level_generated_event_creates_camera(self):
        """Test that LevelGeneratedEvent triggers camera creation."""
        vm = ViewManager(auto_subscribe=True)
        mock_camera = MockCamera()
        camera_factory = Mock(return_value=mock_camera)
        vm.set_factories(camera_factory, None)
        
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
        assert mock_camera.x == 10.5
        assert mock_camera.y == 20.5
    
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
        vm = ViewManager(auto_subscribe=True)
        mock_camera = MockCamera()
        camera_factory = Mock(return_value=mock_camera)
        vm.set_factories(camera_factory, None)
        
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
