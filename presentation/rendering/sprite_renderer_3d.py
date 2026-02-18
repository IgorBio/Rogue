"""
Sprite rendering for 3D mode.

Sprites (enemies, items, exit) are projected into screen space,
depth-tested against the z-buffer, and drawn as 3x3 character
glyphs with a semi-transparent outline.
"""
import math
import time
from typing import List, Optional


class Sprite:
    """A single entity to be rendered in 3D space."""

    __slots__ = (
        'x', 'y', 'char', 'color', 'sprite_type',
        'distance', 'screen_x', 'height',
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
        self.has_outline: bool = False
        self.outline_char: str = '░'


class SpriteRenderer:
    """Projects and draws sprites with z-buffering and outline glyphs."""

    def __init__(self, viewport_width: int, viewport_height: int,
                 fov: float = 60.0):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.fov = fov
        self.max_sprite_distance = 20.0
        self.sprite_base_height = 1.0

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def collect_sprites(self, level, fog_of_war=None) -> List[Sprite]:
        """
        Gather all visible sprites from the level.

        Args:
            level: Level object.
            fog_of_war: Optional FogOfWar used for visibility checks.

        Returns:
            List of Sprite objects.
        """
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
            enemy.position[0], enemy.position[1],
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
            item.position[0], item.position[1],
            char, color,
            sprite_type='item',
        )
        sprite.has_outline = True
        sprite.outline_char = '░'
        return sprite

    def _make_exit_sprite(self, position) -> Sprite:
        from presentation.colors import COLOR_EXIT
        sprite = Sprite(
            position[0], position[1],
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
        Compute screen_x, distance, and height for each sprite.

        Returns sprites that are in front of the camera, sorted
        farthest-first for correct painter's-algorithm ordering.
        """
        visible: List[Sprite] = []
        dx, dy = camera.get_direction_vector()
        right_x, right_y = -dy, dx

        half_w = self.viewport_width / 2
        proj_dist = half_w / math.tan(math.radians(self.fov / 2))

        for sprite in sprites:
            sx = sprite.x - camera.x
            sy = sprite.y - camera.y
            dist = math.sqrt(sx * sx + sy * sy)

            if dist > self.max_sprite_distance or dist < 0.1:
                continue

            forward = sx * dx + sy * dy
            if forward <= 0:
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
                int((base_h / dist) * self.viewport_height * 2),
                self.viewport_height,
            ))

            sprite.distance = dist
            sprite.screen_x = screen_x
            sprite.height = height
            visible.append(sprite)

        visible.sort(key=lambda s: s.distance, reverse=True)
        return visible

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_sprites(self, stdscr, sprites: List[Sprite], camera,
                       z_buffer: list, x_offset: int = 0,
                       y_offset: int = 0) -> None:
        """
        Draw all visible sprites onto the curses screen.

        Args:
            stdscr: Curses screen object.
            sprites: Projected sprites sorted farthest-first.
            camera: Camera (unused here, kept for API compatibility).
            z_buffer: Per-column wall distances from the wall renderer.
            x_offset: Viewport left edge on screen.
            y_offset: Viewport top edge on screen.
        """
        import curses

        center_y = self.viewport_height // 2

        for sprite in sprites:
            sx = sprite.screen_x
            if sx < 1 or sx >= self.viewport_width - 1:
                continue
            if sprite.distance >= z_buffer[sx]:
                continue

            char = self._shade_char(sprite.char, sprite.distance)
            color = curses.color_pair(sprite.color)
            if sprite.sprite_type == 'exit':
                color |= curses.A_BOLD
            elif sprite.sprite_type == 'item' and sprite.distance < 5.0:
                color |= curses.A_BOLD
            elif sprite.sprite_type == 'enemy' and sprite.distance < 3.0:
                color |= curses.A_BOLD

            if sprite.has_outline:
                ol = sprite.outline_char
                ol_color = curses.color_pair(sprite.color) | curses.A_DIM
                for ry, rx, ch, cl in (
                    (center_y - 1, sx - 1, ol, ol_color),
                    (center_y - 1, sx,     ol, ol_color),
                    (center_y - 1, sx + 1, ol, ol_color),
                    (center_y,     sx - 1, ol, ol_color),
                    (center_y,     sx,     char, color),
                    (center_y,     sx + 1, ol, ol_color),
                    (center_y + 1, sx - 1, ol, ol_color),
                    (center_y + 1, sx,     ol, ol_color),
                    (center_y + 1, sx + 1, ol, ol_color),
                ):
                    self._put(stdscr, ry, rx, ch, cl, y_offset, x_offset)
            else:
                self._put(stdscr, center_y, sx, char, color, y_offset, x_offset)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
