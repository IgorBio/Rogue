"""
Key and Door system for colored keys (DOOM-style).

This module implements a key-door puzzle system where keys are color-coded
and must be found before their corresponding doors can be unlocked.
Keys do NOT persist across levels.
"""
import random
from enum import Enum
from collections import deque
from utils.constants import ItemType


# Level tier configuration for key distribution
TIER_1_MAX_LEVEL = 7
TIER_2_MAX_LEVEL = 14
TIER_1_KEY_COUNT = 3
TIER_2_KEY_COUNT = 4
TIER_3_KEY_COUNT = 5

MAX_PLACEMENT_ATTEMPTS = 15


class KeyColor(Enum):
    """Available key colors - expanded to support 5 keys."""
    RED = "red"
    BLUE = "blue"
    YELLOW = "yellow"
    GREEN = "green"
    PURPLE = "purple"


class Key:
    """Represents a colored key item."""
    
    def __init__(self, color):
        """
        Initialize a key.
        
        Args:
            color (KeyColor): Key color
        """
        
        self.item_type = ItemType.KEY
        self.color = color
        self.position = None
    
    def __repr__(self):
        return f"Key(color={self.color.value})"


class Door:
    """Represents a colored door that blocks corridors."""
    
    def __init__(self, color, x, y):
        """
        Initialize a door.
        
        Args:
            color (KeyColor): Door color (matches required key)
            x (int): X coordinate
            y (int): Y coordinate
        """
        self.color = color
        self.position = (x, y)
        self.is_locked = True
    
    def unlock(self):
        """Unlock the door."""
        self.is_locked = False
    
    def __repr__(self):
        return f"Door(color={self.color.value}, pos={self.position}, locked={self.is_locked})"


def place_keys_and_doors(level):
    """
    Place colored keys and doors in the level with softlock prevention.
    
    Key distribution by level tier:
    - Levels 1-7:   3 keys (RED, BLUE, YELLOW)
    - Levels 8-14:  4 keys (RED, BLUE, YELLOW, GREEN)
    - Levels 15-21: 5 keys (RED, BLUE, YELLOW, GREEN, PURPLE)
    
    Each level has its own independent set of keys.
    
    Args:
        level: Level object to add keys and doors to
    
    Returns:
        bool: True if placement succeeded, False otherwise
    """
    num_keys = _get_key_count_for_level(level.level_number)
    selected_colors = list(KeyColor)[:num_keys]
    
    graph = _build_room_graph(level)
    
    for attempt in range(MAX_PLACEMENT_ATTEMPTS):
        placement = _attempt_key_door_placement(level, graph, selected_colors)
        
        if placement and _verify_no_softlocks(level, graph, placement):
            _apply_placement(level, placement)
            return True
    
    return False


def _get_key_count_for_level(level_number):
    """
    Determine number of keys based on level tier.
    
    Args:
        level_number (int): Current level number
        
    Returns:
        int: Number of keys for this level
    """
    if level_number <= TIER_1_MAX_LEVEL:
        return TIER_1_KEY_COUNT
    elif level_number <= TIER_2_MAX_LEVEL:
        return TIER_2_KEY_COUNT
    else:
        return TIER_3_KEY_COUNT


def _build_room_graph(level):
    """
    Build a graph representing room connectivity via corridors.
    
    Args:
        level: Level object
    
    Returns:
        dict: Maps room indices to lists of (neighbor_index, corridor_index) tuples
    """
    graph = {i: [] for i in range(len(level.rooms))}
    
    for corridor_idx, corridor in enumerate(level.corridors):
        connected_rooms = []
        
        for tile in corridor.tiles:
            for room_idx, room in enumerate(level.rooms):
                if _is_tile_near_room(tile, room):
                    if room_idx not in connected_rooms:
                        connected_rooms.append(room_idx)
        
        if len(connected_rooms) >= 2:
            for i in range(len(connected_rooms)):
                for j in range(i + 1, len(connected_rooms)):
                    room_a = connected_rooms[i]
                    room_b = connected_rooms[j]
                    
                    graph[room_a].append((room_b, corridor_idx))
                    graph[room_b].append((room_a, corridor_idx))
    
    return graph


def _is_tile_near_room(tile, room):
    """Check if a tile is adjacent to or inside a room."""
    x, y = tile
    
    if room.is_in_room(x, y):
        return True
    
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if room.is_in_room(x + dx, y + dy):
                return True
    
    return False


def _find_door_position_near_room(corridor, rooms):
    """
    Find a corridor tile that adjoins a room (near entrance/exit).
    
    Args:
        corridor: Corridor object
        rooms (list): List of Room objects
    
    Returns:
        tuple: (x, y) for door position, or None if not found
    """
    corridor_len = len(corridor.tiles)
    check_positions = []
    
    end_section_size = max(1, corridor_len // 5)
    
    for i in range(min(end_section_size, corridor_len)):
        check_positions.append(corridor.tiles[i])
    
    for i in range(max(0, corridor_len - end_section_size), corridor_len):
        if corridor.tiles[i] not in check_positions:
            check_positions.append(corridor.tiles[i])
    
    for pos in check_positions:
        x, y = pos
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            adj_x, adj_y = x + dx, y + dy
            
            for room in rooms:
                if room.is_on_wall(adj_x, adj_y):
                    return pos
    
    if corridor.tiles:
        return corridor.tiles[0]
    
    return None


def _attempt_key_door_placement(level, graph, colors):
    """
    Attempt to place keys and doors in the level.
    
    Args:
        level: Level object
        graph: Room connectivity graph
        colors (list): List of KeyColor values to place
    
    Returns:
        dict: Placement info with 'keys' and 'doors' lists, or None if failed
    """
        
    placement = {
        'keys': [],
        'doors': []
    }
    
    starting_room = level.starting_room_index
    starting_corridors = [corridor_idx for _, corridor_idx in graph[starting_room]]
    available_corridors = [i for i in range(len(level.corridors)) 
                          if i not in starting_corridors]
    
    if len(available_corridors) < len(colors):
        return None
    
    random.shuffle(available_corridors)
    
    for color in colors:
        if not available_corridors:
            return None
        
        corridor_idx = available_corridors.pop()
        corridor = level.corridors[corridor_idx]
        
        door_pos = _find_door_position_near_room(corridor, level.rooms)
        
        if door_pos is None:
            door_pos = corridor.tiles[len(corridor.tiles) // 2]
        
        placement['doors'].append((color, corridor_idx, door_pos))
    
    for color in colors:
        door_corridor = None
        for door_color, corridor_idx, _ in placement['doors']:
            if door_color == color:
                door_corridor = corridor_idx
                break
        
        accessible_rooms = _get_accessible_rooms_without_corridor(
            graph, starting_room, door_corridor
        )
        
        accessible_rooms = [r for r in accessible_rooms 
                           if r != starting_room and r != level.exit_room_index]
        
        if not accessible_rooms:
            return None
        
        room_key_counts = {}
        for _, key_room, _ in placement['keys']:
            room_key_counts[key_room] = room_key_counts.get(key_room, 0) + 1
        
        accessible_rooms.sort(key=lambda r: room_key_counts.get(r, 0))
        
        candidates = [r for r in accessible_rooms 
                     if room_key_counts.get(r, 0) == room_key_counts.get(accessible_rooms[0], 0)]
        key_room = random.choice(candidates)
        
        key_pos = level.rooms[key_room].get_random_floor_position()
        
        placement['keys'].append((color, key_room, key_pos))
    
    return placement


def _get_accessible_rooms_without_corridor(graph, start_room, blocked_corridor):
    """
    Find all rooms accessible from start_room without using blocked_corridor.
    
    Args:
        graph: Room connectivity graph
        start_room (int): Starting room index
        blocked_corridor (int): Corridor index that is blocked
    
    Returns:
        set: Set of accessible room indices
    """
    accessible = set()
    queue = deque([start_room])
    accessible.add(start_room)
    
    while queue:
        current = queue.popleft()
        
        for neighbor, corridor_idx in graph[current]:
            if corridor_idx == blocked_corridor:
                continue
            
            if neighbor not in accessible:
                accessible.add(neighbor)
                queue.append(neighbor)
    
    return accessible


def _verify_no_softlocks(level, graph, placement):
    """
    Verify that the key/door placement has no softlocks.
    
    A softlock occurs when a key is behind its own door.
    
    Args:
        level: Level object
        graph: Room connectivity graph
        placement (dict): Placement dictionary
    
    Returns:
        bool: True if placement is valid, False if softlock exists
    """
    starting_room = level.starting_room_index
    
    blocked_corridors = {}
    for color, corridor_idx, _ in placement['doors']:
        blocked_corridors[corridor_idx] = color
    
    key_locations = {}
    for color, room_idx, _ in placement['keys']:
        key_locations[color] = room_idx
    
    collected_keys = set()
    max_iterations = len(placement['keys']) + 2
    
    for iteration in range(max_iterations):
        accessible = _get_accessible_rooms_with_keys(
            graph, starting_room, blocked_corridors, collected_keys
        )
        
        if level.exit_room_index in accessible:
            remaining_keys = set(key_locations.keys()) - collected_keys
            if not remaining_keys:
                return True
            
            all_remaining_accessible = all(
                key_locations[color] in accessible 
                for color in remaining_keys
            )
            if all_remaining_accessible:
                return True
        
        new_keys_found = False
        for color, room_idx in key_locations.items():
            if color not in collected_keys and room_idx in accessible:
                collected_keys.add(color)
                new_keys_found = True
        
        if not new_keys_found:
            if len(collected_keys) == len(placement['keys']):
                accessible = _get_accessible_rooms_with_keys(
                    graph, starting_room, blocked_corridors, collected_keys
                )
                return level.exit_room_index in accessible
            else:
                return False
    
    if len(collected_keys) == len(placement['keys']):
        accessible = _get_accessible_rooms_with_keys(
            graph, starting_room, blocked_corridors, collected_keys
        )
        return level.exit_room_index in accessible
    
    return False


def _get_accessible_rooms_with_keys(graph, start_room, blocked_corridors, collected_keys):
    """
    Find all rooms accessible with a set of collected keys.
    
    Args:
        graph: Room connectivity graph
        start_room (int): Starting room index
        blocked_corridors (dict): Maps corridor_idx to required key color
        collected_keys (set): Set of collected KeyColor values
    
    Returns:
        set: Set of accessible room indices
    """
    accessible = set()
    queue = deque([start_room])
    accessible.add(start_room)
    
    while queue:
        current = queue.popleft()
        
        for neighbor, corridor_idx in graph[current]:
            if corridor_idx in blocked_corridors:
                required_key = blocked_corridors[corridor_idx]
                
                if required_key not in collected_keys:
                    continue
            
            if neighbor not in accessible:
                accessible.add(neighbor)
                queue.append(neighbor)
    
    return accessible


def _apply_placement(level, placement):
    """
    Apply the key and door placement to the level.
    
    Args:
        level: Level object
        placement (dict): Placement dictionary
    """
    level.doors = []
    for color, corridor_idx, position in placement['doors']:
        door = Door(color, position[0], position[1])
        level.doors.append(door)
    
    for color, room_idx, position in placement['keys']:
        key = Key(color)
        key.position = position
        level.rooms[room_idx].add_item(key)


def can_pass_door(door, character):
    """
    Check if the character can pass through a door.
    
    Args:
        door: Door object
        character: Character object
    
    Returns:
        bool: True if character can pass
    """
    if not door.is_locked:
        return True
    
    keys = character.backpack.get_items(ItemType.KEY)
    
    for key in keys:
        if key.color == door.color:
            return True
    
    return False


def unlock_door_if_possible(door, character):
    """
    Try to unlock a door with a key from the character's backpack.
    
    Args:
        door: Door object
        character: Character object
    
    Returns:
        bool: True if door was unlocked, False otherwise
    """
    if not door.is_locked:
        return True
    
    keys = character.backpack.get_items(ItemType.KEY)
    
    for key in keys:
        if key.color == door.color:
            door.unlock()
            return True
    
    return False