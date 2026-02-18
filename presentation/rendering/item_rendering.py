"""
Item rendering helpers for 2D and 3D modes.
"""
from config.game_config import ItemType
from presentation.colors import get_item_color, get_key_door_color

_ITEM_CHARS = {
    ItemType.FOOD:     '%',
    ItemType.TREASURE: '$',
    ItemType.WEAPON:   '(',
    ItemType.ELIXIR:   '!',
    ItemType.SCROLL:   '?',
    ItemType.KEY:      'k',
}

_ITEM_PRIORITY = {
    ItemType.KEY:      10,
    ItemType.WEAPON:    8,
    ItemType.ELIXIR:    7,
    ItemType.SCROLL:    6,
    ItemType.TREASURE:  4,
    ItemType.FOOD:      3,
}

_ITEM_DESCRIPTIONS = {
    ItemType.FOOD:     'Food (restores health)',
    ItemType.TREASURE: 'Gold (increases score)',
    ItemType.WEAPON:   'Weapon (increases damage)',
    ItemType.ELIXIR:   'Elixir (special effect)',
    ItemType.SCROLL:   'Scroll (magical effect)',
    ItemType.KEY:      'Key (unlocks doors)',
}


def get_item_char(item) -> str:
    """Return the display character for an item."""
    return _ITEM_CHARS.get(item.item_type, '?')


def get_item_render_data(item):
    """
    Return (char, color_pair_id) for an item.

    Keys use the colour-coded door palette; all other items use the
    standard item colour lookup.
    """
    char = _ITEM_CHARS.get(item.item_type, '?')
    if item.item_type == ItemType.KEY:
        color = get_key_door_color(item.color)
    else:
        color = get_item_color(char)
    return char, color


def get_item_description(item) -> str:
    """Return a human-readable description for an item."""
    desc = _ITEM_DESCRIPTIONS.get(item.item_type, 'Unknown item')
    if item.item_type == ItemType.KEY and hasattr(item, 'color'):
        desc = f'{item.color.value.capitalize()} {desc}'
    return desc


def get_item_priority(item) -> int:
    """
    Return a rendering priority for an item (higher = more important).

    Used to decide which items to highlight or render first.
    Range: 0–10.
    """
    return _ITEM_PRIORITY.get(item.item_type, 0)


def should_item_glow(item) -> bool:
    """Return True for high-priority items that warrant a visual emphasis."""
    return get_item_priority(item) >= 7
