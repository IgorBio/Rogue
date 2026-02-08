"""
Unified input handling for keyboard controls in 2D and 3D modes.
"""
import curses
from domain.services.action_types import ActionType


class InputHandler:
    """
    Handles keyboard input and converts to game actions for 2D and 3D modes.

    Attributes:
        stdscr: Curses standard screen object
        mode: '2d' or '3d'
    """

    # Action types (domain)
    ACTION_MOVE = ActionType.MOVE
    ACTION_USE_WEAPON = ActionType.USE_WEAPON
    ACTION_USE_FOOD = ActionType.USE_FOOD
    ACTION_USE_ELIXIR = ActionType.USE_ELIXIR
    ACTION_USE_SCROLL = ActionType.USE_SCROLL
    ACTION_QUIT = ActionType.QUIT
    ACTION_NONE = ActionType.NONE

    # 3D movement (domain)
    ACTION_MOVE_FORWARD = ActionType.MOVE_FORWARD
    ACTION_MOVE_BACKWARD = ActionType.MOVE_BACKWARD
    ACTION_STRAFE_LEFT = ActionType.STRAFE_LEFT
    ACTION_STRAFE_RIGHT = ActionType.STRAFE_RIGHT
    ACTION_ROTATE_LEFT = ActionType.ROTATE_LEFT
    ACTION_ROTATE_RIGHT = ActionType.ROTATE_RIGHT

    # 3D combat & interaction (domain)
    ACTION_ATTACK = ActionType.ATTACK
    ACTION_PICKUP = ActionType.PICKUP
    ACTION_INTERACT = ActionType.INTERACT

    # UI-only actions
    ACTION_TOGGLE_MODE = "toggle_mode"
    ACTION_TOGGLE_TEXTURES = "toggle_textures"
    ACTION_TOGGLE_DEBUG = "toggle_debug"
    ACTION_TOGGLE_HELP = "toggle_help"
    ACTION_TOGGLE_MINIMAP = "toggle_minimap"
    ACTION_TOGGLE_SPRITES = "toggle_sprites"

    # Direction tuples (dx, dy) for 2D
    DIR_UP = (0, -1)
    DIR_DOWN = (0, 1)
    DIR_LEFT = (-1, 0)
    DIR_RIGHT = (1, 0)

    def __init__(self, stdscr, mode: str = '2d'):
        self.stdscr = stdscr
        self.mode = mode
        self.stdscr.nodelay(False)

        # 3D control scheme flags
        self.use_arrow_keys = True
        self.use_wasd = True
        self.auto_pickup = False

    def set_mode(self, mode: str) -> None:
        """Set input mode to '2d' or '3d'."""
        self.mode = mode

    def get_action(self):
        """Get the next action based on current mode."""
        key = self.stdscr.getch()
        if self.mode == '3d':
            return self._get_3d_action(key)
        return self._get_2d_action(key)

    def _get_2d_action(self, key):
        # Movement keys (WASD) - accept both upper and lowercase
        if key == ord('w') or key == ord('W'):
            return (self.ACTION_MOVE, self.DIR_UP)
        elif key == ord('s') or key == ord('S'):
            return (self.ACTION_MOVE, self.DIR_DOWN)
        elif key == ord('a') or key == ord('A'):
            return (self.ACTION_MOVE, self.DIR_LEFT)
        elif key == ord('d') or key == ord('D'):
            return (self.ACTION_MOVE, self.DIR_RIGHT)

        # Arrow keys (alternative movement)
        elif key == curses.KEY_UP:
            return (self.ACTION_MOVE, self.DIR_UP)
        elif key == curses.KEY_DOWN:
            return (self.ACTION_MOVE, self.DIR_DOWN)
        elif key == curses.KEY_LEFT:
            return (self.ACTION_MOVE, self.DIR_LEFT)
        elif key == curses.KEY_RIGHT:
            return (self.ACTION_MOVE, self.DIR_RIGHT)

        # Toggle 2D/3D mode (handled by UI layer)
        elif key == ord('\t') or key == 9:
            return (self.ACTION_TOGGLE_MODE, None)

        # Item usage keys
        elif key == ord('h') or key == ord('H'):
            return (self.ACTION_USE_WEAPON, None)
        elif key == ord('j') or key == ord('J'):
            return (self.ACTION_USE_FOOD, None)
        elif key == ord('k') or key == ord('K'):
            return (self.ACTION_USE_ELIXIR, None)
        elif key == ord('e') or key == ord('E'):
            return (self.ACTION_USE_SCROLL, None)

        # Quit key
        elif key == ord('q') or key == ord('Q'):
            return (self.ACTION_QUIT, None)

        return (self.ACTION_NONE, None)

    def _get_3d_action(self, key):
        # Movement - WASD (primary in 3D mode)
        if self.use_wasd:
            if key == ord('w') or key == ord('W'):
                return self.ACTION_MOVE_FORWARD
            elif key == ord('s') or key == ord('S'):
                return self.ACTION_MOVE_BACKWARD
            elif key == ord('a') or key == ord('A'):
                return self.ACTION_ROTATE_LEFT
            elif key == ord('d') or key == ord('D'):
                return self.ACTION_ROTATE_RIGHT

        # Movement - Arrow keys (alternative)
        if self.use_arrow_keys:
            if key == curses.KEY_UP:
                return self.ACTION_MOVE_FORWARD
            elif key == curses.KEY_DOWN:
                return self.ACTION_MOVE_BACKWARD
            elif key == curses.KEY_LEFT:
                return self.ACTION_ROTATE_LEFT
            elif key == curses.KEY_RIGHT:
                return self.ACTION_ROTATE_RIGHT

        # Quit - Q
        if key == ord('q') or key == ord('Q'):
            return self.ACTION_QUIT

        # Combat & Interaction - F or Space
        elif key == ord('f') or key == ord('F') or key == ord(' '):
            return self.ACTION_INTERACT

        # Direct attack - X
        elif key == ord('x') or key == ord('X'):
            return self.ACTION_ATTACK

        # Direct pickup - G
        elif key == ord('g') or key == ord('G'):
            return self.ACTION_PICKUP

        # Item usage (same as 2D mode)
        elif key == ord('h') or key == ord('H'):
            return self.ACTION_USE_WEAPON
        elif key == ord('j') or key == ord('J'):
            return self.ACTION_USE_FOOD
        elif key == ord('k') or key == ord('K'):
            return self.ACTION_USE_ELIXIR
        elif key == ord('e') or key == ord('E'):
            return self.ACTION_USE_SCROLL

        # Mode toggling
        elif key == ord('\t') or key == 9:
            return self.ACTION_TOGGLE_MODE

        # Feature toggles
        elif key == ord('t') or key == ord('T'):
            return self.ACTION_TOGGLE_TEXTURES
        elif key == ord('i') or key == ord('I'):
            return self.ACTION_TOGGLE_DEBUG
        elif key == ord('m') or key == ord('M'):
            return self.ACTION_TOGGLE_MINIMAP
        elif key == ord('n') or key == ord('N'):
            return self.ACTION_TOGGLE_SPRITES
        elif key == ord('?') or key == ord('/'):
            return self.ACTION_TOGGLE_HELP

        # Quit
        elif key == 27:  # ESC
            return self.ACTION_QUIT

        return self.ACTION_NONE

    def enable_arrow_keys(self, enabled=True):
        self.use_arrow_keys = enabled

    def enable_wasd(self, enabled=True):
        self.use_wasd = enabled

    def enable_auto_pickup(self, enabled=True):
        self.auto_pickup = enabled

    def get_control_help(self):
        help_text = []

        help_text.append("??? MOVEMENT ???")
        if self.use_wasd:
            help_text.append("W/? - Move Forward")
            help_text.append("S/? - Move Backward")
            help_text.append("A/? - Rotate Left")
            help_text.append("D/? - Rotate Right")
        if self.use_arrow_keys and not self.use_wasd:
            help_text.append("?   - Move Forward")
            help_text.append("?   - Move Backward")
            help_text.append("?   - Rotate Left")
            help_text.append("?   - Rotate Right")

        help_text.append("")
        help_text.append("??? COMBAT ???")
        help_text.append("F/Space - Interact")
        help_text.append("X       - Attack Enemy")
        help_text.append("G       - Pick Up Item")

        help_text.append("")
        help_text.append("??? ITEMS ???")
        help_text.append("H - Use Weapon")
        help_text.append("J - Use Food")
        help_text.append("K - Use Elixir")
        help_text.append("E - Use Scroll")

        help_text.append("")
        help_text.append("??? VIEW ???")
        help_text.append("Tab - Toggle 2D/3D")
        help_text.append("T   - Toggle Textures")
        help_text.append("M   - Toggle Mini-map")
        help_text.append("N   - Toggle Sprites")
        help_text.append("I   - Toggle Debug")
        help_text.append("?   - Toggle Help")
        help_text.append("Q/ESC - Quit")

        return help_text

    def get_selection(self, max_options):
        while True:
            key = self.stdscr.getch()
            if key == 27 or key == ord('q') or key == ord('Q'):
                return None
            if ord('0') <= key <= ord('9'):
                selection = key - ord('0')
                if selection < max_options:
                    return selection
            continue
