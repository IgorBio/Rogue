"""
3D renderer for first-person perspective using raycasting.
"""
import curses
import math
from presentation.camera import Camera
from presentation.rendering.raycasting import cast_fov_rays, calculate_wall_height
from presentation.rendering.texture_system import get_texture_manager, TexturedRenderer
from presentation.rendering.minimap_renderer import MiniMapRenderer
from presentation.rendering.sprite_renderer_3d import SpriteRenderer
from presentation.colors import (
    init_colors,
    get_key_door_color,
    COLOR_WALL,
    COLOR_FLOOR,
    COLOR_CORRIDOR,
    COLOR_UI_TEXT,
)
from config.game_config import GameConfig
from common.logging_utils import get_logger


class Renderer3D:
    """First-person 3D renderer with texture and sprite support."""

    SHADE_CHARS = ['█', '▓', '▓', '▒', '▒', '▒', '░', '░', '░', '·', '·', ' ']
    SHADE_DISTANCES = [1.5, 2.5, 3.5, 5.0, 6.5, 8.0, 10.0, 12.0, 14.5, 17.0, 19.5, 22.0]
    FLOOR_CHARS = ['.', ':', ';', 'x', '#']
    CEILING_CHARS = ['#', 'x', ':', '.', ' ']

    def __init__(self, stdscr, viewport_width=None, viewport_height=None,
                 use_textures=True, show_minimap=True, show_sprites=True):
        """
        Args:
            stdscr: Curses standard screen object.
            viewport_width: Viewport width in characters (None = auto).
            viewport_height: Viewport height in characters (None = auto).
            use_textures: Enable texture rendering.
            show_minimap: Enable mini-map overlay.
            show_sprites: Enable sprite rendering.
        """
        self.stdscr = stdscr
        self.logger = get_logger(__name__)
        self._logger = self.logger
        self._curses_error_count = 0
        self._curses_error_limit = 5

        max_y, max_x = stdscr.getmaxyx()
        self.viewport_width = max(40, viewport_width or (max_x - 2))
        self.viewport_height = max(15, viewport_height or (max_y - 8))

        self.use_textures = use_textures
        self.show_minimap = show_minimap
        self.show_sprites = show_sprites
        self.show_compass = False
        self.show_quest_marker = False

        if self.use_textures:
            self.texture_manager = get_texture_manager()
            self.textured_renderer = TexturedRenderer(self.texture_manager)
        else:
            self.texture_manager = None
            self.textured_renderer = None

        self.sprite_renderer = (
            SpriteRenderer(self.viewport_width, self.viewport_height)
            if self.show_sprites else None
        )

        self.minimap_renderer = (
            MiniMapRenderer(
                minimap_size=15,
                map_width=GameConfig.MAP_WIDTH,
                map_height=GameConfig.MAP_HEIGHT,
            )
            if self.show_minimap else None
        )

        self.z_buffer = [float('inf')] * self.viewport_width
        self._shade_cache = {}

        init_colors()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, camera, level, fog_of_war=None, x_offset=0, y_offset=0):
        """
        Render one frame of the 3D view.

        Args:
            camera: Camera object.
            level: Level object.
            fog_of_war: Optional FogOfWar object.
            x_offset: Left edge of the viewport on screen.
            y_offset: Top edge of the viewport on screen.
        """
        self.z_buffer = [float('inf')] * self.viewport_width

        hits = cast_fov_rays(camera, level, num_rays=self.viewport_width)
        for column, hit in enumerate(hits):
            if hit:
                self.z_buffer[column] = hit.distance
                self._render_wall_column(column, hit, x_offset, y_offset)
            else:
                self._render_empty_column(column, x_offset, y_offset)

        if self.show_sprites and self.sprite_renderer:
            self.sprite_renderer.sync_projection(
                self.viewport_width, self.viewport_height, camera.fov
            )
            sprites = self.sprite_renderer.collect_sprites(level, fog_of_war)
            visible = self.sprite_renderer.calculate_sprite_positions(sprites, camera)
            self.sprite_renderer.render_sprites(
                self.stdscr, visible, camera, self.z_buffer,
                x_offset=x_offset, y_offset=y_offset,
            )

        if self.show_minimap and self.minimap_renderer:
            mm_x = x_offset + self.viewport_width - self.minimap_renderer.minimap_size - 3
            mm_y = y_offset + self.viewport_height - self.minimap_renderer.minimap_size - 3
            if fog_of_war:
                self.minimap_renderer.render_minimap(
                    self.stdscr, level, camera, fog_of_war,
                    x_offset=mm_x, y_offset=mm_y,
                )
            else:
                self.minimap_renderer.render_minimap_simple(
                    self.stdscr, level, camera,
                    x_offset=mm_x, y_offset=mm_y,
                )

        self.render_viewport_border(x_offset, y_offset)

    def render_3d_view(self, camera, level, fog_of_war=None,
                       x_offset=0, y_offset=0):
        """Alias for render() — kept for backward compatibility."""
        return self.render(camera, level, fog_of_war, x_offset, y_offset)

    def set_viewport(self, width: int, height: int) -> None:
        """Resize the viewport and reinitialise dependent buffers."""
        self.viewport_width = max(40, width)
        self.viewport_height = max(15, height)
        self.z_buffer = [float('inf')] * self.viewport_width
        if self.sprite_renderer:
            self.sprite_renderer.viewport_width = self.viewport_width
            self.sprite_renderer.viewport_height = self.viewport_height

    def get_viewport_size(self):
        """Return (width, height) of the current viewport."""
        return (self.viewport_width, self.viewport_height)

    def toggle_textures(self):
        self.use_textures = not self.use_textures
        return self.use_textures

    def toggle_minimap(self):
        self.show_minimap = not self.show_minimap
        return self.show_minimap

    def toggle_sprites(self):
        self.show_sprites = not self.show_sprites
        return self.show_sprites

    def toggle_compass(self):
        self.show_compass = not self.show_compass
        return self.show_compass

    def toggle_quest_marker(self):
        self.show_quest_marker = not self.show_quest_marker
        return self.show_quest_marker

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _render_wall_column(self, column, hit, x_offset, y_offset):
        wall_height = calculate_wall_height(hit.distance, self.viewport_height)
        wall_top = max(0, (self.viewport_height - wall_height) // 2)
        wall_bottom = min(self.viewport_height, wall_top + wall_height)
        color = self._get_wall_color(hit.wall_type, hit.side, hit.door)
        wall_attr = self._get_wall_attr(hit.side, hit.distance)

        for y in range(wall_top):
            ceiling_char = self._get_ceiling_char(y, wall_top)
            self._draw_char(
                y_offset + y, x_offset + column, ceiling_char, COLOR_UI_TEXT, curses.A_DIM
            )

        if self.use_textures and self.textured_renderer:
            for y in range(wall_top, wall_bottom):
                texture_y = (y - wall_top) / wall_height if wall_height > 0 else 0.0
                char = self.textured_renderer.get_wall_char(
                    hit.wall_type, hit.texture_x, texture_y, hit.distance
                )
                self._draw_char(y_offset + y, x_offset + column, char, color, wall_attr)
        else:
            wall_char = self._get_simple_wall_char(hit)
            if wall_char == ' ':
                wall_char = self._get_shade_char(hit.distance)
            for y in range(wall_top, wall_bottom):
                self._draw_char(y_offset + y, x_offset + column, wall_char, color, wall_attr)

        for y in range(wall_bottom, self.viewport_height):
            floor_char = self._get_floor_char(y, wall_bottom, self.viewport_height)
            self._draw_char(y_offset + y, x_offset + column, floor_char, COLOR_FLOOR)

    def _render_empty_column(self, column, x_offset, y_offset):
        half = self.viewport_height // 2
        for y in range(half):
            ceiling_char = self._get_ceiling_char(y, half)
            self._draw_char(
                y_offset + y, x_offset + column, ceiling_char, COLOR_UI_TEXT, curses.A_DIM
            )
        for y in range(half, self.viewport_height):
            floor_char = self._get_floor_char(y, half, self.viewport_height)
            self._draw_char(y_offset + y, x_offset + column, floor_char, COLOR_FLOOR)

    def _get_wall_color(self, wall_type, side, door=None):
        if wall_type == 'corridor_wall':
            return COLOR_CORRIDOR
        if wall_type in ('door_open', 'door_locked') and door is not None:
            return get_key_door_color(door.color) if door.is_locked else COLOR_CORRIDOR
        if wall_type == 'room_wall_entrance':
            return COLOR_CORRIDOR
        return COLOR_WALL

    def _get_wall_attr(self, side, distance):
        attr = curses.A_NORMAL
        if side == 'EW':
            attr |= curses.A_DIM
        if distance < 2.5:
            attr |= curses.A_BOLD
        return attr

    def _get_simple_wall_char(self, hit):
        chars = {
            'door_locked': '+',
            'door_open': '/',
            'room_wall_entrance': '|',
            'room_wall_beside_entrance': '▓',
        }
        return chars.get(hit.wall_type, ' ')

    def _get_shade_char(self, distance):
        key = int(distance * 10)
        if key in self._shade_cache:
            return self._shade_cache[key]
        for i, threshold in enumerate(self.SHADE_DISTANCES):
            if distance < threshold:
                self._shade_cache[key] = self.SHADE_CHARS[i]
                return self.SHADE_CHARS[i]
        self._shade_cache[key] = self.SHADE_CHARS[-1]
        return self.SHADE_CHARS[-1]

    def _get_floor_char(self, y, wall_bottom, viewport_height):
        span = max(1, viewport_height - wall_bottom - 1)
        rel = (y - wall_bottom) / span
        idx = min(int(rel * (len(self.FLOOR_CHARS) - 1)), len(self.FLOOR_CHARS) - 1)
        return self.FLOOR_CHARS[idx]

    def _get_ceiling_char(self, y, wall_top):
        if wall_top <= 1:
            return ' '
        rel = y / (wall_top - 1)
        idx = min(int(rel * (len(self.CEILING_CHARS) - 1)), len(self.CEILING_CHARS) - 1)
        return self.CEILING_CHARS[idx]

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def render_viewport_border(self, x_offset=0, y_offset=0):
        """Draw a box border around the viewport."""
        try:
            self._draw_string(
                y_offset - 1, x_offset - 1,
                '┌' + '─' * self.viewport_width + '┐',
                COLOR_UI_TEXT,
            )
            self._draw_string(
                y_offset + self.viewport_height, x_offset - 1,
                '└' + '─' * self.viewport_width + '┘',
                COLOR_UI_TEXT,
            )
            for y in range(self.viewport_height):
                self._draw_char(y_offset + y, x_offset - 1, '│', COLOR_UI_TEXT)
                self._draw_char(
                    y_offset + y, x_offset + self.viewport_width, '│', COLOR_UI_TEXT
                )
        except curses.error:
            pass

    def render_mode_indicator(self, y_offset=0):
        """Render a mode label centred at the top of the viewport."""
        text = '[ 3D MODE - TEXTURED ]' if self.use_textures else '[ 3D MODE ]'
        try:
            self._draw_string(
                y_offset, (self.viewport_width - len(text)) // 2, text, COLOR_UI_TEXT
            )
        except curses.error:
            pass

    def render_camera_info(self, camera, x_offset=0, y_offset=0):
        """Render debug camera information."""
        lines = [
            f'Position: ({camera.x:.1f}, {camera.y:.1f})',
            f'Angle: {camera.angle:.0f}',
            f'FOV: {camera.fov:.0f}',
            f'Textures: {"ON" if self.use_textures else "OFF"}',
            f'Minimap: {"ON" if self.show_minimap else "OFF"}',
            f'Sprites: {"ON" if self.show_sprites else "OFF"}',
        ]
        try:
            for i, line in enumerate(lines):
                self._draw_string(y_offset + i, x_offset, line, COLOR_UI_TEXT)
        except curses.error:
            pass

    def clear_viewport(self, x_offset=0, y_offset=0):
        """Fill the viewport area with blank characters."""
        try:
            for y in range(self.viewport_height):
                for x in range(self.viewport_width):
                    self._draw_char(y_offset + y, x_offset + x, ' ', COLOR_UI_TEXT)
        except curses.error:
            pass

    # ------------------------------------------------------------------
    # Low-level drawing
    # ------------------------------------------------------------------

    def _draw_char(self, y, x, char, color_pair, attr=0):
        try:
            self.stdscr.addch(y, x, char, curses.color_pair(color_pair) | attr)
        except curses.error as exc:
            self._log_curses_error(exc, y, x)

    def _draw_string(self, y, x, string, color_pair):
        try:
            self.stdscr.addstr(y, x, string, curses.color_pair(color_pair))
        except curses.error as exc:
            self._log_curses_error(exc, y, x)

    def _log_curses_error(self, exc, y, x):
        if self._curses_error_count >= self._curses_error_limit:
            return
        self._curses_error_count += 1
        self.logger.warning('Curses render error at (%s, %s): %s', x, y, exc)
        if self._curses_error_count == self._curses_error_limit:
            self.logger.warning('Curses error limit reached, suppressing further errors.')
