from pathlib import Path
from types import SimpleNamespace

from presentation.camera.camera import Camera
import presentation.renderer_3d as renderer_3d_mod


class FakeStdScr:
    def __init__(self, height=40, width=120):
        self.height = height
        self.width = width
        self.cells = {}

    def getmaxyx(self):
        return (self.height, self.width)

    def addch(self, y, x, char, attr=0):
        if y < 0 or x < 0 or y >= self.height or x >= self.width:
            raise renderer_3d_mod.curses.error("out-of-bounds")
        if isinstance(char, int):
            char = chr(char)
        self.cells[(y, x)] = (char, attr)

    def addstr(self, y, x, text, attr=0):
        for i, ch in enumerate(text):
            self.addch(y, x + i, ch, attr)

    def get_char(self, y, x):
        return self.cells.get((y, x), (" ", 0))[0]

    def get_attr(self, y, x):
        return self.cells.get((y, x), (" ", 0))[1]


def _make_hit(distance, side):
    return SimpleNamespace(
        distance=distance,
        wall_type="room_wall",
        texture_x=0.5,
        hit_x=0,
        hit_y=0,
        side=side,
        door=None,
    )


def _render_viewport_snapshot(stdscr, x_offset, y_offset, width, height):
    lines = []
    for y in range(y_offset, y_offset + height):
        line = "".join(stdscr.get_char(y, x) for x in range(x_offset, x_offset + width))
        lines.append(line)
    return "\n".join(lines)


def test_renderer_3d_snapshot_frame(monkeypatch):
    monkeypatch.setattr(renderer_3d_mod, "init_colors", lambda: None)
    monkeypatch.setattr(renderer_3d_mod.curses, "A_DIM", 1 << 12, raising=False)
    monkeypatch.setattr(renderer_3d_mod.curses, "A_BOLD", 1 << 13, raising=False)
    monkeypatch.setattr(renderer_3d_mod.curses, "color_pair", lambda c: c * 256)

    stdscr = FakeStdScr()
    renderer = renderer_3d_mod.Renderer3D(
        stdscr,
        viewport_width=12,
        viewport_height=8,
        use_textures=False,
        show_minimap=False,
        show_sprites=False,
    )

    pattern = [
        _make_hit(2.0, "NS"),
        _make_hit(2.2, "EW"),
        _make_hit(2.5, "NS"),
        _make_hit(2.8, "EW"),
        _make_hit(3.2, "NS"),
        _make_hit(3.5, "EW"),
        _make_hit(4.0, "NS"),
        _make_hit(4.4, "EW"),
        _make_hit(4.9, "NS"),
        _make_hit(5.4, "EW"),
        _make_hit(6.0, "NS"),
        _make_hit(6.8, "EW"),
    ]
    monkeypatch.setattr(
        renderer_3d_mod,
        "cast_fov_rays",
        lambda camera, level, num_rays: pattern[:num_rays],
    )

    camera = Camera(10, 10, angle=0.0, fov=60.0)
    renderer.render(camera, level=SimpleNamespace(), x_offset=2, y_offset=2)

    frame = _render_viewport_snapshot(stdscr, 2, 2, 12, 8)
    snapshot_path = Path(__file__).with_name("snapshots") / "renderer_3d_frame.txt"
    expected = snapshot_path.read_text(encoding="utf-8").strip("\n")
    assert frame == expected


def test_renderer_3d_ew_side_is_dimmer_than_ns(monkeypatch):
    monkeypatch.setattr(renderer_3d_mod, "init_colors", lambda: None)
    monkeypatch.setattr(renderer_3d_mod.curses, "A_DIM", 1 << 12, raising=False)
    monkeypatch.setattr(renderer_3d_mod.curses, "A_BOLD", 1 << 13, raising=False)
    monkeypatch.setattr(renderer_3d_mod.curses, "color_pair", lambda c: c * 256)

    stdscr = FakeStdScr()
    renderer = renderer_3d_mod.Renderer3D(
        stdscr,
        viewport_width=20,
        viewport_height=12,
        use_textures=False,
        show_minimap=False,
        show_sprites=False,
    )

    ns_hit = _make_hit(3.0, "NS")
    ew_hit = _make_hit(3.0, "EW")
    renderer._render_wall_column(5, ns_hit, x_offset=1, y_offset=1)
    renderer._render_wall_column(6, ew_hit, x_offset=1, y_offset=1)

    ns_attr = stdscr.get_attr(6, 6)
    ew_attr = stdscr.get_attr(6, 7)

    assert ew_attr & renderer_3d_mod.curses.A_DIM
    assert not (ns_attr & renderer_3d_mod.curses.A_DIM)
