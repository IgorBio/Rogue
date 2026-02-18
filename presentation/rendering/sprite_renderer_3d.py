"""
Sprite rendering for 3D mode.

Sprites (enemies, items, exit) are projected into screen space,
depth-tested against the z-buffer, and drawn as scaled billboards.
"""
import math
from typing import List


class Sprite:
    """A single entity to be rendered in 3D space."""

    __slots__ = (
        'x', 'y', 'char', 'color', 'sprite_type',
        'distance', 'screen_x',
        'height', 'width', 'top_y', 'bottom_y',
        'has_outline', 'outline_char',
    )

    def __init__(self, x: float, y: float, char: str,
                 color: int, sprite_type: str = 'entity'):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.sprite_type = sprite_type
        self.distance: float = 0.0
        self.screen_x: int = 0
        self.height: int = 0
        self.width: int = 0
        self.top_y: int = 0
        self.bottom_y: int = 0
        self.has_outline: bool = False
        self.outline_char: str = '░'


class SpriteRenderer:
    """Projects and draws sprites with z-buffering and outline glyphs."""

    # Items within this world-unit distance get a z-bias so they are not
    # hidden by the immediately adjacent wall surface in corners.
    _ITEM_CLOSE_DIST = 1.5
    _ITEM_Z_BIAS = 0.3
    _ITEM_Z_BIAS_MAX_RATIO = 0.10

    def __init__(self, viewport_width: int, viewport_height: int,
                 fov: float = 60.0):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.fov = fov
        self.max_sprite_distance = 20.0
        self.sprite_base_height = 1.0

    def sync_projection(self, viewport_width: int, viewport_height: int,
                        fov: float) -> None:
        """Synchronize sprite projection parameters with active camera/view."""
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.fov = max(1.0, float(fov))

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def collect_sprites(self, level, fog_of_war=None) -> List[Sprite]:
        """Gather all visible sprites from the level."""
        sprites: List[Sprite] = []

        for room in level.rooms:
            for enemy in room.enemies:
                if not enemy.is_alive():
                    continue
                ex, ey = enemy.position
                if fog_of_war and not fog_of_war.is_position_visible(ex, ey):
                    continue
                sprites.append(self._make_enemy_sprite(enemy))

        for room in level.rooms:
            for item in room.items:
                if not item.position:
                    continue
                ix, iy = item.position
                if fog_of_war and not fog_of_war.is_position_visible(ix, iy):
                    continue
                sprites.append(self._make_item_sprite(item))

        if level.exit_position:
            visible = (
                not fog_of_war
                or fog_of_war.is_room_discovered(level.exit_room_index)
            )
            if visible:
                sprites.append(self._make_exit_sprite(level.exit_position))

        return sprites

    # ------------------------------------------------------------------
    # Sprite factories
    # ------------------------------------------------------------------

    def _make_enemy_sprite(self, enemy) -> Sprite:
        from presentation.colors import get_enemy_color

        sprite = Sprite(
            enemy.position[0] + 0.5, enemy.position[1] + 0.5,
            enemy.char.upper(),
            get_enemy_color(enemy.char),
            sprite_type='enemy',
        )
        sprite.has_outline = True
        sprite.outline_char = '░'
        return sprite

    def _make_item_sprite(self, item) -> Sprite:
        from presentation.rendering.item_rendering import get_item_render_data

        char, color = get_item_render_data(item)
        sprite = Sprite(
            item.position[0] + 0.5, item.position[1] + 0.5,
            char, color,
            sprite_type='item',
        )
        sprite.has_outline = True
        sprite.outline_char = '░'
        return sprite

    def _make_exit_sprite(self, position) -> Sprite:
        from presentation.colors import COLOR_EXIT

        sprite = Sprite(
            position[0] + 0.5, position[1] + 0.5,
            '>', COLOR_EXIT,
            sprite_type='exit',
        )
        sprite.has_outline = True
        sprite.outline_char = '▒'
        return sprite

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def calculate_sprite_positions(self, sprites: List[Sprite],
                                   camera) -> List[Sprite]:
        """
        Compute sprite screen position and scaled billboard size.

        Size is based on forward (perpendicular-to-screen) distance,
        which matches the wall projection geometry.
        """
        visible: List[Sprite] = []
        dx, dy = camera.get_direction_vector()
        right_x, right_y = -dy, dx

        half_w = self.viewport_width / 2
        proj_dist = half_w / math.tan(math.radians(self.fov / 2))
        horizon_y = self.viewport_height // 2

        for sprite in sprites:
            sx = sprite.x - camera.x
            sy = sprite.y - camera.y
            dist = math.sqrt(sx * sx + sy * sy)

            if dist > self.max_sprite_distance or dist < 0.1:
                continue

            forward = sx * dx + sy * dy
            if forward <= 0.05:
                continue

            lateral = sx * right_x + sy * right_y
            screen_x = int((lateral / forward) * proj_dist + half_w)

            if sprite.sprite_type == 'enemy':
                base_h, min_h = self.sprite_base_height * 1.2, 3
            elif sprite.sprite_type == 'exit':
                base_h, min_h = self.sprite_base_height * 1.5, 3
            else:
                base_h, min_h = self.sprite_base_height * 0.8, 2

            height = max(min_h, min(
                int((base_h / forward) * self.viewport_height * 2),
                self.viewport_height,
            ))
            width = max(2, min(int(height * 0.6), self.viewport_width // 2))

            bottom_y = horizon_y + (height // 2)
            top_y = bottom_y - height + 1

            sprite.distance = forward
            sprite.screen_x = screen_x
            sprite.height = height
            sprite.width = width
            sprite.top_y = top_y
            sprite.bottom_y = bottom_y
            visible.append(sprite)

        visible.sort(key=lambda s: s.distance, reverse=True)
        return visible

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_sprites(self, stdscr, sprites: List[Sprite], camera,
                       z_buffer: list, x_offset: int = 0,
                       y_offset: int = 0) -> None:
        """Draw all visible sprites onto the curses screen."""
        import curses

        for sprite in sprites:
            sx = sprite.screen_x
            half_w = sprite.width // 2
            left_x = sx - half_w
            right_x = left_x + sprite.width - 1

            if right_x < 0 or left_x >= self.viewport_width:
                continue

            effective_dist = self._effective_sprite_distance(sprite)

            cols_to_check = [
                c for c in range(left_x, right_x + 1)
                if 0 <= c < self.viewport_width
            ]
            if not cols_to_check:
                continue
            if not any(effective_dist < z_buffer[c] for c in cols_to_check):
                continue

            char = self._shade_char(sprite.char, sprite.distance)
            color = curses.color_pair(sprite.color)
            if sprite.sprite_type == 'exit':
                color |= curses.A_BOLD
            elif sprite.sprite_type == 'item' and sprite.distance < 5.0:
                color |= curses.A_BOLD
            elif sprite.sprite_type == 'enemy' and sprite.distance < 3.0:
                color |= curses.A_BOLD

            y_start = max(0, sprite.top_y)
            y_end = min(self.viewport_height - 1, sprite.bottom_y)
            x_start = max(0, left_x)
            x_end = min(self.viewport_width - 1, right_x)

            if y_start > y_end or x_start > x_end:
                continue

            if sprite.has_outline:
                outline_color = curses.color_pair(sprite.color) | curses.A_DIM
                for ry in range(y_start, y_end + 1):
                    for rx in range(x_start, x_end + 1):
                        if not self._passes_depth_test(effective_dist, rx, z_buffer):
                            continue
                        on_border = (
                            ry == sprite.top_y or ry == sprite.bottom_y
                            or rx == left_x or rx == right_x
                        )
                        if on_border:
                            self._put(stdscr, ry, rx, sprite.outline_char,
                                      outline_color, y_offset, x_offset)
                        else:
                            self._put(stdscr, ry, rx, char, color, y_offset, x_offset)
            else:
                for ry in range(y_start, y_end + 1):
                    for rx in range(x_start, x_end + 1):
                        if not self._passes_depth_test(effective_dist, rx, z_buffer):
                            continue
                        self._put(stdscr, ry, rx, char, color, y_offset, x_offset)

            # Keep a strong readable center glyph for target acquisition.
            center_y = (sprite.top_y + sprite.bottom_y) // 2
            if self._passes_depth_test(effective_dist, sx, z_buffer):
                self._put(stdscr, center_y, sx, char, color, y_offset, x_offset)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _effective_sprite_distance(self, sprite: Sprite) -> float:
        """Apply a bounded bias for close items to reduce corner occlusion artifacts."""
        if sprite.sprite_type != 'item' or sprite.distance >= self._ITEM_CLOSE_DIST:
            return sprite.distance
        max_bias = max(0.05, sprite.distance * self._ITEM_Z_BIAS_MAX_RATIO)
        return sprite.distance + min(self._ITEM_Z_BIAS, max_bias)

    @staticmethod
    def _passes_depth_test(distance: float, x: int, z_buffer: list) -> bool:
        if x < 0 or x >= len(z_buffer):
            return False
        return distance < z_buffer[x]

    def _put(self, stdscr, rel_y: int, rel_x: int, char: str,
             color, y_offset: int, x_offset: int) -> None:
        import curses

        if 0 <= rel_y < self.viewport_height and 0 <= rel_x < self.viewport_width:
            try:
                stdscr.addch(y_offset + rel_y, x_offset + rel_x, char, color)
            except curses.error:
                pass

    @staticmethod
    def _shade_char(char: str, distance: float) -> str:
        if distance < 3.0:
            return char
        if distance < 6.0:
            return char.lower() if char.isalpha() else char
        if distance < 10.0:
            if char.isalpha():
                return char.lower()
            return {'%': 'o', '$': 'o', '(': 'c', '!': 'i',
                    '?': '.', 'k': '.', '>': '.'}.get(char, char)
        if distance < 15.0:
            return '·'
        return ' '
