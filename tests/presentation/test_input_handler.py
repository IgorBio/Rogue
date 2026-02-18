from presentation.input_handler import InputHandler


class FakeStdScr:
    def __init__(self, keys):
        self._keys = list(keys)
        self._nodelay = False

    def nodelay(self, enabled):
        self._nodelay = enabled

    def getch(self):
        if not self._keys:
            return -1
        return self._keys.pop(0)


def test_input_handler_3d_maps_l_to_toggle_minimap_mode():
    stdscr = FakeStdScr([ord('l')])
    handler = InputHandler(stdscr, mode='3d')
    assert handler.get_action() == InputHandler.ACTION_TOGGLE_MINIMAP_MODE


def test_input_handler_3d_maps_shift_l_to_toggle_minimap_mode():
    stdscr = FakeStdScr([ord('L')])
    handler = InputHandler(stdscr, mode='3d')
    assert handler.get_action() == InputHandler.ACTION_TOGGLE_MINIMAP_MODE
