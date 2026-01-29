"""
Input handling for keyboard controls in 2D mode.

This module processes keyboard input and converts it into game actions.
Supports both WASD and arrow key movement schemes, plus action keys
for item usage and game control.
"""
import curses


class InputHandler:
    """
    Handles keyboard input and converts to game actions.
    
    Processes raw key presses from curses and translates them into
    structured action tuples that the game logic can understand.
    
    Attributes:
        stdscr: Curses standard screen object
    """
    
    # Action types
    ACTION_MOVE = "move"
    ACTION_USE_WEAPON = "use_weapon"
    ACTION_USE_FOOD = "use_food"
    ACTION_USE_ELIXIR = "use_elixir"
    ACTION_USE_SCROLL = "use_scroll"
    ACTION_QUIT = "quit"
    ACTION_NONE = "none"
    
    # Direction tuples (dx, dy)
    DIR_UP = (0, -1)
    DIR_DOWN = (0, 1)
    DIR_LEFT = (-1, 0)
    DIR_RIGHT = (1, 0)
    
    def __init__(self, stdscr):
        """
        Initialize input handler.
        
        Args:
            stdscr: Curses standard screen object
        """
        self.stdscr = stdscr
        # Set nodelay to False so getch() waits for input
        self.stdscr.nodelay(False)
    
    def get_action(self):
        """
        Get the next action from user input.
        
        Blocks until a key is pressed, then returns the corresponding
        action and any associated data (like movement direction).
        
        Returns:
            tuple: (action_type, data)
                - For movement: (ACTION_MOVE, (dx, dy))
                - For items: (action_type, None)
                - For quit: (ACTION_QUIT, None)
                - For unknown: (ACTION_NONE, None)
        """
        key = self.stdscr.getch()
        
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
        
        # Unknown key
        else:
            return (self.ACTION_NONE, None)
    
    def get_selection(self, max_options):
        """
        Get a numeric selection from user (0-9).
        
        Used for selecting items from inventory menus.
        Blocks until a valid selection or cancellation is made.
        
        Args:
            max_options (int): Maximum number of valid options
        
        Returns:
            int: Selected index (0-9) or None if cancelled
        """
        while True:
            key = self.stdscr.getch()
            
            # ESC or 'q' to cancel
            if key == 27 or key == ord('q') or key == ord('Q'):
                return None
            
            # Number keys
            if ord('0') <= key <= ord('9'):
                selection = key - ord('0')
                if selection < max_options:
                    return selection
            
            # Invalid input - keep waiting
            continue