"""
View Manager for presentation layer.

Manages Camera and CameraController lifecycle for the presentation layer.
Can operate in event-driven mode (subscribing to EventBus) or manual mode.

Usage:
    from presentation.view_manager import ViewManager, view_manager
    from presentation.camera import Camera
    from presentation.camera import CameraController
    
    # Create view manager manually
    vm = ViewManager(auto_subscribe=False)
    vm.set_factories(
        camera_factory=lambda x, y, angle, fov: Camera(x, y, angle=angle, fov=fov),
        camera_controller_factory=lambda cam, lvl: CameraController(cam, lvl)
    )
    
    # Or use event-driven mode
    vm = ViewManager(auto_subscribe=True)
    vm.set_factories(camera_factory, controller_factory)
    # Camera will be created automatically when LevelGeneratedEvent is published
    
    # Access camera and controller
    camera = vm.camera
    controller = vm.camera_controller
"""

from typing import Any, Optional, Callable, Tuple
from domain.event_bus import event_bus
from domain.events import (
    LevelGeneratedEvent,
    CharacterMovedEvent,
)
from presentation.camera_sync import camera_sync
from config.game_config import GameConfig


class ViewManager:
    """
    Manages Camera and CameraController for 3D rendering mode.
    
    Can operate in two modes:
    1. Manual mode (auto_subscribe=False): You create camera manually
    2. Event-driven mode (auto_subscribe=True): Camera created via events
    
    Attributes:
        camera: Camera instance for 3D rendering ( public attribute)
        camera_controller: CameraController for 3D movement (public attribute)
        _camera_factory: Factory function to create Camera
        _camera_controller_factory: Factory function to create CameraController
        _level: Current level reference
        _subscribed: Whether event subscriptions are active
    """
    
    def __init__(self, auto_subscribe: bool = False):
        """
        Initialize ViewManager.
        
        Args:
            auto_subscribe: If True, automatically subscribe to domain events
        """
        self.camera: Optional[Any] = None
        self.camera_controller: Optional[Any] = None
        self._camera_factory: Optional[Callable] = None
        self._camera_controller_factory: Optional[Callable] = None
        self._level: Optional[Any] = None
        self._subscribed = False
        
        if auto_subscribe:
            self.subscribe()
    
    def set_factories(
        self,
        camera_factory: Optional[Callable] = None,
        camera_controller_factory: Optional[Callable] = None
    ) -> None:
        """
        Set camera and controller factories.
        
        Args:
            camera_factory: Callable that creates Camera (x, y, angle, fov)
            camera_controller_factory: Callable that creates CameraController (camera, level)
        """
        self._camera_factory = camera_factory
        self._camera_controller_factory = camera_controller_factory
    
    def subscribe(self) -> None:
        """Subscribe to domain events for camera management."""
        if self._subscribed:
            return
        
        event_bus.subscribe(LevelGeneratedEvent, self._on_level_generated)
        event_bus.subscribe(CharacterMovedEvent, self._on_character_moved)
        self._subscribed = True
    
    def unsubscribe(self) -> None:
        """Unsubscribe from domain events."""
        if not self._subscribed:
            return
        
        event_bus.unsubscribe(LevelGeneratedEvent, self._on_level_generated)
        event_bus.unsubscribe(CharacterMovedEvent, self._on_character_moved)
        self._subscribed = False
    
    def _on_level_generated(self, event: LevelGeneratedEvent) -> None:
        """
        Handle level generation event.
        
        Creates camera at character starting position if factories are set.
        
        Args:
            event: LevelGeneratedEvent with level and character_position
        """
        self._level = event.level
        
        if self._camera_factory is None:
            return
        
        start_x, start_y = event.character_position
        
        try:
            # Create camera at center of starting cell
            self.camera = self._camera_factory(
                start_x + 0.5,
                start_y + 0.5,
                GameConfig.DEFAULT_CAMERA_ANGLE,
                GameConfig.DEFAULT_CAMERA_FOV,
            )
        except Exception:
            self.camera = None
            self.camera_controller = None
            return
        
        # Create camera controller if factory provided
        if self._camera_controller_factory is not None and self.camera is not None:
            try:
                self.camera_controller = self._camera_controller_factory(
                    self.camera, 
                    event.level
                )
            except Exception:
                self.camera_controller = None
    
    def _on_character_moved(self, event: CharacterMovedEvent) -> None:
        """
        Handle character movement event.
        
        Syncs camera position to new character position in 3D mode.
        
        Args:
            event: CharacterMovedEvent with from_position and to_position
        """
        if self.camera is None:
            return
        
        # Sync camera to new position
        to_x, to_y = event.to_position
        self.sync_camera_to_character_coords(to_x, to_y)
    
    def create_camera_for_level(
        self, 
        level: Any, 
        character: Any, 
        mode: str = '3d'
    ) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Create camera and controller for a level.
        
        Args:
            level: Level instance
            character: Character instance (used for position)
            mode: '2d' or '3d' mode
        
        Returns:
            Tuple of (camera, camera_controller) - may be None
        """
        if mode == '2d':
            return None, None
        
        if self._camera_factory is None:
            return None, None
        
        char_x, char_y = character.position
        
        try:
            self.camera = self._camera_factory(
                char_x + 0.5,
                char_y + 0.5,
                GameConfig.DEFAULT_CAMERA_ANGLE,
                GameConfig.DEFAULT_CAMERA_FOV,
            )
        except Exception:
            self.camera = None
            self.camera_controller = None
            return None, None
        
        if self._camera_controller_factory is not None:
            try:
                self.camera_controller = self._camera_controller_factory(self.camera, level)
            except Exception:
                self.camera_controller = None
        
        self._level = level
        return self.camera, self.camera_controller
    
    def sync_camera_to_position(
        self, 
        x: float, 
        y: float, 
        preserve_angle: bool = True
    ) -> None:
        """
        Sync camera to specific world coordinates.
        
        Args:
            x: World X coordinate
            y: World Y coordinate
            preserve_angle: Whether to preserve camera angle
        """
        if self.camera is None:
            return
        
        if preserve_angle:
            old_angle = getattr(self.camera, 'angle', 0)
            self.camera.set_position(x, y)
            self.camera.angle = old_angle
        else:
            self.camera.set_position(x, y)
    
    def sync_camera_to_character_coords(self, x: int, y: int, preserve_angle: bool = True) -> None:
        """
        Sync camera to character grid coordinates.
        
        Args:
            x: Grid X coordinate
            y: Grid Y coordinate
            preserve_angle: Whether to preserve camera angle
        """
        if self.camera is None:
            return
        
        camera_sync.sync_camera_to_coords(self.camera, x, y, preserve_angle)
    
    def sync_camera_to_character(self, character: Any, preserve_angle: bool = True) -> None:
        """
        Sync camera to character position.
        
        Args:
            character: Character instance
            preserve_angle: Whether to preserve camera angle
        """
        if self.camera is None:
            return
        
        camera_sync.sync_camera_to_character(self.camera, character, preserve_angle)
    
    def get_camera_grid_position(self) -> Optional[Tuple[int, int]]:
        """
        Get camera position as grid coordinates.
        
        Returns:
            Tuple of (x, y) grid coordinates or None if no camera
        """
        if self.camera is None:
            return None
        
        return camera_sync.get_camera_grid_position(self.camera)
    
    def reset(self) -> None:
        """Reset camera, controller and level."""
        self.camera = None
        self.camera_controller = None
        self._level = None


# Global instance for application-wide use
view_manager = ViewManager()


def reset_view_manager() -> None:
    """
    Reset the global view manager.
    
    Useful for testing to ensure clean state between tests.
    """
    view_manager.camera = None
    view_manager.camera_controller = None
    view_manager._level = None
    view_manager._camera_factory = None
    view_manager._camera_controller_factory = None


def create_view_manager(
    camera_factory: Optional[Callable] = None,
    camera_controller_factory: Optional[Callable] = None
) -> ViewManager:
    """
    Factory function to create and configure a ViewManager.
    
    Args:
        camera_factory: Factory for creating Camera instances
        camera_controller_factory: Factory for creating CameraController instances
    
    Returns:
        Configured ViewManager instance with event subscriptions
    """
    vm = ViewManager(auto_subscribe=True)
    vm.set_factories(camera_factory, camera_controller_factory)
    return vm
