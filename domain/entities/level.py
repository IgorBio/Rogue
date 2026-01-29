"""
Level entity representing a dungeon floor.

A level contains rooms connected by corridors, along with enemies, items,
and special locations like starting points and exits.
"""


class Level:
    """
    Complete dungeon floor with rooms, corridors, and entities.
    
    Each level consists of exactly ROOM_COUNT rooms arranged in a grid,
    connected by corridors. Levels track player progress through fog of war.
    
    Attributes:
        level_number (int): Level depth (1-21)
        rooms (list): List of Room instances
        corridors (list): List of Corridor instances
        doors (list): List of Door instances (for key system)
        starting_room_index (int): Index of the starting room
        exit_room_index (int): Index of the exit room
        exit_position (tuple): (x, y) coordinates of level exit
        discovered_rooms (set): Set of discovered room indices
        discovered_corridors (set): Set of discovered corridor indices
        current_room_index (int): Index of room player is currently in
    """
    
    def __init__(self, level_number):
        """
        Initialize a new level.
        
        Args:
            level_number (int): Level depth (1-21)
        """
        self.level_number = level_number
        self.rooms = []
        self.corridors = []
        self.doors = []
        
        self.starting_room_index = None
        self.exit_room_index = None
        self.exit_position = None
        
        self.discovered_rooms = set()
        self.discovered_corridors = set()
        self.current_room_index = None
    
    def add_room(self, room):
        """
        Add a room to the level.
        
        Args:
            room: Room instance to add
        """
        self.rooms.append(room)
    
    def add_corridor(self, corridor):
        """
        Add a corridor to the level.
        
        Args:
            corridor: Corridor instance to add
        """
        self.corridors.append(corridor)
    
    def get_room_at(self, x, y):
        """
        Get the room containing a point.
        
        Args:
            x (int): Point X coordinate
            y (int): Point Y coordinate
            
        Returns:
            tuple: (room, room_index) or (None, None) if not in any room
        """
        for idx, room in enumerate(self.rooms):
            if room.is_in_room(x, y):
                return room, idx
        return None, None
    
    def get_corridor_at(self, x, y):
        """
        Get the corridor containing a point.
        
        Args:
            x (int): Point X coordinate
            y (int): Point Y coordinate
            
        Returns:
            tuple: (corridor, corridor_index) or (None, None)
        """
        for idx, corridor in enumerate(self.corridors):
            if corridor.contains_point(x, y):
                return corridor, idx
        return None, None
    
    def is_walkable(self, x, y):
        """
        Check if a position is walkable.
        
        Considers room interiors, corridors, and locked doors.
        
        Args:
            x (int): Point X coordinate
            y (int): Point Y coordinate
            
        Returns:
            bool: True if position is walkable, False otherwise
        """
        for door in self.doors:
            if door.position == (x, y) and door.is_locked:
                return False
        
        for room in self.rooms:
            if room.contains_point(x, y):
                return True
        
        for corridor in self.corridors:
            if corridor.contains_point(x, y):
                return True
        
        return False
    
    def is_wall(self, x, y):
        """
        Check if a position is a wall.
        
        Args:
            x (int): Point X coordinate
            y (int): Point Y coordinate
            
        Returns:
            bool: True if position is a wall, False otherwise
        """
        for room in self.rooms:
            if room.is_on_wall(x, y):
                return True
        return False
    
    def get_starting_room(self):
        """
        Get the starting room.
        
        Returns:
            Room: Starting room instance or None
        """
        if self.starting_room_index is not None:
            return self.rooms[self.starting_room_index]
        return None
    
    def get_exit_room(self):
        """
        Get the exit room.
        
        Returns:
            Room: Exit room instance or None
        """
        if self.exit_room_index is not None:
            return self.rooms[self.exit_room_index]
        return None
    
    def get_all_enemies(self):
        """
        Get all enemies in the level.
        
        Returns:
            list: All enemy instances across all rooms
        """
        all_enemies = []
        for room in self.rooms:
            all_enemies.extend(room.enemies)
        return all_enemies
    
    def get_all_items(self):
        """
        Get all items in the level.
        
        Returns:
            list: All item instances across all rooms
        """
        all_items = []
        for room in self.rooms:
            all_items.extend(room.items)
        return all_items
    
    def get_door_at(self, x, y):
        """
        Get the door at the specified position.
        
        Args:
            x (int): Point X coordinate
            y (int): Point Y coordinate
            
        Returns:
            Door: Door instance at position or None
        """
        for door in self.doors:
            if door.position == (x, y):
                return door
        return None
    
    def discover_room(self, room_index):
        """
        Mark a room as discovered.
        
        Args:
            room_index (int): Index of room to discover
        """
        if 0 <= room_index < len(self.rooms):
            self.discovered_rooms.add(room_index)
    
    def discover_corridor(self, corridor_index):
        """
        Mark a corridor as discovered.
        
        Args:
            corridor_index (int): Index of corridor to discover
        """
        if 0 <= corridor_index < len(self.corridors):
            self.discovered_corridors.add(corridor_index)
    
    def __repr__(self):
        return (f"Level(number={self.level_number}, rooms={len(self.rooms)}, "
                f"corridors={len(self.corridors)}, doors={len(self.doors)})")