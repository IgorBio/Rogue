"""
Color definitions for curses rendering.

This module defines all color pairs used throughout the game's terminal display.
Colors are used to visually distinguish different game elements like walls,
enemies, items, and UI components.
"""
import curses


# Color pair IDs for map elements
COLOR_WALL = 1
COLOR_FLOOR = 2
COLOR_CORRIDOR = 3
COLOR_PLAYER = 4
COLOR_EXIT = 5

# Color pair IDs for enemies
COLOR_ZOMBIE = 6
COLOR_VAMPIRE = 7
COLOR_GHOST = 8
COLOR_OGRE = 9
COLOR_SNAKE_MAGE = 10

# Color pair IDs for items
COLOR_FOOD = 11
COLOR_TREASURE = 12
COLOR_WEAPON = 13
COLOR_ELIXIR = 14
COLOR_SCROLL = 15

# Color pair IDs for UI
COLOR_UI_TEXT = 16
COLOR_UI_HIGHLIGHT = 17

# Color pair IDs for doors and keys
COLOR_DOOR_PURPLE = 18


def init_colors():
    """
    Initialize all color pairs for curses display.
    
    Must be called after curses.start_color() is invoked.
    Sets up color pairs for all game elements including
    map tiles, enemies, items, and UI components.
    """
    # Map elements
    curses.init_pair(COLOR_WALL, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_FLOOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_CORRIDOR, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_PLAYER, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_EXIT, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    
    # Enemies
    curses.init_pair(COLOR_ZOMBIE, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_VAMPIRE, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(COLOR_GHOST, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_OGRE, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SNAKE_MAGE, curses.COLOR_WHITE, curses.COLOR_BLACK)
    
    # Items
    curses.init_pair(COLOR_FOOD, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_TREASURE, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_WEAPON, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_ELIXIR, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SCROLL, curses.COLOR_BLUE, curses.COLOR_BLACK)
    
    # UI elements
    curses.init_pair(COLOR_UI_TEXT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_UI_HIGHLIGHT, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    
    # Doors and keys
    curses.init_pair(COLOR_DOOR_PURPLE, curses.COLOR_MAGENTA, curses.COLOR_BLACK)


def get_enemy_color(enemy_char):
    """
    Get the color pair ID for an enemy based on its character.
    
    Args:
        enemy_char (str): Single character representing the enemy
    
    Returns:
        int: Color pair ID for the enemy
    """
    color_map = {
        'z': COLOR_ZOMBIE,
        'v': COLOR_VAMPIRE,
        'g': COLOR_GHOST,
        'o': COLOR_OGRE,
        's': COLOR_SNAKE_MAGE
    }
    return color_map.get(enemy_char, COLOR_UI_TEXT)


def get_item_color(item_char):
    """
    Get the color pair ID for an item based on its character.
    
    Args:
        item_char (str): Single character representing the item
    
    Returns:
        int: Color pair ID for the item
    """
    color_map = {
        '%': COLOR_FOOD,
        '$': COLOR_TREASURE,
        '(': COLOR_WEAPON,
        '!': COLOR_ELIXIR,
        '?': COLOR_SCROLL
    }
    return color_map.get(item_char, COLOR_UI_TEXT)


def get_key_door_color(color_enum):
    """
    Get the color pair ID for a key or door based on its color.
    
    Args:
        color_enum: KeyColor enum value
    
    Returns:
        int: Color pair ID for rendering
    """
    from domain.key_door_system import KeyColor
    
    color_map = {
        KeyColor.RED: COLOR_VAMPIRE,       # Red (reuse vampire color)
        KeyColor.BLUE: COLOR_SCROLL,       # Blue (reuse scroll color)
        KeyColor.YELLOW: COLOR_TREASURE,   # Yellow (reuse treasure color)
        KeyColor.GREEN: COLOR_FOOD,        # Green (reuse food color)
        KeyColor.PURPLE: COLOR_DOOR_PURPLE # Purple (dedicated color)
    }
    
    return color_map.get(color_enum, COLOR_UI_TEXT)
