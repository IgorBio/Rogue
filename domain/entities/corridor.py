"""
Corridor entity for connecting rooms.

Corridors are pathways between rooms consisting of walkable tiles.
They enable navigation between different areas of the dungeon level.
"""


class Corridor:
    """
    Pathway connecting two or more rooms.
    
    Corridors are defined by a list of walkable tile coordinates.
    Both the player and enemies can move through corridors.
    
    Attributes:
        tiles (list): List of (x, y) tuples representing walkable tiles
    """
    
    def __init__(self, tiles=None):
        """
        Initialize a corridor.
        
        Args:
            tiles (list): Optional list of (x, y) coordinate tuples
        """
        self.tiles = tiles if tiles is not None else []
    
    def add_tile(self, x, y):
        """
        Add a tile to the corridor.
        
        Args:
            x (int): Tile X coordinate
            y (int): Tile Y coordinate
        """
        if (x, y) not in self.tiles:
            self.tiles.append((x, y))
    
    def contains_point(self, px, py):
        """
        Check if a point is part of this corridor.
        
        Args:
            px (int): Point X coordinate
            py (int): Point Y coordinate
            
        Returns:
            bool: True if point is in corridor, False otherwise
        """
        return (px, py) in self.tiles
    
    def get_length(self):
        """
        Get the number of tiles in this corridor.
        
        Returns:
            int: Number of walkable tiles
        """
        return len(self.tiles)
    
    def __repr__(self):
        return f"Corridor(tiles={len(self.tiles)})"