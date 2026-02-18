from types import SimpleNamespace

from config.game_config import ItemType
from presentation.rendering.minimap_renderer import MiniMapRenderer
import presentation.rendering.minimap_renderer as minimap_mod


class FakeStdScr:
    def __init__(self, height=40, width=120):
        self.height = height
        self.width = width
        self.cells = {}

    def getmaxyx(self):
        return (self.height, self.width)

    def addch(self, y, x, ch, attr=0):
        if isinstance(ch, int):
            ch = chr(ch)
        self.cells[(y, x)] = (ch, attr)

    def addstr(self, y, x, text, attr=0):
        for i, ch in enumerate(text):
            self.addch(y, x + i, ch, attr)

    def get_char(self, y, x):
        return self.cells.get((y, x), (" ", 0))[0]


class DummyLevel:
    def __init__(self):
        self.exit_position = (12, 12)
        self.exit_room_index = 0
        self.rooms = [SimpleNamespace(x=10, y=10, width=6, height=6, items=[], enemies=[])]
        self.corridors = [SimpleNamespace(tiles={(5, 5), (6, 5), (7, 5)})]

    def is_wall(self, x, y):
        return x in (10, 15) or y in (10, 15)

    def is_walkable(self, x, y):
        return 0 <= x < 80 and 0 <= y < 24 and not self.is_wall(x, y)

    def get_corridor_at(self, x, y):
        if (x, y) in self.corridors[0].tiles:
            return self.corridors[0], 0
        return None, None

    def get_room_at(self, x, y):
        room = self.rooms[0]
        if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
            return room, 0
        return None, None


class DummyFog:
    def __init__(self, discovered_rooms=None, discovered_corridors=None, visible_tiles=None):
        self._rooms = discovered_rooms or set()
        self._corridors = discovered_corridors or set()
        self._visible = visible_tiles or set()

    def is_tile_visible(self, x, y):
        return (x, y) in self._visible

    def is_position_visible(self, x, y):
        return self.is_tile_visible(x, y)

    def is_room_discovered(self, room_idx):
        return room_idx in self._rooms

    def is_corridor_discovered(self, corridor_idx):
        return corridor_idx in self._corridors


def test_minimap_local_mode_places_player_in_center(monkeypatch):
    monkeypatch.setattr(minimap_mod.curses, "A_BOLD", 1 << 10, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "A_DIM", 1 << 11, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "A_NORMAL", 0, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "color_pair", lambda c: c * 256)

    stdscr = FakeStdScr()
    renderer = MiniMapRenderer(map_width=80, map_height=24, minimap_size=11)
    level = DummyLevel()
    camera = SimpleNamespace(x=12.0, y=12.0, angle=0.0)

    renderer.render_minimap(stdscr, level, camera, fog_of_war=None, x_offset=2, y_offset=2)

    half = renderer.minimap_size // 2
    assert stdscr.get_char(2 + 1 + half, 2 + 1 + half) == renderer.PLAYER_CHAR


def test_minimap_toggle_mode_switches_local_global():
    renderer = MiniMapRenderer(map_width=80, map_height=24, minimap_size=11)
    assert renderer.mode == renderer.MODE_LOCAL
    assert renderer.toggle_mode() == renderer.MODE_GLOBAL
    assert renderer.toggle_mode() == renderer.MODE_LOCAL


def test_minimap_fog_hides_undiscovered_tiles(monkeypatch):
    monkeypatch.setattr(minimap_mod.curses, "A_BOLD", 1 << 10, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "A_DIM", 1 << 11, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "A_NORMAL", 0, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "color_pair", lambda c: c * 256)

    stdscr = FakeStdScr()
    renderer = MiniMapRenderer(map_width=80, map_height=24, minimap_size=9)
    level = DummyLevel()
    camera = SimpleNamespace(x=40.0, y=12.0, angle=0.0)
    fog = DummyFog(discovered_rooms=set(), discovered_corridors=set(), visible_tiles=set())

    renderer.render_minimap(stdscr, level, camera, fog_of_war=fog, x_offset=1, y_offset=1)

    # Any non-player tile should stay blank when undiscovered.
    assert stdscr.get_char(1 + 1, 1 + 1) == renderer.UNKNOWN_CHAR


def test_minimap_local_renders_visible_items_and_enemies(monkeypatch):
    monkeypatch.setattr(minimap_mod.curses, "A_BOLD", 1 << 10, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "A_DIM", 1 << 11, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "A_NORMAL", 0, raising=False)
    monkeypatch.setattr(minimap_mod.curses, "color_pair", lambda c: c * 256)

    stdscr = FakeStdScr()
    renderer = MiniMapRenderer(map_width=80, map_height=24, minimap_size=11)
    level = DummyLevel()
    camera = SimpleNamespace(x=12.0, y=12.0, angle=0.0)

    item = SimpleNamespace(item_type=ItemType.FOOD, position=(13, 13))
    enemy = SimpleNamespace(position=(14, 13), char='z', is_alive=lambda: True)
    level.rooms[0].items = [item]
    level.rooms[0].enemies = [enemy]

    fog = DummyFog(
        discovered_rooms={0},
        discovered_corridors={0},
        visible_tiles={(13, 13), (12, 12)},
    )

    renderer.render_minimap(stdscr, level, camera, fog_of_war=fog, x_offset=2, y_offset=2)

    half = renderer.minimap_size // 2
    # Visible item is rendered.
    assert stdscr.get_char(2 + 1 + half + 1, 2 + 1 + half + 1) == '%'
    # Enemy out of visibility is not rendered.
    assert stdscr.get_char(2 + 1 + half + 1, 2 + 1 + half + 2) != 'z'
