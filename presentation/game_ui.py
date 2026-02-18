"""
Enhanced GameUI coordinator for 2D and 3D rendering.

This module coordinates all UI interactions for the game, providing
a unified interface for both 2D and 3D rendering modes. Acts as a
facade for the entire presentation layer.
"""
from common.logging_utils import log_exception
import curses
import math


class GameUI:
    """
    Coordinates all UI interactions for the game (2D and 3D).
    
    Encapsulates all curses-specific rendering logic and provides
    a clean interface for the game session to display content and
    receive player input.
    
    Attributes:
        stdscr: Curses standard screen object
        view_manager: ViewManager for camera/controller access
        renderer_2d: Renderer instance for 2D mode
        input_handler_2d: InputHandler for 2D controls
        renderer_3d: Renderer3D instance for 3D mode
        input_handler_3d: InputHandler for 3D controls
        combat_feedback: CombatFeedback for 3D combat visuals
        reticle: TargetingReticle for 3D aiming
        health_bar: EnemyHealthBar for 3D enemy display
        show_debug (bool): Whether to show debug information
        show_help (bool): Whether to show help text
    """
    
    def __init__(self, stdscr, view_manager):
        """
        Initialize game UI coordinator.
        
        Args:
            stdscr: Curses standard screen object
            view_manager: ViewManager for camera/controller access
        """
        self.stdscr = stdscr
        self.view_manager = view_manager
        
        # Initialize 2D components
        from presentation.renderer_2d import Renderer
        from presentation.input_handler import InputHandler
        
        self.renderer_2d = Renderer(stdscr)
        self.input_handler_2d = InputHandler(stdscr)
        
        # Initialize 3D components
        from presentation.renderer_3d import Renderer3D
        from presentation.input_handler import InputHandler
        from presentation.ui import CombatFeedback, TargetingReticle, EnemyHealthBar
        
        self.renderer_3d = Renderer3D(stdscr, use_textures=True, show_minimap=True, show_sprites=True)
        self.input_handler_3d = InputHandler(stdscr, mode='3d')
        
        self.combat_feedback = CombatFeedback(stdscr)
        self.reticle = TargetingReticle(stdscr)
        self.health_bar = EnemyHealthBar(stdscr)
        
        self.show_debug = False
        self.show_help = False
    
    def show_error(self, message, details=None):
        """
        Show an error message dialog.
        
        Args:
            message (str): Main error message
            details (str): Optional additional details
        """
        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()
        
        try:
            y = max_y // 2
            x = (max_x - len(message)) // 2
            self.stdscr.addstr(y, x, message, curses.A_BOLD)
            
            if details:
                y += 2
                x = (max_x - len(details)) // 2
                self.stdscr.addstr(y, x, details)
            
            y += 2
            prompt = "Press any key to continue..."
            x = (max_x - len(prompt)) // 2
            self.stdscr.addstr(y, x, prompt, curses.A_DIM)
            
        except curses.error:
            pass
        
        self.stdscr.refresh()
        self.stdscr.getch()
    
    def show_item_selection(self, selection_request):
        """
        Show item selection dialog based on request.
        
        Args:
            selection_request (dict): Selection request data
        
        Returns:
            int: Selected index or None
        """
        from presentation.renderer_2d import show_item_selection
        
        return show_item_selection(
            self.stdscr,
            selection_request.items,
            selection_request.title,
            selection_request.allow_zero
        )
    
    def show_main_menu(self, save_manager):
        """
        Show main menu and get user selection.
        
        Args:
            save_manager: SaveManager instance
        
        Returns:
            str: Selected option
        """
        from presentation.renderer_2d import show_main_menu
        return show_main_menu(self.stdscr, save_manager)
    
    def show_test_mode_menu(self):
        """Show test mode configuration menu."""
        from presentation.renderer_2d import show_test_mode_menu
        return show_test_mode_menu(self.stdscr)
    
    def show_statistics(self, stats_manager):
        """Show statistics/leaderboard screen."""
        from presentation.renderer_2d import show_statistics_screen
        show_statistics_screen(self.stdscr, stats_manager)
    
    def show_game_over(self, stats, victory=False):
        """Show game over screen with statistics."""
        from presentation.renderer_2d import show_game_over_screen
        return show_game_over_screen(self.stdscr, stats, victory)
    
    def render_game(self, game_session):
        """
        Render current game state (2D or 3D based on mode).
        
        Args:
            game_session: GameSession instance
        """
        if game_session.is_3d_mode():
            self._render_game_3d(game_session)
        else:
            self._render_game_2d(game_session)
    
    def _render_game_2d(self, game_session):
        """Render game in 2D mode."""
        level = game_session.get_current_level()
        character = game_session.get_character()
        
        fog_of_war = game_session.get_fog_of_war() if game_session.should_use_fog_of_war() else None
        
        self.renderer_2d.render_level(level, character, fog_of_war, game_session.stats)
        
        message = game_session.get_message()
        if message:
            self.renderer_2d.display_message(message)
    
    def _render_game_3d(self, game_session):
        """Render game in 3D mode."""
        self.stdscr.clear()
        level = game_session.get_current_level()
        character = game_session.get_character()
        camera = self.view_manager.camera
        camera_controller = self.view_manager.camera_controller

        if camera is None or camera_controller is None:
            self.stdscr.clear()
            try:
                self.stdscr.addstr(1, 2, "3D camera not initialized. Switching to 2D...")
            except curses.error:
                pass
            self.stdscr.refresh()
            game_session.rendering_mode = '2d'
            return
        
        fog_of_war = game_session.get_fog_of_war() if game_session.should_use_fog_of_war() else None
        
        viewport_x = 2
        viewport_y = 2

        max_y, max_x = self.stdscr.getmaxyx()
        status_lines = 6
        status_gap = 2
        help_lines = 3 if self.show_help else 0
        min_width = 20
        min_height = 8

        available_width = max_x - viewport_x - 1
        available_height = max_y - viewport_y - (status_gap + status_lines + help_lines)

        viewport_width = min(70, max(available_width, 0))
        viewport_height = min(20, max(available_height, 0))

        if viewport_width < min_width or viewport_height < min_height:
            self.stdscr.clear()
            try:
                self.stdscr.addstr(1, 2, "Terminal too small for 3D view.")
                self.stdscr.addstr(2, 2, "Resize window or switch to 2D (Tab).")
            except curses.error:
                pass
            self.stdscr.refresh()
            return

        self.renderer_3d.set_viewport(viewport_width, viewport_height)
        camera_controller.set_targeting_viewport_width(self.renderer_3d.viewport_width)
        
        self.renderer_3d.render_viewport_border(x_offset=viewport_x, y_offset=viewport_y)
        self.renderer_3d.render_3d_view(camera, level, fog_of_war=fog_of_war,
                                        x_offset=viewport_x, y_offset=viewport_y)
        self.renderer_3d.render_mode_indicator(y_offset=viewport_y - 1)
        
        entity, entity_type, distance = camera_controller.get_entity_in_front(
            level, viewport_width=self.renderer_3d.viewport_width
        )

        # Door detection in front of camera (without triggering interaction)
        rad = math.radians(camera.angle)
        check_x = camera.x + math.cos(rad) * camera_controller.interaction_range
        check_y = camera.y + math.sin(rad) * camera_controller.interaction_range
        door = level.get_door_at(int(check_x), int(check_y))

        if door:
            door_target = 'door_locked' if door.is_locked else 'door_open'
            self.reticle.set_target(door_target, door)
        else:
            self.reticle.set_target(entity_type, entity)
        
        self.reticle.render(self.renderer_3d.viewport_width, self.renderer_3d.viewport_height,
                           x_offset=viewport_x, y_offset=viewport_y)
        
        if entity_type == 'enemy':
            self.health_bar.render_for_enemy(entity, self.renderer_3d.viewport_width,
                                             self.renderer_3d.viewport_height,
                                             x_offset=viewport_x, y_offset=viewport_y)
        
        # Log messages for 3D mode and render feedback
        message = game_session.get_message()
        if message:
            self.renderer_2d.display_message(message)

        self.combat_feedback.update()
        self.combat_feedback.render(
            x_offset=viewport_x,
            y_offset=viewport_y,
            max_width=self.renderer_3d.viewport_width,
            viewport_width=self.renderer_3d.viewport_width,
            viewport_height=self.renderer_3d.viewport_height
        )
        
        from presentation.renderer_2d import render_status_panel, render_message_log
        status_y = viewport_y + self.renderer_3d.viewport_height + 2
        render_status_panel(self.stdscr, character, level, game_session.stats, y_offset=status_y)

        # Render message log below status panel (3D mode)
        message_log_y = status_y + 7
        render_message_log(self.stdscr, self.renderer_2d.message_log, y_offset=message_log_y, max_messages=4)
        
        if self.show_help:
            help_y = status_y + 10
            self._render_3d_help(x_offset=viewport_x, y_offset=help_y)
    
    def _render_3d_help(self, x_offset=0, y_offset=0):
        """Render help text for 3D mode."""
        help_lines = [
            "WASD/Arrows - Move/Rotate | Q/E - Strafe | F/Space - Interact",
            "X - Attack | G - Pickup | J - Food | H - Weapon | K - Elixir | R - Scroll",
            "Tab - Toggle 2D/3D | M - Mini-map | L - Local/Global | I - Debug | ? - Help"
        ]
        
        for i, line in enumerate(help_lines):
            try:
                self.stdscr.addstr(y_offset + i, x_offset, line[:70], curses.A_DIM)
            except curses.error:
                pass
    
    def get_player_action(self, game_session):
        """
        Get next player action from input (2D or 3D based on mode).
        
        Args:
            game_session: GameSession instance
        
        Returns:
            tuple: (action_type, action_data)
        """
        if game_session.is_3d_mode():
            action = self.input_handler_3d.get_action()
            
            from presentation.input_handler import InputHandler
            
            if action == InputHandler.ACTION_TOGGLE_MODE:
                new_mode = game_session.toggle_rendering_mode()
                return ('toggle_mode', {'new_mode': new_mode})
            elif action == InputHandler.ACTION_TOGGLE_DEBUG:
                self.show_debug = not self.show_debug
                return (InputHandler.ACTION_NONE, None)
            elif action == InputHandler.ACTION_TOGGLE_HELP:
                self.show_help = not self.show_help
                return (InputHandler.ACTION_NONE, None)
            elif action == InputHandler.ACTION_TOGGLE_TEXTURES:
                self.renderer_3d.use_textures = not self.renderer_3d.use_textures
                return (InputHandler.ACTION_NONE, None)
            elif action == InputHandler.ACTION_TOGGLE_MINIMAP:
                self.renderer_3d.toggle_minimap()
                return (InputHandler.ACTION_NONE, None)
            elif action == InputHandler.ACTION_TOGGLE_MINIMAP_MODE:
                self.renderer_3d.toggle_minimap_mode()
                return (InputHandler.ACTION_NONE, None)
            elif action == InputHandler.ACTION_TOGGLE_SPRITES:
                self.renderer_3d.toggle_sprites()
                return (InputHandler.ACTION_NONE, None)
            
            return (action, None)
        else:
            action_type, action_data = self.input_handler_2d.get_action()
            from presentation.input_handler import InputHandler

            if action_type == InputHandler.ACTION_TOGGLE_MODE:
                new_mode = game_session.toggle_rendering_mode()
                return ('toggle_mode', {'new_mode': new_mode})

            return (action_type, action_data)
    
    def display_message(self, message):
        """Display a message."""
        self.renderer_2d.display_message(message)
    
    def clear_messages(self):
        """Clear message log."""
        self.renderer_2d.message_log.clear()
        self.combat_feedback.clear()
    
    def cleanup(self):
        """Clean up and restore terminal."""
        self.renderer_2d.cleanup()
