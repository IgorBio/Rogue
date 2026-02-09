"""
Sprite rendering system for 3D mode.
Renders enemies, items, and other entities in 3D space.
"""
import math
from typing import List, Tuple, Optional


class Sprite:
    """Represents an entity to be rendered as a sprite in 3D."""
    
    def __init__(self, x, y, char, color, sprite_type='entity'):
        """
        Initialize sprite.
        
        Args:
            x: World X position
            y: World Y position
            char: Character to display
            color: Color pair ID
            sprite_type: Type of sprite ('enemy', 'item', 'exit', etc.)
        """
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.sprite_type = sprite_type
        self.distance = 0.0  # Distance from camera (calculated during render)
        self.screen_x = 0    # Screen column position
        self.height = 0      # Height on screen


class SpriteRenderer:
    """Handles rendering of sprites in 3D space."""
    
    def __init__(self, viewport_width, viewport_height, fov=60.0):
        """
        Initialize sprite renderer.
        
        Args:
            viewport_width: Width of viewport in characters
            viewport_height: Height of viewport in characters
            fov: Field of view in degrees
        """
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.fov = fov
        
        # Sprite rendering constants
        self.sprite_base_height = 1.0  # Height of sprite in world units
        self.max_sprite_distance = 20.0  # Don't render sprites beyond this
        self.sprite_width = 3  # Sprite width in screen columns
    
    def collect_sprites(self, level, fog_of_war=None):
        """
        Collect all visible sprites from the level.
        
        Args:
            level: Level object
            fog_of_war: FogOfWar object (optional)
        
        Returns:
            List of Sprite objects
        """
        sprites = []
        
        # Collect enemies
        for room in level.rooms:
            for enemy in room.enemies:
                if not enemy.is_alive():
                    continue
                
                # Check visibility
                if fog_of_war:
                    ex, ey = enemy.position
                    if not fog_of_war.is_position_visible(ex, ey):
                        continue
                
                # Get enemy color
                from presentation.colors import get_enemy_color
                color = get_enemy_color(enemy.char)
                
                sprite = Sprite(
                    enemy.position[0],
                    enemy.position[1],
                    enemy.char,
                    color,
                    sprite_type='enemy'
                )
                sprites.append(sprite)
        
        # Collect items
        for room in level.rooms:
            for item in room.items:
                if not item.position:
                    continue
                
                # Check visibility
                if fog_of_war:
                    ix, iy = item.position
                    if not fog_of_war.is_position_visible(ix, iy):
                        continue
                
                # Get item character and color
                from presentation.rendering.item_rendering import get_item_render_data
                item_char, color = get_item_render_data(item)
                
                sprite = Sprite(
                    item.position[0],
                    item.position[1],
                    item_char,
                    color,
                    sprite_type='item'
                )
                sprites.append(sprite)
        
        # Collect exit
        if level.exit_position:
            if fog_of_war:
                if fog_of_war.is_room_discovered(level.exit_room_index):
                    from presentation.colors import COLOR_EXIT
                    sprite = Sprite(
                        level.exit_position[0],
                        level.exit_position[1],
                        '>',
                        COLOR_EXIT,
                        sprite_type='exit'
                    )
                    sprites.append(sprite)
            else:
                from presentation.colors import COLOR_EXIT
                sprite = Sprite(
                    level.exit_position[0],
                    level.exit_position[1],
                    '>',
                    COLOR_EXIT,
                    sprite_type='exit'
                )
                sprites.append(sprite)
        
        return sprites
    
    def calculate_sprite_positions(self, sprites, camera):
        """
        Calculate screen positions for all sprites.
        
        Args:
            sprites: List of Sprite objects
            camera: Camera object
        
        Returns:
            List of sprites that should be rendered (sorted by distance)
        """
        visible_sprites = []
        
        # Camera basis vectors
        dx, dy = camera.get_direction_vector()
        right_x, right_y = -dy, dx

        for sprite in sprites:
            # Calculate relative position to camera
            sprite_x = sprite.x - camera.x
            sprite_y = sprite.y - camera.y
            
            # Calculate distance
            distance = math.sqrt(sprite_x**2 + sprite_y**2)
            
            # Skip if too far
            if distance > self.max_sprite_distance or distance < 0.1:
                continue
            
            # Transform to camera space using forward/right basis
            transformed_y = (sprite_x * dx) + (sprite_y * dy)  # forward
            transformed_x = (sprite_x * right_x) + (sprite_y * right_y)  # right
            
            # Check if sprite is in front of camera
            if transformed_y <= 0:
                continue
            
            # Calculate screen position
            # Project to screen using perspective division
            fov_rad = math.radians(self.fov)
            projection_plane_distance = (self.viewport_width / 2) / math.tan(fov_rad / 2)
            
            screen_x = int((transformed_x / transformed_y) * projection_plane_distance + self.viewport_width / 2)
            
            # Calculate sprite height based on distance and type
            if sprite.sprite_type == 'enemy':
                base_height = self.sprite_base_height * 1.0
                min_height = 3
            elif sprite.sprite_type == 'item':
                base_height = self.sprite_base_height * 0.8
                min_height = 2
            elif sprite.sprite_type == 'exit':
                base_height = self.sprite_base_height * 0.9
                min_height = 2
            else:
                base_height = self.sprite_base_height
                min_height = 1

            sprite_height = int((base_height / distance) * self.viewport_height * 2)
            sprite_height = max(min_height, min(sprite_height, self.viewport_height))
            
            # Store calculated values
            sprite.distance = distance
            sprite.screen_x = screen_x
            sprite.height = sprite_height
            
            visible_sprites.append(sprite)
        
        # Sort by distance (furthest first for proper occlusion)
        visible_sprites.sort(key=lambda s: s.distance, reverse=True)
        
        return visible_sprites
    
    def render_sprites(self, stdscr, sprites, camera, z_buffer, x_offset=0, y_offset=0):
        """
        Render sprites to screen with Z-buffering.
        
        Args:
            stdscr: Curses screen object
            sprites: List of Sprite objects (already calculated)
            camera: Camera object (for reference)
            z_buffer: List of distances for each screen column (from wall rendering)
            x_offset: X offset for rendering
            y_offset: Y offset for rendering
        """
        import curses
        
        for sprite in sprites:
            # Calculate vertical position
            sprite_top = (self.viewport_height - sprite.height) // 2
            sprite_bottom = sprite_top + sprite.height
            
            # Clamp to viewport
            sprite_top = max(0, sprite_top)
            sprite_bottom = min(self.viewport_height, sprite_bottom)
            
            # Get display character based on type
            if sprite.sprite_type in ('item', 'exit'):
                display_char = sprite.char
            else:
                display_char = self._shade_sprite_char(sprite.char, sprite.distance)

            half_width = self.sprite_width // 2
            for col_offset in range(-half_width, half_width + 1):
                render_x = sprite.screen_x + col_offset

                if render_x < 0 or render_x >= self.viewport_width:
                    continue

                # Check Z-buffer per column (don't draw if behind wall)
                if render_x < len(z_buffer) and z_buffer[render_x] < sprite.distance:
                    continue

                # Draw sprite column
                for y in range(sprite_top, sprite_bottom):
                    try:
                        stdscr.addch(
                            y_offset + y,
                            x_offset + render_x,
                            display_char,
                            curses.color_pair(sprite.color) | curses.A_BOLD
                        )
                    except curses.error:
                        pass
    
    def _shade_sprite_char(self, char, distance):
        """
        Apply distance-based shading to sprite character.
        
        Args:
            char: Original character
            distance: Distance to sprite
        
        Returns:
            Shaded character
        """
        # Progressive dimming based on distance
        if distance < 3.0:
            return char
        elif distance < 6.0:
            # Slight dimming for medium distance
            dim_map = {
                'z': 'z', 'v': 'v', 'g': 'g', 'o': 'o', 's': 's',
                '%': '%', '$': '$', '(': '(', '!': '!', '?': '?',
                '>': '>', 'k': 'k',
            }
            return dim_map.get(char, char)
        elif distance < 10.0:
            # More dimming for far distance
            dim_map = {
                'z': 'z', 'v': 'v', 'g': 'g', 'o': 'o', 's': 's',
                '%': 'o', '$': 'o', '(': 'c', '!': 'i', '?': '.',
                '>': '>', 'k': '.',
            }
            return dim_map.get(char, '.')
        else:
            # Very dim for very far
            return '·'


def test_sprite_renderer():
    """Test sprite renderer."""
    print("=" * 60)
    print("SPRITE RENDERER TEST")
    print("=" * 60)
    
    # Create renderer
    renderer = SpriteRenderer(viewport_width=70, viewport_height=20, fov=60.0)
    
    print(f"\nRenderer Configuration:")
    print(f"  Viewport: {renderer.viewport_width}x{renderer.viewport_height}")
    print(f"  FOV: {renderer.fov}°")
    print(f"  Max distance: {renderer.max_sprite_distance}")
    
    # Test sprite creation
    print(f"\n" + "=" * 60)
    print("SPRITE CREATION TEST")
    print("=" * 60)
    
    from presentation.colors import COLOR_ZOMBIE
    test_sprite = Sprite(10.5, 10.5, 'z', COLOR_ZOMBIE, 'enemy')
    
    print(f"\nTest Sprite:")
    print(f"  Position: ({test_sprite.x}, {test_sprite.y})")
    print(f"  Character: '{test_sprite.char}'")
    print(f"  Type: {test_sprite.sprite_type}")
    
    # Test distance shading
    print(f"\n" + "=" * 60)
    print("DISTANCE SHADING TEST")
    print("=" * 60)
    
    test_distances = [1.0, 3.0, 6.0, 10.0, 15.0]
    test_chars = ['z', '%', '$', '>']
    
    print("\n  Char | Distance | Result")
    print("  -----|----------|--------")
    
    for char in test_chars:
        for dist in test_distances:
            shaded = renderer._shade_sprite_char(char, dist)
            print(f"  '{char}'  | {dist:5.1f}    | '{shaded}'")
    
    # Test sprite positioning
    print(f"\n" + "=" * 60)
    print("SPRITE POSITIONING TEST")
    print("=" * 60)
    
    from presentation.camera.camera import Camera
    
    camera = Camera(5.0, 5.0, angle=0.0, fov=60.0)
    
    # Create test sprites at different positions
    test_sprites = [
        Sprite(8.0, 5.0, 'z', COLOR_ZOMBIE, 'enemy'),   # Directly ahead
        Sprite(5.0, 8.0, '%', 2, 'item'),                # To the north
        Sprite(3.0, 5.0, '$', 3, 'item'),                # Behind
    ]
    
    visible = renderer.calculate_sprite_positions(test_sprites, camera)
    
    print(f"\nCamera at ({camera.x}, {camera.y}) facing {camera.angle}°")
    print(f"Total sprites: {len(test_sprites)}")
    print(f"Visible sprites: {len(visible)}")
    
    print("\n  Sprite | Distance | Screen X | Height")
    print("  -------|----------|----------|--------")
    
    for sprite in visible:
        print(f"  '{sprite.char}'    | {sprite.distance:6.2f}   | {sprite.screen_x:4d}     | {sprite.height:3d}")
    
    print("\n✓ Sprite renderer tests complete!")


if __name__ == "__main__":
    test_sprite_renderer()
