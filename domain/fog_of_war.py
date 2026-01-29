"""
Fog of War system for tracking visibility and discovered areas.

This module implements line-of-sight calculations and visibility tracking,
ensuring players only see explored areas and entities within view.
"""
import math


# Visibility constants
DEFAULT_VISIBILITY_RANGE = 10
RAY_CASTING_ANGLE_STEP = 5  # degrees


def bresenham_line(x0, y0, x1, y1):
    """
    Generate points along a line using Bresenham's algorithm.
    
    Used for line-of-sight calculations between two points.
    
    Args:
        x0 (int): Starting X coordinate
        y0 (int): Starting Y coordinate
        x1 (int): Ending X coordinate
        y1 (int): Ending Y coordinate
    
    Returns:
        list: List of (x, y) tuples along the line
    """
    points = []
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    
    err = dx - dy
    x, y = x0, y0
    
    while True:
        points.append((x, y))
        
        if x == x1 and y == y1:
            break
        
        e2 = 2 * err
        
        if e2 > -dy:
            err -= dy
            x += sx
        
        if e2 < dx:
            err += dx
            y += sy
    
    return points


def get_visible_tiles(player_pos, level, max_distance=DEFAULT_VISIBILITY_RANGE):
    """
    Calculate visible tiles using ray casting.
    
    Casts rays in all directions and stops at walls to determine
    which tiles are visible from the player's position.
    
    Args:
        player_pos (tuple): (x, y) player position
        level: Level object for walkability checks
        max_distance (int): Maximum visibility range in tiles
    
    Returns:
        set: Set of (x, y) tuples that are visible
    """
    visible = set()
    px, py = player_pos
    visible.add((px, py))
    
    for angle in range(0, 360, RAY_CASTING_ANGLE_STEP):
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)
        
        for distance in range(1, max_distance + 1):
            x = int(round(px + dx * distance))
            y = int(round(py + dy * distance))
            
            visible.add((x, y))
            
            if level.is_wall(x, y):
                break
            
            if not level.is_walkable(x, y):
                break
    
    return visible


class FogOfWar:
    """
    Manages fog of war state for a level.
    
    Tracks which rooms and corridors have been discovered,
    the player's current location, and visible tiles for
    line-of-sight rendering in corridors.
    
    Attributes:
        level: Level instance being tracked
        discovered_rooms (set): Indices of discovered rooms
        discovered_corridors (set): Indices of discovered corridors
        current_room_index (int): Index of current room or None
        current_corridor_index (int): Index of current corridor or None
        visible_tiles (set): Set of (x, y) tiles visible via line-of-sight
    """
    
    def __init__(self, level):
        """
        Initialize fog of war system.
        
        Args:
            level: Level object to track visibility for
        """
        self.level = level
        self.discovered_rooms = set()
        self.discovered_corridors = set()
        self.current_room_index = None
        self.current_corridor_index = None
        self.visible_tiles = set()
    
    def update_visibility(self, player_pos):
        """
        Update fog of war based on player position.
        
        Determines whether player is in a room or corridor,
        updates discovered areas, and calculates visible tiles.
        
        Args:
            player_pos (tuple): (x, y) player position
        """
        x, y = player_pos
        
        corridor, corridor_idx = self.level.get_corridor_at(x, y)
        
        if corridor:
            self._update_corridor_visibility(player_pos, corridor_idx)
        else:
            self._update_room_visibility(player_pos)
    
    def _update_corridor_visibility(self, player_pos, corridor_idx):
        """Update visibility when player is in a corridor."""
        self.current_room_index = None
        self.current_corridor_index = corridor_idx
        self.discovered_corridors.add(corridor_idx)
        
        self.visible_tiles = get_visible_tiles(player_pos, self.level)
        
        for vx, vy in self.visible_tiles:
            for idx, room in enumerate(self.level.rooms):
                if room.contains_point(vx, vy):
                    self.discovered_rooms.add(idx)
                    break
    
    def _update_room_visibility(self, player_pos):
        """Update visibility when player is in a room."""
        x, y = player_pos
        room, room_idx = self.level.get_room_at(x, y)
        
        if room:
            self.current_room_index = room_idx
            self.current_corridor_index = None
            self.discovered_rooms.add(room_idx)
            
            self.visible_tiles = set()
            for rx in range(room.x + 1, room.x + room.width - 1):
                for ry in range(room.y + 1, room.y + room.height - 1):
                    self.visible_tiles.add((rx, ry))
    
    def is_room_discovered(self, room_idx):
        """Check if a room has been discovered."""
        return room_idx in self.discovered_rooms
    
    def is_corridor_discovered(self, corridor_idx):
        """Check if a corridor has been discovered."""
        return corridor_idx in self.discovered_corridors
    
    def is_room_current(self, room_idx):
        """Check if a room is the current room."""
        return room_idx == self.current_room_index
    
    def is_corridor_current(self, corridor_idx):
        """Check if a corridor is the current corridor."""
        return corridor_idx == self.current_corridor_index
    
    def get_current_room(self):
        """Get the current room index, or None."""
        return self.current_room_index
    
    def get_current_corridor(self):
        """Get the current corridor index, or None."""
        return self.current_corridor_index
    
    def should_render_room_contents(self, room_idx):
        """
        Check if room contents (enemies, items) should be rendered.
        
        Only renders contents if player is currently in the room.
        
        Args:
            room_idx (int): Room index to check
        
        Returns:
            bool: True if contents should be visible
        """
        return self.is_room_current(room_idx)
    
    def should_render_room_walls(self, room_idx):
        """
        Check if room walls should be rendered.
        
        Renders walls if room has been discovered.
        
        Args:
            room_idx (int): Room index to check
        
        Returns:
            bool: True if walls should be visible
        """
        return self.is_room_discovered(room_idx)
    
    def should_render_corridor(self, corridor_idx):
        """
        Check if corridor should be rendered.
        
        Args:
            corridor_idx (int): Corridor index to check
        
        Returns:
            bool: True if corridor should be visible
        """
        return self.is_corridor_discovered(corridor_idx)
    
    def is_tile_visible(self, x, y):
        """
        Check if a specific tile is visible.
        
        Used for line-of-sight rendering in corridors.
        
        Args:
            x (int): Tile X coordinate
            y (int): Tile Y coordinate
        
        Returns:
            bool: True if tile is visible
        """
        if self.current_room_index is not None:
            room = self.level.rooms[self.current_room_index]
            return room.is_in_room(x, y)
        
        if self.current_corridor_index is not None:
            return (x, y) in self.visible_tiles
        
        return False
    
    def is_position_visible(self, x, y):
        """
        Check if a position should show enemies/items.
        
        This is the authoritative method for entity rendering decisions.
        
        Args:
            x (int): Position X coordinate
            y (int): Position Y coordinate
        
        Returns:
            bool: True if entities at this position should render
        """
        if self.current_room_index is not None:
            room = self.level.rooms[self.current_room_index]
            return room.contains_point(x, y)
        
        if self.current_corridor_index is not None:
            in_visible_tiles = (x, y) in self.visible_tiles
            if in_visible_tiles:
                current_corridor = self.level.corridors[self.current_corridor_index]
                if current_corridor.contains_point(x, y):
                    return True
                
                for room_idx in self.discovered_rooms:
                    room = self.level.rooms[room_idx]
                    if room.contains_point(x, y):
                        return True
        
        return False
    
    def reset(self):
        """Reset fog of war (for new level)."""
        self.discovered_rooms.clear()
        self.discovered_corridors.clear()
        self.current_room_index = None
        self.current_corridor_index = None
        self.visible_tiles.clear()