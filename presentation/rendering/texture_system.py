"""
Texture system for 3D wall rendering.
Provides pattern-based textures that show movement direction.
"""
import math


class WallTexture:
    """Represents a wall texture pattern."""
    
    def __init__(self, name, pattern, width=None, height=None):
        """
        Initialize wall texture.
        
        Args:
            name: Texture name
            pattern: 2D list of characters (rows x columns)
            width: Texture width (auto-calculated if None)
            height: Texture height (auto-calculated if None)
        """
        self.name = name
        self.pattern = pattern
        self.height = height or len(pattern)
        self.width = width or (len(pattern[0]) if pattern else 0)
    
    def sample(self, texture_x, texture_y):
        """
        Sample texture at given coordinates.
        
        Args:
            texture_x: X coordinate (0.0 - 1.0)
            texture_y: Y coordinate (0.0 - 1.0)
        
        Returns:
            Character at texture position
        """
        # Wrap coordinates
        texture_x = texture_x % 1.0
        texture_y = texture_y % 1.0
        
        # Convert to pixel coordinates
        px = int(texture_x * self.width) % self.width
        py = int(texture_y * self.height) % self.height
        
        # Clamp to valid range
        px = max(0, min(px, self.width - 1))
        py = max(0, min(py, self.height - 1))
        
        return self.pattern[py][px]


class TextureManager:
    """Manages all wall textures."""
    
    def __init__(self):
        """Initialize texture manager with predefined textures."""
        self.textures = {}
        self._create_default_textures()
    
    def _create_default_textures(self):
        """Create default texture set."""
        
        # Brick wall texture (for rooms)
        brick_pattern = [
            "█▓▒░░▒▓█",
            "▓▒░ ░▒▓█",
            "░    ░▒▓",
            "█▓▒░░▒▓█",
            "▓▒░ ░▒▓█",
            "░    ░▒▓",
            "█▓▒░░▒▓█",
            "▓▒░ ░▒▓█",
        ]
        self.textures['room_wall'] = WallTexture('room_wall', brick_pattern)
        
        # Stone wall texture (for corridors)
        stone_pattern = [
            "▓▓▒▒░░▒▒",
            "▓▒▒░  ░▒",
            "▒░    ░▒",
            "░      ░",
            "▒░    ░▒",
            "▓▒▒░  ░▒",
            "▓▓▒▒░░▒▒",
            "▓▓▒▒░░▒▒",
        ]
        self.textures['corridor_wall'] = WallTexture('corridor_wall', stone_pattern)
        
        # Door texture
        door_pattern = [
            "╔═══════╗",
            "║███████║",
            "║███████║",
            "║██   ██║",
            "║██ ● ██║",
            "║██   ██║",
            "║███████║",
            "╚═══════╝",
        ]
        self.textures['door'] = WallTexture('door', door_pattern)
        
        # Locked door texture
        locked_door_pattern = [
            "╔═══════╗",
            "║▓▓▓▓▓▓▓║",
            "║▓▓▓▓▓▓▓║",
            "║▓▓   ▓▓║",
            "║▓▓ ⚿ ▓▓║",
            "║▓▓   ▓▓║",
            "║▓▓▓▓▓▓▓║",
            "╚═══════╝",
        ]
        self.textures['locked_door'] = WallTexture('locked_door', locked_door_pattern)
        
        # Alternative brick pattern (horizontal)
        brick_h_pattern = [
            "████▓▓▓▓",
            "▓▓▓▓░░░░",
            "████▓▓▓▓",
            "▓▓▓▓░░░░",
            "████▓▓▓▓",
            "▓▓▓▓░░░░",
            "████▓▓▓▓",
            "▓▓▓▓░░░░",
        ]
        self.textures['brick_horizontal'] = WallTexture('brick_horizontal', brick_h_pattern)
        
        # Metal panel texture
        metal_pattern = [
            "║│││││││",
            "║│││││││",
            "╬═══════",
            "║│││││││",
            "║│││││││",
            "╬═══════",
            "║│││││││",
            "║│││││││",
        ]
        self.textures['metal'] = WallTexture('metal', metal_pattern)
    
    def get_texture(self, texture_name):
        """
        Get texture by name.
        
        Args:
            texture_name: Name of texture
        
        Returns:
            WallTexture object or None
        """
        return self.textures.get(texture_name)
    
    def add_texture(self, texture):
        """
        Add a custom texture.
        
        Args:
            texture: WallTexture object
        """
        self.textures[texture.name] = texture
    
    def sample_texture(self, texture_name, texture_x, texture_y):
        """
        Sample a texture by name.
        
        Args:
            texture_name: Name of texture
            texture_x: X coordinate (0.0 - 1.0)
            texture_y: Y coordinate (0.0 - 1.0)
        
        Returns:
            Character at texture position or fallback character
        """
        texture = self.get_texture(texture_name)
        
        if texture:
            return texture.sample(texture_x, texture_y)
        
        # Fallback - return solid character
        return '█'


class TexturedRenderer:
    """Helper class for rendering textured walls."""
    
    def __init__(self, texture_manager):
        """
        Initialize textured renderer.
        
        Args:
            texture_manager: TextureManager instance
        """
        self.texture_manager = texture_manager
    
    def get_wall_char(self, wall_type, texture_x, texture_y, distance):
        """
        Get character for a wall position with texture and shading.
        
        Args:
            wall_type: Type of wall ('room_wall', 'corridor_wall', 'door')
            texture_x: X coordinate on texture (0.0 - 1.0)
            texture_y: Y coordinate on texture (0.0 - 1.0)
            distance: Distance to wall (for shading)
        
        Returns:
            Character to render
        """
        # Get base texture character
        char = self.texture_manager.sample_texture(wall_type, texture_x, texture_y)
        
        # Apply distance-based shading
        char = self._apply_distance_shading(char, distance)
        
        return char
    
    def _apply_distance_shading(self, char, distance):
        """
        Apply distance-based shading to character.
        
        Args:
            char: Original character
            distance: Distance to wall
        
        Returns:
            Shaded character
        """
        # Define shading levels
        # Bright characters stay bright, dim characters get dimmer
        shading_map = {
            # Very close (< 2.0) - no change
            (0.0, 2.0): lambda c: c,
            
            # Close (2.0 - 4.0) - slight dimming
            (2.0, 4.0): self._dim_char_level_1,
            
            # Medium (4.0 - 7.0) - moderate dimming
            (4.0, 7.0): self._dim_char_level_2,
            
            # Far (7.0 - 11.0) - significant dimming
            (7.0, 11.0): self._dim_char_level_3,
            
            # Very far (11.0 - 16.0) - heavy dimming
            (11.0, 16.0): self._dim_char_level_4,
            
            # Extremely far (> 16.0) - almost invisible
            (16.0, 100.0): self._dim_char_level_5,
        }
        
        # Find appropriate shading function
        for (min_dist, max_dist), shade_func in shading_map.items():
            if min_dist <= distance < max_dist:
                return shade_func(char)
        
        return char
    
    def _dim_char_level_1(self, char):
        """Slight dimming."""
        dim_map = {
            '█': '▓', '▓': '▒', '▒': '░', '░': '·',
            '║': '│', '═': '─', '╬': '+',
            '●': 'o', '⚿': '*',
        }
        return dim_map.get(char, char)
    
    def _dim_char_level_2(self, char):
        """Moderate dimming."""
        dim_map = {
            '█': '▒', '▓': '░', '▒': '░', '░': '·', '·': ' ',
            '║': '│', '│': '|', '═': '─', '─': '-', '╬': '+',
            '●': 'o', 'o': '.', '⚿': '*', '*': '.',
        }
        return dim_map.get(char, char)
    
    def _dim_char_level_3(self, char):
        """Significant dimming."""
        dim_map = {
            '█': '░', '▓': '·', '▒': '·', '░': ' ', '·': ' ',
            '║': '|', '│': '|', '|': '·', '═': '-', '─': '-', '-': '·',
            '╬': '+', '+': '·',
            '●': '.', 'o': '.', '⚿': '.', '*': '.',
        }
        return dim_map.get(char, '·')
    
    def _dim_char_level_4(self, char):
        """Heavy dimming."""
        dim_map = {
            '█': '·', '▓': ' ', '▒': ' ', '░': ' ', '·': ' ',
            '║': '·', '│': '·', '|': '·', '═': '·', '─': '·', '-': ' ',
            '╬': '·', '+': '·',
            '●': '·', 'o': '·', '.': ' ', '⚿': '·', '*': '·',
        }
        return dim_map.get(char, ' ')
    
    def _dim_char_level_5(self, char):
        """Almost invisible."""
        # Everything becomes empty or very faint
        return ' ' if char not in ['·'] else '·'


# Global texture manager instance
_texture_manager = None


def get_texture_manager():
    """Get global texture manager instance."""
    global _texture_manager
    if _texture_manager is None:
        _texture_manager = TextureManager()
    return _texture_manager


def test_textures():
    """Test texture system."""
    print("=" * 60)
    print("TEXTURE SYSTEM TEST")
    print("=" * 60)
    
    # Create texture manager
    tm = TextureManager()
    
    print(f"\nLoaded {len(tm.textures)} textures:")
    for name in tm.textures.keys():
        print(f"  - {name}")
    
    # Test sampling
    print("\n" + "=" * 60)
    print("TEXTURE SAMPLING TEST")
    print("=" * 60)
    
    # Sample room wall texture
    room_texture = tm.get_texture('room_wall')
    print(f"\nRoom Wall Texture ({room_texture.width}x{room_texture.height}):")
    print("─" * 40)
    for row in room_texture.pattern:
        print("".join(row))
    
    # Sample corridor wall texture
    corridor_texture = tm.get_texture('corridor_wall')
    print(f"\nCorridor Wall Texture ({corridor_texture.width}x{corridor_texture.height}):")
    print("─" * 40)
    for row in corridor_texture.pattern:
        print("".join(row))
    
    # Sample door texture
    door_texture = tm.get_texture('door')
    print(f"\nDoor Texture ({door_texture.width}x{door_texture.height}):")
    print("─" * 40)
    for row in door_texture.pattern:
        print("".join(row))
    
    # Test texture sampling at different coordinates
    print("\n" + "=" * 60)
    print("COORDINATE SAMPLING TEST")
    print("=" * 60)
    
    test_coords = [
        (0.0, 0.0), (0.5, 0.0), (1.0, 0.0),
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5),
        (0.0, 1.0), (0.5, 1.0), (1.0, 1.0),
    ]
    
    print("\nSampling room_wall at different coordinates:")
    print("  Coord      | Char")
    print("  -----------|-----")
    for x, y in test_coords:
        char = tm.sample_texture('room_wall', x, y)
        print(f"  ({x:.1f}, {y:.1f}) | '{char}'")
    
    # Test textured renderer
    print("\n" + "=" * 60)
    print("DISTANCE SHADING TEST")
    print("=" * 60)
    
    renderer = TexturedRenderer(tm)
    
    test_distances = [1.0, 3.0, 6.0, 9.0, 13.0, 18.0]
    
    print("\nShading '█' at different distances:")
    print("  Distance | Result")
    print("  ---------|-------")
    for dist in test_distances:
        char = renderer.get_wall_char('room_wall', 0.5, 0.5, dist)
        print(f"  {dist:5.1f}   | '{char}'")
    
    print("\n✓ Texture system working correctly!")


if __name__ == "__main__":
    test_textures()
