"""
Mini-map renderer for 3D mode navigation.
Shows a local tactical window by default and supports global overview mode.
"""
import curses
import math
from presentation.colors import (
    COLOR_WALL,
    COLOR_FLOOR,
    COLOR_CORRIDOR,
    COLOR_PLAYER,
    COLOR_EXIT,
    COLOR_UI_TEXT,
    COLOR_UI_HIGHLIGHT,
    get_enemy_color,
)
from presentation.rendering.item_rendering import get_item_render_data


class MiniMapRenderer:
    """Renders a mini-map overlay for 3D mode."""

    WALL_CHAR = '#'
    FLOOR_CHAR = '.'
    CORRIDOR_CHAR = ':'
    UNKNOWN_CHAR = ' '
    PLAYER_CHAR = '@'
    EXIT_CHAR = '>'

    MODE_LOCAL = 'local'
    MODE_GLOBAL = 'global'

    def __init__(self, map_width, map_height, minimap_size=12):
        self.map_width = map_width
        self.map_height = map_height
        self.minimap_size = minimap_size

        self.scale_x = map_width / minimap_size
        self.scale_y = map_height / minimap_size

        self.show_discovered_only = True
        self.show_fog = True
        self.show_enemies = True
        self.show_items = True

        # New defaults for better readability.
        self.mode = self.MODE_LOCAL
        self.local_radius = max(3, minimap_size // 2)

    def render_minimap(self, stdscr, level, camera, fog_of_war=None,
                      x_offset=0, y_offset=0):
        self._draw_border(stdscr, x_offset, y_offset)

        if self.mode == self.MODE_LOCAL:
            self._draw_local_window(stdscr, level, camera, fog_of_war, x_offset, y_offset)
        else:
            self._draw_global_window(stdscr, level, camera, fog_of_war, x_offset, y_offset)

        self._draw_title(stdscr, x_offset, y_offset)
    def _draw_border(self, stdscr, x_offset, y_offset):
        try:
            stdscr.addstr(
                y_offset,
                x_offset,
                '+' + '-' * self.minimap_size + '+',
                curses.color_pair(COLOR_UI_TEXT)
            )
            for y in range(self.minimap_size):
                stdscr.addch(y_offset + y + 1, x_offset, '|', curses.color_pair(COLOR_UI_TEXT))
                stdscr.addch(
                    y_offset + y + 1,
                    x_offset + self.minimap_size + 1,
                    '|',
                    curses.color_pair(COLOR_UI_TEXT),
                )
            stdscr.addstr(
                y_offset + self.minimap_size + 1,
                x_offset,
                '+' + '-' * self.minimap_size + '+',
                curses.color_pair(COLOR_UI_TEXT)
            )
        except curses.error:
            pass

    def _draw_title(self, stdscr, x_offset, y_offset):
        mode_tag = 'L' if self.mode == self.MODE_LOCAL else 'G'
        title = f'MAP {mode_tag}'
        try:
            stdscr.addstr(
                y_offset,
                x_offset + max(1, (self.minimap_size - len(title)) // 2),
                title,
                curses.color_pair(COLOR_UI_HIGHLIGHT) | curses.A_BOLD,
            )
        except curses.error:
            pass

    def _draw_local_window(self, stdscr, level, camera, fog_of_war, x_offset, y_offset):
        cx = int(camera.x)
        cy = int(camera.y)
        half = self.minimap_size // 2
        world_span = (self.local_radius * 2) + 1
        sample_step = world_span / self.minimap_size

        for my in range(self.minimap_size):
            for mx in range(self.minimap_size):
                wx = cx + int(round((mx - half) * sample_step))
                wy = cy + int(round((my - half) * sample_step))
                char, color, attr = self._tile_style(level, fog_of_war, wx, wy)
                self._put(stdscr, x_offset, y_offset, mx, my, char, color, attr)

        self._draw_local_entities(stdscr, level, fog_of_war, cx, cy, half, sample_step, x_offset, y_offset)

        # Exit marker in local coordinates.
        if getattr(level, 'exit_position', None):
            ex, ey = level.exit_position
            mx, my = self._world_to_local_map(cx, cy, half, sample_step, ex, ey)
            if 0 <= mx < self.minimap_size and 0 <= my < self.minimap_size:
                if self._should_show_exit(level, fog_of_war):
                    self._put(
                        stdscr, x_offset, y_offset, mx, my,
                        self.EXIT_CHAR, COLOR_EXIT, curses.A_BOLD,
                    )

        self._draw_player_local(stdscr, camera, x_offset, y_offset)

    def _draw_global_window(self, stdscr, level, camera, fog_of_war, x_offset, y_offset):
        for my in range(self.minimap_size):
            for mx in range(self.minimap_size):
                wx = min(self.map_width - 1, max(0, int((mx + 0.5) * self.scale_x)))
                wy = min(self.map_height - 1, max(0, int((my + 0.5) * self.scale_y)))
                char, color, attr = self._tile_style(level, fog_of_war, wx, wy)
                self._put(stdscr, x_offset, y_offset, mx, my, char, color, attr)

        if getattr(level, 'exit_position', None) and self._should_show_exit(level, fog_of_war):
            ex, ey = level.exit_position
            mx = int(ex / self.scale_x)
            my = int(ey / self.scale_y)
            if 0 <= mx < self.minimap_size and 0 <= my < self.minimap_size:
                self._put(stdscr, x_offset, y_offset, mx, my, self.EXIT_CHAR, COLOR_EXIT, curses.A_BOLD)

        self._draw_player_global(stdscr, camera, x_offset, y_offset)

    def _draw_player_local(self, stdscr, camera, x_offset, y_offset):
        half = self.minimap_size // 2
        self._put(stdscr, x_offset, y_offset, half, half, self.PLAYER_CHAR, COLOR_PLAYER, curses.A_BOLD)

    def _draw_player_global(self, stdscr, camera, x_offset, y_offset):
        mx = int(camera.x / self.scale_x)
        my = int(camera.y / self.scale_y)
        if 0 <= mx < self.minimap_size and 0 <= my < self.minimap_size:
            self._put(stdscr, x_offset, y_offset, mx, my, self.PLAYER_CHAR, COLOR_PLAYER, curses.A_BOLD)

    def _tile_style(self, level, fog_of_war, x, y):
        if x < 0 or y < 0 or x >= self.map_width or y >= self.map_height:
            return self.UNKNOWN_CHAR, COLOR_UI_TEXT, curses.A_DIM

        visible = True
        discovered = True
        if fog_of_war and self.show_discovered_only:
            visible = fog_of_war.is_tile_visible(x, y)
            discovered = self._is_tile_discovered(level, fog_of_war, x, y)

        if self.show_fog and not discovered:
            return self.UNKNOWN_CHAR, COLOR_UI_TEXT, curses.A_DIM

        if level.is_wall(x, y):
            char = self.WALL_CHAR
            color = COLOR_WALL
        elif level.is_walkable(x, y):
            corridor, _ = level.get_corridor_at(x, y)
            if corridor is not None:
                char = self.CORRIDOR_CHAR
                color = COLOR_CORRIDOR
            else:
                char = self.FLOOR_CHAR
                color = COLOR_FLOOR
        else:
            char = self.UNKNOWN_CHAR
            color = COLOR_UI_TEXT

        attr = curses.A_NORMAL
        if fog_of_war and self.show_discovered_only and not visible:
            attr |= curses.A_DIM
        return char, color, attr

    def _draw_local_entities(self, stdscr, level, fog_of_war, cx, cy, half, sample_step, x_offset, y_offset):
        if self.show_items:
            for item in self._iter_level_items(level):
                if not getattr(item, 'position', None):
                    continue
                ix, iy = item.position
                if not self._is_entity_visible(fog_of_war, ix, iy):
                    continue
                mx, my = self._world_to_local_map(cx, cy, half, sample_step, ix, iy)
                if 0 <= mx < self.minimap_size and 0 <= my < self.minimap_size:
                    char, color = get_item_render_data(item)
                    self._put(stdscr, x_offset, y_offset, mx, my, char, color, curses.A_BOLD)

        if self.show_enemies:
            for enemy in self._iter_level_enemies(level):
                if not getattr(enemy, 'position', None):
                    continue
                if hasattr(enemy, 'is_alive') and not enemy.is_alive():
                    continue
                if getattr(enemy, 'is_invisible', False):
                    continue
                ex, ey = enemy.position
                if not self._is_entity_visible(fog_of_war, ex, ey):
                    continue
                mx, my = self._world_to_local_map(cx, cy, half, sample_step, ex, ey)
                if 0 <= mx < self.minimap_size and 0 <= my < self.minimap_size:
                    self._put(
                        stdscr, x_offset, y_offset, mx, my,
                        getattr(enemy, 'char', 'e'),
                        get_enemy_color(getattr(enemy, 'char', 'e')),
                        curses.A_BOLD,
                    )

    @staticmethod
    def _iter_level_items(level):
        for room in getattr(level, 'rooms', []):
            for item in getattr(room, 'items', []):
                yield item

    @staticmethod
    def _iter_level_enemies(level):
        for room in getattr(level, 'rooms', []):
            for enemy in getattr(room, 'enemies', []):
                yield enemy

    def _is_entity_visible(self, fog_of_war, x, y):
        if not fog_of_war or not self.show_discovered_only:
            return True
        if hasattr(fog_of_war, 'is_position_visible'):
            return fog_of_war.is_position_visible(x, y)
        if hasattr(fog_of_war, 'is_tile_visible'):
            return fog_of_war.is_tile_visible(x, y)
        return True

    @staticmethod
    def _world_to_local_map(cx, cy, half, sample_step, wx, wy):
        mx = int(round(((wx - cx) / sample_step) + half))
        my = int(round(((wy - cy) / sample_step) + half))
        return mx, my

    @staticmethod
    def _is_tile_discovered(level, fog_of_war, x, y):
        room, room_idx = level.get_room_at(x, y)
        if room is not None:
            return fog_of_war.is_room_discovered(room_idx)

        corridor, corridor_idx = level.get_corridor_at(x, y)
        if corridor is not None:
            return fog_of_war.is_corridor_discovered(corridor_idx)

        return False

    @staticmethod
    def _direction_step(angle):
        # World coordinates: +X east, +Y south on terminal map.
        rad = math.radians(angle)
        dx = int(round(math.cos(rad)))
        dy = int(round(math.sin(rad)))
        if dx == 0 and dy == 0:
            return (1, 0)
        return (dx, dy)

    def _put(self, stdscr, x_offset, y_offset, mx, my, char, color, attr=0):
        try:
            stdscr.addch(
                y_offset + 1 + my,
                x_offset + 1 + mx,
                char,
                curses.color_pair(color) | attr,
            )
        except curses.error:
            pass

    def _should_show_exit(self, level, fog_of_war):
        if not getattr(level, 'exit_position', None):
            return False
        if fog_of_war and self.show_discovered_only:
            return fog_of_war.is_room_discovered(level.exit_room_index)
        return True

    def render_minimap_simple(self, stdscr, level, camera, x_offset=0, y_offset=0):
        """Render mini-map without fog restrictions."""
        self._draw_border(stdscr, x_offset, y_offset)
        prev_show = self.show_discovered_only
        try:
            self.show_discovered_only = False
            if self.mode == self.MODE_LOCAL:
                self._draw_local_window(stdscr, level, camera, None, x_offset, y_offset)
            else:
                self._draw_global_window(stdscr, level, camera, None, x_offset, y_offset)
            self._draw_title(stdscr, x_offset, y_offset)
        finally:
            self.show_discovered_only = prev_show

    def toggle_fog(self):
        self.show_fog = not self.show_fog
        return self.show_fog

    def toggle_discovered_only(self):
        self.show_discovered_only = not self.show_discovered_only
        return self.show_discovered_only

    def toggle_mode(self):
        self.mode = self.MODE_GLOBAL if self.mode == self.MODE_LOCAL else self.MODE_LOCAL
        return self.mode

    def set_local_radius(self, radius):
        self.local_radius = max(3, int(radius))

    def set_size(self, size):
        self.minimap_size = max(8, min(size, 20))
        self.scale_x = self.map_width / self.minimap_size
        self.scale_y = self.map_height / self.minimap_size
        self.local_radius = max(3, self.minimap_size // 2)
