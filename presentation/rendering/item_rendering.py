"""
Shared item rendering helpers for 2D and 3D.
"""
from config.game_config import ItemType
from presentation.colors import get_item_color, get_key_door_color


def get_item_char(item) -> str:
    """Get the character representation for an item."""
    item_chars = {
        ItemType.FOOD: '%',
        ItemType.TREASURE: '$',
        ItemType.WEAPON: '(',
        ItemType.ELIXIR: '!',
        ItemType.SCROLL: '?',
        ItemType.KEY: 'k',
    }
    return item_chars.get(item.item_type, '?')


def get_item_render_data(item):
    """
    Get (char, color) for an item.

    Keys use door colors; others use item colors.
    """
    char = get_item_char(item)
    if item.item_type == ItemType.KEY:
        color = get_key_door_color(item.color)
    else:
        color = get_item_color(char)
    return char, color
