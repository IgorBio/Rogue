"""
Mini-map renderer for 3D mode navigation.
Shows scaled-down 2D overview with player position and orientation.
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
)


class MiniMapRenderer:
    """Renders a mini-map overlay for 3D mode."""
    
    def __init__(self, map_width, map_height, minimap_size=12):
        """
        Initialize mini-map renderer.
        
        Args:
            map_width: Full map width
            map_height: Full map height
            minimap_size: Size of mini-map in characters (width and height)
        """
        self.map_width = map_width
        self.map_height = map_height
        self.minimap_size = minimap_size
        
        # Calculate scale factors
        self.scale_x = map_width / minimap_size
        self.scale_y = map_height / minimap_size
        
        # Display options
        self.show_discovered_only = True
        self.show_fog = True
        self.show_enemies = False
        self.show_items = False
    
    def render_minimap(self, stdscr, level, camera, fog_of_war=None, 
                      x_offset=0, y_offset=0):
        """
        Render the mini-map.
        
        Args:
            stdscr: Curses screen object
            level: Level object
            camera: Camera object with position and angle
            fog_of_war: FogOfWar object (optional)
            x_offset: X position to render mini-map
            y_offset: Y position to render mini-map
        """
        # Draw border
        self._draw_border(stdscr, x_offset, y_offset)
        
        # Draw level elements
        self._draw_rooms(stdscr, level, fog_of_war, x_offset, y_offset)
        self._draw_corridors(stdscr, level, fog_of_war, x_offset, y_offset)
        self._draw_exit(stdscr, level, fog_of_war, x_offset, y_offset)
        
        # Draw player last (on top)
        self._draw_player(stdscr, camera, x_offset, y_offset)
        
        # Draw title
        self._draw_title(stdscr, x_offset, y_offset)
    
    def _draw_border(self, stdscr, x_offset, y_offset):
        """Draw border around mini-map."""
        # Top border
        try:
            stdscr.addstr(
                y_offset,
                x_offset,
                "┌" + "─" * self.minimap_size + "┐",
                curses.color_pair(COLOR_UI_TEXT)
            )
        except:
            from config.game_config import GameConfig
            self.map_width = GameConfig.MAP_WIDTH
            self.map_height = GameConfig.MAP_HEIGHT
        # Side borders
        for y in range(self.minimap_size):
            try:
                stdscr.addch(y_offset + y + 1, x_offset, '│', 
                           curses.color_pair(COLOR_UI_TEXT))
                stdscr.addch(y_offset + y + 1, x_offset + self.minimap_size + 1, '│',
                           curses.color_pair(COLOR_UI_TEXT))
            except:
                pass
        
        # Bottom border
        try:
            stdscr.addstr(
                y_offset + self.minimap_size + 1,
                x_offset,
                "└" + "─" * self.minimap_size + "┘",
                curses.color_pair(COLOR_UI_TEXT)
            )
        except:
            pass
    
    def _draw_title(self, stdscr, x_offset, y_offset):
        """Draw mini-map title."""
        title = "MAP"
        try:
            stdscr.addstr(
                y_offset,
                x_offset + (self.minimap_size - len(title)) // 2 + 1,
                title,
                curses.color_pair(COLOR_UI_HIGHLIGHT) | curses.A_BOLD
            )
        except:
            pass
    
    def _draw_rooms(self, stdscr, level, fog_of_war, x_offset, y_offset):
        """Draw rooms on mini-map."""
        for room_idx, room in enumerate(level.rooms):
            # Check if room should be visible
            if fog_of_war and self.show_discovered_only:
                if not fog_of_war.is_room_discovered(room_idx):
                    continue
            
            # Scale room coordinates
            scaled_x = int(room.x / self.scale_x)
            scaled_y = int(room.y / self.scale_y)
            scaled_width = max(1, int(room.width / self.scale_x))
            scaled_height = max(1, int(room.height / self.scale_y))
            
            # Determine if this is the current room
            is_current = False
            if fog_of_war:
                is_current = fog_of_war.is_room_current(room_idx)
            
            # Draw room
            char = '■' if is_current else '□'
            color = COLOR_UI_HIGHLIGHT if is_current else COLOR_WALL
            
            # Draw as single character or small rectangle
            for dy in range(scaled_height):
                for dx in range(scaled_width):
                    map_x = scaled_x + dx
                    map_y = scaled_y + dy
                    
                    if 0 <= map_x < self.minimap_size and 0 <= map_y < self.minimap_size:
                        try:
                            stdscr.addch(
                                y_offset + 1 + map_y,
                                x_offset + 1 + map_x,
                                char,
                                curses.color_pair(color)
                            )
                        except:
                            pass
    
    def _draw_corridors(self, stdscr, level, fog_of_war, x_offset, y_offset):
        """Draw corridors on mini-map."""
        for corridor_idx, corridor in enumerate(level.corridors):
            # Check if corridor should be visible
            if fog_of_war and self.show_discovered_only:
                if not fog_of_war.is_corridor_discovered(corridor_idx):
                    continue
            
            # Draw corridor tiles
            for tile_x, tile_y in corridor.tiles:
                scaled_x = int(tile_x / self.scale_x)
                scaled_y = int(tile_y / self.scale_y)
                
                if 0 <= scaled_x < self.minimap_size and 0 <= scaled_y < self.minimap_size:
                    try:
                        stdscr.addch(
                            y_offset + 1 + scaled_y,
                            x_offset + 1 + scaled_x,
                            '·',
                            curses.color_pair(COLOR_CORRIDOR)
                        )
                    except:
                        pass
    
    def _draw_exit(self, stdscr, level, fog_of_war, x_offset, y_offset):
        """Draw exit marker on mini-map."""
        if not level.exit_position:
            return
        
        # Check if exit room is discovered
        if fog_of_war and self.show_discovered_only:
            if not fog_of_war.is_room_discovered(level.exit_room_index):
                return
        
        exit_x, exit_y = level.exit_position
        scaled_x = int(exit_x / self.scale_x)
        scaled_y = int(exit_y / self.scale_y)
        
        if 0 <= scaled_x < self.minimap_size and 0 <= scaled_y < self.minimap_size:
            try:
                stdscr.addch(
                    y_offset + 1 + scaled_y,
                    x_offset + 1 + scaled_x,
                    '>',
                    curses.color_pair(COLOR_EXIT) | curses.A_BOLD
                )
            except:
                pass
    
    def _draw_player(self, stdscr, camera, x_offset, y_offset):
        """Draw player position and facing direction."""
        # Scale player position
        scaled_x = int(camera.x / self.scale_x)
        scaled_y = int(camera.y / self.scale_y)
        
        if 0 <= scaled_x < self.minimap_size and 0 <= scaled_y < self.minimap_size:
            # Get direction arrow
            arrow = self._get_direction_arrow(camera.angle)
            
            try:
                stdscr.addch(
                    y_offset + 1 + scaled_y,
                    x_offset + 1 + scaled_x,
                    arrow,
                    curses.color_pair(COLOR_PLAYER) | curses.A_BOLD
                )
            except:
                pass
    
    def _get_direction_arrow(self, angle):
        """
        Get arrow character for direction.
        
        Args:
            angle: Angle in degrees
        
        Returns:
            Arrow character
        """
        angle = angle % 360
        
        # 8-direction arrows
        if angle < 22.5 or angle >= 337.5:
            return '→'
        elif angle < 67.5:
            return '↗'
        elif angle < 112.5:
            return '↑'
        elif angle < 157.5:
            return '↖'
        elif angle < 202.5:
            return '←'
        elif angle < 247.5:
            return '↙'
        elif angle < 292.5:
            return '↓'
        elif angle < 337.5:
            return '↘'
        
        return '@'
    
    def render_minimap_simple(self, stdscr, level, camera, x_offset=0, y_offset=0):
        """
        Render simplified mini-map (no fog of war).
        Shows entire level for testing/debugging.
        
        Args:
            stdscr: Curses screen object
            level: Level object
            camera: Camera object
            x_offset: X position
            y_offset: Y position
        """
        self._draw_border(stdscr, x_offset, y_offset)
        
        # Draw all rooms (simplified)
        for room in level.rooms:
            scaled_x = int(room.x / self.scale_x)
            scaled_y = int(room.y / self.scale_y)
            scaled_width = max(1, int(room.width / self.scale_x))
            scaled_height = max(1, int(room.height / self.scale_y))
            
            for dy in range(scaled_height):
                for dx in range(scaled_width):
                    map_x = scaled_x + dx
                    map_y = scaled_y + dy
                    
                    if 0 <= map_x < self.minimap_size and 0 <= map_y < self.minimap_size:
                        try:
                            stdscr.addch(
                                y_offset + 1 + map_y,
                                x_offset + 1 + map_x,
                                '□',
                                curses.color_pair(COLOR_WALL)
                            )
                        except:
                            pass
        
        # Draw player
        self._draw_player(stdscr, camera, x_offset, y_offset)
        self._draw_title(stdscr, x_offset, y_offset)
    
    def toggle_fog(self):
        """Toggle fog of war display."""
        self.show_fog = not self.show_fog
        return self.show_fog
    
    def toggle_discovered_only(self):
        """Toggle showing only discovered areas."""
        self.show_discovered_only = not self.show_discovered_only
        return self.show_discovered_only
    
    def set_size(self, size):
        """
        Change mini-map size.
        
        Args:
            size: New size in characters
        """
        self.minimap_size = max(8, min(size, 20))
        self.scale_x = self.map_width / self.minimap_size
        self.scale_y = self.map_height / self.minimap_size


def test_minimap():
    """Test mini-map rendering."""
    print("=" * 60)
    print("MINI-MAP RENDERER TEST")
    print("=" * 60)
    
    from config.game_config import GameConfig

    # Create mini-map renderer
    minimap = MiniMapRenderer(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT, minimap_size=12)

    print(f"\nMini-map Configuration:")
    print(f"  Full map size: {GameConfig.MAP_WIDTH}x{GameConfig.MAP_HEIGHT}")
    print(f"  Mini-map size: {minimap.minimap_size}x{minimap.minimap_size}")
    print(f"  Scale X: {minimap.scale_x:.2f}")
    print(f"  Scale Y: {minimap.scale_y:.2f}")
    
    # Test coordinate scaling
    print(f"\n" + "=" * 60)
    print("COORDINATE SCALING TEST")
    print("=" * 60)
    
    test_coords = [
        (0, 0, "Top-left corner"),
        (GameConfig.MAP_WIDTH // 2, GameConfig.MAP_HEIGHT // 2, "Center"),
        (GameConfig.MAP_WIDTH - 1, GameConfig.MAP_HEIGHT - 1, "Bottom-right corner"),
        (10, 10, "Room position"),
    ]
    
    print("\n  World Coord    | Mini-map Coord | Description")
    print("  ---------------|----------------|------------------")
    
    for x, y, desc in test_coords:
        scaled_x = int(x / minimap.scale_x)
        scaled_y = int(y / minimap.scale_y)
        print(f"  ({x:3d}, {y:3d})    | ({scaled_x:2d}, {scaled_y:2d})        | {desc}")
    
    # Test direction arrows
    print(f"\n" + "=" * 60)
    print("DIRECTION ARROWS TEST")
    print("=" * 60)
    
    print("\n  Angle | Arrow | Direction")
    print("  ------|-------|------------------")
    
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        arrow = minimap._get_direction_arrow(angle)
        print(f"  {angle:3d}°  | {arrow}    |")
    
    # Test size adjustment
    print(f"\n" + "=" * 60)
    print("SIZE ADJUSTMENT TEST")
    print("=" * 60)
    
    print(f"\nOriginal size: {minimap.minimap_size}x{minimap.minimap_size}")
    
    minimap.set_size(16)
    print(f"After set_size(16): {minimap.minimap_size}x{minimap.minimap_size}")
    print(f"  New scale X: {minimap.scale_x:.2f}")
    print(f"  New scale Y: {minimap.scale_y:.2f}")
    
    minimap.set_size(8)
    print(f"After set_size(8): {minimap.minimap_size}x{minimap.minimap_size}")
    print(f"  New scale X: {minimap.scale_x:.2f}")
    print(f"  New scale Y: {minimap.scale_y:.2f}")
    
    # Test toggles
    print(f"\n" + "=" * 60)
    print("FEATURE TOGGLES TEST")
    print("=" * 60)
    
    print(f"\nShow fog: {minimap.show_fog}")
    minimap.toggle_fog()
    print(f"After toggle_fog(): {minimap.show_fog}")
    
    print(f"\nShow discovered only: {minimap.show_discovered_only}")
    minimap.toggle_discovered_only()
    print(f"After toggle_discovered_only(): {minimap.show_discovered_only}")
    
    print("\n✓ Mini-map renderer tests complete!")


if __name__ == "__main__":
    test_minimap()
