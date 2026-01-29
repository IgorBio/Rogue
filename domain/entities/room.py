"""
Room entity for dungeon levels.

Rooms are rectangular areas that can contain enemies and items.
They are connected by corridors to form a complete level.
"""
import random


class Room:
    """
    Rectangular room in the dungeon.
    
    Rooms have walls on all sides with a walkable interior floor.
    The coordinate system uses top-left as the origin point.
    
    Attributes:
        x (int): Top-left corner X coordinate
        y (int): Top-left corner Y coordinate
        width (int): Room width including walls
        height (int): Room height including walls
        enemies (list): Enemy instances in this room
        items (list): Item instances in this room
    """
    
    def __init__(self, x, y, width, height):
        """
        Initialize a room.
        
        Args:
            x (int): Top-left corner X coordinate
            y (int): Top-left corner Y coordinate
            width (int): Room width (including walls)
            height (int): Room height (including walls)
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.enemies = []
        self.items = []
    
    def add_enemy(self, enemy):
        """
        Add an enemy to this room.
        
        Args:
            enemy: Enemy instance to add
        """
        self.enemies.append(enemy)
    
    def remove_enemy(self, enemy):
        """
        Remove an enemy from this room.
        
        Args:
            enemy: Enemy instance to remove
        """
        if enemy in self.enemies:
            self.enemies.remove(enemy)
    
    def add_item(self, item):
        """
        Add an item to this room.
        
        Args:
            item: Item instance to add
        """
        self.items.append(item)
    
    def remove_item(self, item):
        """
        Remove an item from this room.
        
        Args:
            item: Item instance to remove
        """
        if item in self.items:
            self.items.remove(item)
    
    def contains_point(self, px, py):
        """
        Check if a point is inside the room's interior (excluding walls).
        
        Args:
            px (int): Point X coordinate
            py (int): Point Y coordinate
            
        Returns:
            bool: True if point is on the floor, False otherwise
        """
        return (self.x < px < self.x + self.width - 1 and
                self.y < py < self.y + self.height - 1)
    
    def is_on_wall(self, px, py):
        """
        Check if a point is on the room's wall.
        
        Args:
            px (int): Point X coordinate
            py (int): Point Y coordinate
            
        Returns:
            bool: True if point is on a wall, False otherwise
        """
        on_horizontal_wall = (py == self.y or py == self.y + self.height - 1)
        on_vertical_wall = (px == self.x or px == self.x + self.width - 1)
        within_bounds = (self.x <= px <= self.x + self.width - 1 and
                        self.y <= py <= self.y + self.height - 1)
        
        return within_bounds and (on_horizontal_wall or on_vertical_wall)
    
    def is_in_room(self, px, py):
        """
        Check if point is anywhere in room (including walls).
        
        Args:
            px (int): Point X coordinate
            py (int): Point Y coordinate
            
        Returns:
            bool: True if point is in room bounds, False otherwise
        """
        return (self.x <= px <= self.x + self.width - 1 and
                self.y <= py <= self.y + self.height - 1)
    
    def get_center(self):
        """
        Get the center coordinates of the room.
        
        Returns:
            tuple: (center_x, center_y) coordinates
        """
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        return (center_x, center_y)
    
    def get_random_floor_position(self):
        """
        Get a random position on the room floor (not on walls).
        
        Used for spawning enemies and items.
        
        Returns:
            tuple: (x, y) coordinates on the floor
        """
        x = random.randint(self.x + 1, self.x + self.width - 2)
        y = random.randint(self.y + 1, self.y + self.height - 2)
        return (x, y)
    
    def __repr__(self):
        return (f"Room(x={self.x}, y={self.y}, w={self.width}, h={self.height}, "
                f"enemies={len(self.enemies)}, items={len(self.items)})")