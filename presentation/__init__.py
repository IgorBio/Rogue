"""
Presentation Layer - User Interface and Rendering.

This package handles all visual presentation and user input:
- 2D and 3D rendering using the curses library
- Keyboard input processing and action mapping
- Color scheme management for terminal display
- UI components (menus, status panels, message logs)

The presentation layer communicates with the domain layer
through well-defined interfaces, maintaining separation of concerns.
"""

from presentation.renderer import Renderer
from presentation.input_handler import InputHandler
from presentation.colors import init_colors
from presentation.game_ui import GameUI

__all__ = [
    'Renderer',
    'InputHandler',
    'init_colors',
    'GameUI',
]