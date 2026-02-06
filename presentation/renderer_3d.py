"""
3D Renderer for first-person perspective.
FIXED: Z-buffer now properly updates and sprites render correctly.
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
    COLOR_WALL,
    COLOR_FLOOR,
    COLOR_CORRIDOR,
    COLOR_UI_TEXT,
)
from config.game_config import GameConfig


class Renderer3D:
    """Handles 3D first-person rendering."""
    
    # Shading characters from bright to dark
    SHADE_CHARS = ['█', '▓', '▒', '░', '·', ' ']
    
    # Distance thresholds for shading
    SHADE_DISTANCES = [2.0, 4.0, 7.0, 11.0, 16.0, 20.0]
    
    def __init__(self, stdscr, viewport_width=None, viewport_height=None, use_textures=True, show_minimap=True, show_sprites=True):
        """
        Initialize 3D renderer.
        
        Args:
            stdscr: Curses screen object
            viewport_width: Width of 3D viewport in characters
            viewport_height: Height of 3D viewport in characters
            use_textures: Enable texture rendering (vs simple shading)
            show_minimap: Enable mini-map overlay
            show_sprites: Enable sprite rendering (enemies/items)
        """
        self.stdscr = stdscr
        if viewport_width is None or viewport_height is None:
            max_y, max_x = stdscr.getmaxyx()
            viewport_width = min(70, max(10, max_x - 3))
            viewport_height = min(20, max(8, max_y - 10))

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.num_rays = viewport_width  # One ray per column
        self.use_textures = use_textures
        self.show_minimap = show_minimap
        self.show_sprites = show_sprites
        
        # Initialize colors if not already done
        if curses.has_colors():
            curses.start_color()
            init_colors()
        
        # Initialize texture system
        self.texture_manager = get_texture_manager()
        self.textured_renderer = TexturedRenderer(self.texture_manager)
        
        # Initialize mini-map
        self.minimap = MiniMapRenderer(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT, minimap_size=12)
        
        # Initialize sprite renderer
        self.sprite_renderer = SpriteRenderer(viewport_width, viewport_height, fov=60.0)
        
        # Z-buffer for sprite occlusion (reset each frame)
        self.z_buffer = [float('inf')] * viewport_width
        
        # Cache for performance
        self._shade_cache = {}

    def set_viewport(self, viewport_width: int, viewport_height: int) -> None:
        """Update viewport size and resize dependent buffers/renderers."""
        if viewport_width <= 0 or viewport_height <= 0:
            return
        if viewport_width == self.viewport_width and viewport_height == self.viewport_height:
            return

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.num_rays = viewport_width
        self.sprite_renderer = SpriteRenderer(viewport_width, viewport_height, fov=60.0)
        self.z_buffer = [float('inf')] * viewport_width
    
    def render_3d_view(self, camera, level, fog_of_war=None, x_offset=0, y_offset=0):
        """
        Render the 3D first-person view with sprites and optional mini-map.
        FIXED: Now properly updates Z-buffer and renders sprites.
        
        Args:
            camera: Camera object with position and orientation
            level: Level object for ray casting
            fog_of_war: FogOfWar object (optional)
            x_offset: X position to start rendering
            y_offset: Y position to start rendering
        """
        # FIXED: Reset Z-buffer at start of each frame
        self.z_buffer = [float('inf')] * self.viewport_width
        
        # Cast rays across FOV
        ray_hits = cast_fov_rays(camera, level, num_rays=self.num_rays)
        
        # Render each column and update Z-buffer
        for column in range(self.viewport_width):
            hit = ray_hits[column] if column < len(ray_hits) else None
            
            if hit:
                # FIXED: Update Z-buffer with wall distance
                self.z_buffer[column] = hit.distance
                self._render_wall_column(column, hit, x_offset, y_offset)
            else:
                # No wall hit - render empty column
                self._render_empty_column(column, x_offset, y_offset)
        
        # FIXED: Render sprites after walls (using Z-buffer for occlusion)
        if self.show_sprites:
            sprites = self.sprite_renderer.collect_sprites(level, fog_of_war)
            visible_sprites = self.sprite_renderer.calculate_sprite_positions(sprites, camera)
            self.sprite_renderer.render_sprites(
                self.stdscr, visible_sprites, camera, self.z_buffer,
                x_offset=x_offset, y_offset=y_offset
            )
        
        # Render mini-map overlay (top-right corner)
        if self.show_minimap:
            minimap_x = x_offset + self.viewport_width - self.minimap.minimap_size - 3
            minimap_y = y_offset + 1
            
            self.minimap.render_minimap(
                self.stdscr,
                level,
                camera,
                fog_of_war,
                x_offset=minimap_x,
                y_offset=minimap_y
            )
    
    def _render_wall_column(self, column, hit, x_offset, y_offset):
        """Render a single vertical wall column with textures."""
        # Calculate wall height on screen
        wall_height = calculate_wall_height(
            hit.distance, 
            self.viewport_height,
            wall_unit_size=1.0
        )
        
        # Calculate top and bottom of wall
        wall_top = (self.viewport_height - wall_height) // 2
        wall_bottom = wall_top + wall_height
        
        # Clamp to viewport
        wall_top = max(0, wall_top)
        wall_bottom = min(self.viewport_height, wall_bottom)
        
        # Get color based on wall type
        color = self._get_wall_color(hit.wall_type, hit.side)
        
        # Render ceiling (above wall)
        for y in range(wall_top):
            self._draw_char(
                y_offset + y,
                x_offset + column,
                ' ',
                COLOR_UI_TEXT
            )
        
        # Render wall with textures
        if self.use_textures:
            for y in range(wall_top, wall_bottom):
                # Calculate texture Y coordinate (0.0 - 1.0)
                if wall_height > 0:
                    texture_y = (y - wall_top) / wall_height
                else:
                    texture_y = 0.0
                
                # Get textured character
                char = self.textured_renderer.get_wall_char(
                    hit.wall_type,
                    hit.texture_x,
                    texture_y,
                    hit.distance
                )
                
                self._draw_char(
                    y_offset + y,
                    x_offset + column,
                    char,
                    color
                )
        else:
            # Fallback to simple shading
            shade_char = self._get_shade_char(hit.distance)
            
            for y in range(wall_top, wall_bottom):
                self._draw_char(
                    y_offset + y,
                    x_offset + column,
                    shade_char,
                    color
                )
        
        # Render floor (below wall)
        floor_char = self._get_floor_char(wall_bottom, self.viewport_height)
        for y in range(wall_bottom, self.viewport_height):
            self._draw_char(
                y_offset + y,
                x_offset + column,
                floor_char,
                COLOR_FLOOR
            )
    
    def _render_empty_column(self, column, x_offset, y_offset):
        """Render an empty column (no wall hit)."""
        # Render ceiling
        for y in range(self.viewport_height // 2):
            self._draw_char(
                y_offset + y,
                x_offset + column,
                ' ',
                COLOR_UI_TEXT
            )
        
        # Render floor
        for y in range(self.viewport_height // 2, self.viewport_height):
            self._draw_char(
                y_offset + y,
                x_offset + column,
                '.',
                COLOR_FLOOR
            )
    
    def _get_shade_char(self, distance):
        """Get shading character based on distance."""
        # Use cache for performance
        distance_key = int(distance * 10)  # Round to 0.1
        
        if distance_key in self._shade_cache:
            return self._shade_cache[distance_key]
        
        # Determine shade based on distance thresholds
        for i, threshold in enumerate(self.SHADE_DISTANCES):
            if distance < threshold:
                char = self.SHADE_CHARS[i]
                self._shade_cache[distance_key] = char
                return char
        
        # Very far - darkest shade
        char = self.SHADE_CHARS[-1]
        self._shade_cache[distance_key] = char
        return char
    
    def _get_wall_color(self, wall_type, side):
        """Get color for wall based on type and side."""
        if wall_type == 'corridor_wall':
            return COLOR_CORRIDOR
        elif wall_type == 'door':
            return COLOR_WALL
        else:
            return COLOR_WALL
    
    def _get_floor_char(self, wall_bottom, viewport_height):
        """Get character for floor based on distance from camera."""
        distance_from_center = abs(wall_bottom - (viewport_height / 2))
        
        if distance_from_center < 2:
            return '·'
        elif distance_from_center < 5:
            return '.'
        else:
            return ' '
    
    def _draw_char(self, y, x, char, color_pair):
        """Safely draw a character at given position."""
        try:
            self.stdscr.addch(y, x, char, curses.color_pair(color_pair))
        except curses.error:
            pass
    
    def render_viewport_border(self, x_offset=0, y_offset=0):
        """Render a border around the 3D viewport."""
        # Top border
        self._draw_string(
            y_offset - 1,
            x_offset,
            "┌" + "─" * self.viewport_width + "┐",
            COLOR_UI_TEXT
        )
        
        # Bottom border
        self._draw_string(
            y_offset + self.viewport_height,
            x_offset,
            "└" + "─" * self.viewport_width + "┘",
            COLOR_UI_TEXT
        )
        
        # Side borders
        for y in range(self.viewport_height):
            self._draw_char(y_offset + y, x_offset - 1, '│', COLOR_UI_TEXT)
            self._draw_char(
                y_offset + y,
                x_offset + self.viewport_width,
                '│',
                COLOR_UI_TEXT
            )
    
    def _draw_string(self, y, x, string, color_pair):
        """Safely draw a string at given position."""
        try:
            self.stdscr.addstr(y, x, string, curses.color_pair(color_pair))
        except curses.error:
            pass
    
    def render_mode_indicator(self, y_offset=0):
        """Render an indicator showing 3D mode is active."""
        mode_text = "[ 3D MODE - TEXTURED ]" if self.use_textures else "[ 3D MODE ]"
        indicator = mode_text
        self._draw_string(
            y_offset,
            (self.viewport_width - len(indicator)) // 2,
            indicator,
            COLOR_UI_TEXT
        )
    
    def render_camera_info(self, camera, x_offset=0, y_offset=0):
        """Render camera information for debugging."""
        info_lines = [
            f"Position: ({camera.x:.1f}, {camera.y:.1f})",
            f"Angle: {camera.angle:.0f}°",
            f"FOV: {camera.fov:.0f}°",
            f"Textures: {'ON' if self.use_textures else 'OFF'}",
            f"Mini-map: {'ON' if self.show_minimap else 'OFF'}",
            f"Sprites: {'ON' if self.show_sprites else 'OFF'}",
        ]
        
        for i, line in enumerate(info_lines):
            self._draw_string(
                y_offset + i,
                x_offset,
                line,
                COLOR_UI_TEXT
            )
    
    def toggle_minimap(self):
        """Toggle mini-map display."""
        self.show_minimap = not self.show_minimap
        return self.show_minimap
    
    def toggle_sprites(self):
        """Toggle sprite rendering."""
        self.show_sprites = not self.show_sprites
        return self.show_sprites
    
    def clear_viewport(self, x_offset=0, y_offset=0):
        """Clear the viewport area."""
        for y in range(self.viewport_height):
            for x in range(self.viewport_width):
                self._draw_char(y_offset + y, x_offset + x, ' ', COLOR_UI_TEXT)
