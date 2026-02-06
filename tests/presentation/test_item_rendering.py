"""
Tests for shared item rendering helpers.
"""

from config.game_config import ItemType
from domain.key_door_system import KeyColor
from presentation.colors import get_key_door_color, get_item_color
from presentation.rendering.item_rendering import get_item_char, get_item_render_data


class MockItem:
    def __init__(self, item_type, color=None):
        self.item_type = item_type
        self.color = color


class TestItemRendering:
    def test_get_item_char_defaults(self):
        item = MockItem(ItemType.FOOD)
        assert get_item_char(item) == '%'

    def test_get_item_char_unknown(self):
        item = MockItem("unknown")
        assert get_item_char(item) == '?'

    def test_get_item_render_data_non_key(self):
        item = MockItem(ItemType.WEAPON)
        char, color = get_item_render_data(item)
        assert char == '('
        assert color == get_item_color(char)

    def test_get_item_render_data_key(self):
        item = MockItem(ItemType.KEY, color=KeyColor.RED)
        char, color = get_item_render_data(item)
        assert char == 'k'
        assert color == get_key_door_color(KeyColor.RED)
