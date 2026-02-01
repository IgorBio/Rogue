"""
View manager for presentation-layer view creation and management.

This module handles creation and lifecycle of presentation objects
like Camera and CameraController, keeping domain layer decoupled
from presentation concerns.

The ViewManager subscribes to domain events and creates/updates
views accordingly, implementing the observer pattern for layer
decoupling.

Usage:
    from presentation.view_manager import ViewManager
    from domain.event_bus import event_bus
    
    # Create view manager (registers event subscribers)
    view_manager = ViewManager()
    
    # Access created views
    if view_manager.camera:
        view_manager.sync_camera_to_character(character)
"""

from typing import Optional, Tuple, Any
from domain.events import LevelGeneratedEvent, CharacterMovedEvent
from domain.event_bus import event_bus
from config.game_config import GameConfig


class ViewManager:
    """
    Manages presentation-layer views (Camera, CameraController).
    
    This class is responsible for:
    - Creating Camera instances when levels are generated
    - Creating CameraController instances for 3D navigation
    - Synchronizing camera position with character position
    - Managing view lifecycle
    
    Attributes:
        camera: The current Camera instance (or None if not in 3D mode)
        camera_controller: The current CameraController instance
        _level: Reference to current level for controller creation
    
    Example:
        view_manager = ViewManager()
        # Camera is created automatically on LevelGeneratedEvent
        # Or manually:
        view_manager.create_camera_for_level(level, character, mode='3d')
    """
    
    def __init__(self, auto_subscribe: bool = True):
        """
        Initialize the view manager.
        
        Args:
            auto_subscribe: If True (default), automatically subscribe to
                           domain events. Set to False for manual control.
        """
        self.camera: Optional[Any] = None
        self.camera_controller: Optional[Any] = None
        self._level: Optional[Any] = None
        self._camera_factory: Optional[callable] = None
        self._camera_controller_factory: Optional[callable] = None
        
        if auto_subscribe:
            self._subscribe_to_events()
    
    def _subscribe_to_events(self) -> None:
        """Subscribe to domain events for automatic view management."""
        event_bus.subscribe(LevelGeneratedEvent, self._on_level_generated)
        event_bus.subscribe(CharacterMovedEvent, self._on_character_moved)
    
    def unsubscribe(self) -> None:
        """Unsubscribe from all events. Call before disposal."""
        event_bus.unsubscribe(LevelGeneratedEvent, self._on_level_generated)
        event_bus.unsubscribe(CharacterMovedEvent, self._on_character_moved)
    
    def set_factories(self, camera_factory: callable, 
                     camera_controller_factory: callable) -> None:
        """
        Set the factories for creating camera and controller.
        
        Args:
            camera_factory: Factory function for creating Camera instances
            camera_controller_factory: Factory function for creating 
                                      CameraController instances
        """
        self._camera_factory = camera_factory
        self._camera_controller_factory = camera_controller_factory
    
    def _on_level_generated(self, event: LevelGeneratedEvent) -> None:
        """
        Handler for LevelGeneratedEvent - creates camera for new level.
        
        Args:
            event: The level generated event containing level and position info
        """
        self._level = event.level
        char_x, char_y = event.character_position
        
        # Create camera at character position with center offset
        self._create_camera(char_x + 0.5, char_y + 0.5)
        
        # Create controller if camera was created successfully
        if self.camera is not None and self._camera_controller_factory:
            self._create_controller()
    
    def _on_character_moved(self, event: CharacterMovedEvent) -> None:
        """
        Handler for CharacterMovedEvent - syncs camera to character.
        
        Args:
            event: The character moved event with from/to positions
        """
        if self.camera is not None:
            to_x, to_y = event.to_position
            self.sync_camera_to_position(to_x + 0.5, to_y + 0.5)
    
    def _create_camera(self, x: float, y: float) -> None:
        """
        Create camera using the injected factory.
        
        Args:
            x: Camera X position (float for grid center)
            y: Camera Y position (float for grid center)
        """
        if self._camera_factory is None:
            self.camera = None
            return
        
        try:
            self.camera = self._camera_factory(
                x,
                y,
                angle=GameConfig.DEFAULT_CAMERA_ANGLE,
                fov=GameConfig.DEFAULT_CAMERA_FOV,
            )
        except Exception:
            self.camera = None
    
    def _create_controller(self) -> None:
        """Create camera controller using the injected factory."""
        if self._camera_controller_factory is None or self.camera is None:
            self.camera_controller = None
            return
        
        try:
            self.camera_controller = self._camera_controller_factory(
                self.camera, self._level
            )
        except Exception:
            self.camera_controller = None
    
    def create_camera_for_level(self, level: Any, character: Any, 
                                mode: str = '2d') -> Tuple[Optional[Any], Optional[Any]]:
        """
        Manually create camera and controller for a level.
        
        This is an alternative to event-based creation for manual control.
        
        Args:
            level: The Level instance
            character: The Character instance (for starting position)
            mode: View mode - '2d' or '3d' (camera only needed for 3d)
        
        Returns:
            Tuple of (camera, camera_controller) - either may be None
        
        Example:
            camera, controller = view_manager.create_camera_for_level(
                level, character, mode='3d'
            )
        """
        if mode != '3d' or self._camera_factory is None:
            self.camera = None
            self.camera_controller = None
            return None, None
        
        self._level = level
        
        # Get starting position from character
        char_x, char_y = character.position
        
        # Create camera centered on character's grid cell
        self._create_camera(char_x + 0.5, char_y + 0.5)
        
        # Create controller if camera was created
        if self.camera is not None:
            self._create_controller()
        
        return self.camera, self.camera_controller
    
    def sync_camera_to_position(self, x: float, y: float, 
                                preserve_angle: bool = True) -> None:
        """
        Synchronize camera position to given coordinates.
        
        Args:
            x: Target X position (float, typically character.x + 0.5)
            y: Target Y position (float, typically character.y + 0.5)
            preserve_angle: Whether to preserve current camera angle
        """
        if self.camera is None:
            return
        
        try:
            if preserve_angle:
                old_angle = getattr(self.camera, 'angle', 0)
                self.camera.set_position(x, y)
                self.camera.angle = old_angle
            else:
                self.camera.set_position(x, y)
        except Exception:
            pass
    
    def sync_camera_to_character(self, character: Any, 
                                 preserve_angle: bool = True) -> None:
        """
        Synchronize camera position to character position.
        
        Places camera at the center of the character's grid cell.
        
        Args:
            character: The Character instance to sync to
            preserve_angle: Whether to preserve current camera angle
        
        Example:
            Character at (10, 20) → Camera at (10.5, 20.5)
        """
        char_x, char_y = character.position
        self.sync_camera_to_position(
            char_x + 0.5, char_y + 0.5, preserve_angle
        )
    
    def reset(self) -> None:
        """Reset views to None (e.g., on game reset)."""
        self.camera = None
        self.camera_controller = None
        self._level = None


# Global view manager instance for application-wide use
view_manager = ViewManager()


def reset_view_manager() -> None:
    """Reset the global view manager to initial state."""
    view_manager.reset()
