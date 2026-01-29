"""
Pathfinding utilities for enemy AI.
FIXED: Improved pathfinding to handle corridor tiles correctly.
"""
from collections import deque


def find_path(start, goal, level, max_distance=50):
    """
    Find the shortest path from start to goal using BFS.
    
    Args:
        start: Tuple of (x, y) starting position
        goal: Tuple of (x, y) goal position
        level: Level object for walkability checks
        max_distance: Maximum path length to search
    
    Returns:
        List of (x, y) positions from start to goal, or None if no path
    """
    if start == goal:
        return [start]
    
    # BFS queue: (position, path)
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        # Check if path is too long
        if len(path) > max_distance:
            continue
        
        # Check all adjacent positions (4-directional movement only)
        x, y = current
        neighbors = [
            (x, y - 1),  # Up
            (x, y + 1),  # Down
            (x - 1, y),  # Left
            (x + 1, y),  # Right
        ]
        
        for next_pos in neighbors:
            # Skip if already visited
            if next_pos in visited:
                continue
            
            # Check if walkable - this is the key fix
            # We need to check both rooms AND corridors
            nx, ny = next_pos
            if not level.is_walkable(nx, ny):
                continue
            
            # Add to visited
            visited.add(next_pos)
            
            # Create new path
            new_path = path + [next_pos]
            
            # Check if we reached the goal
            if next_pos == goal:
                return new_path
            
            # Add to queue
            queue.append((next_pos, new_path))
    
    # No path found
    return None


def get_next_step(start, goal, level):
    """
    Get the next step toward the goal using pathfinding.
    
    Args:
        start: Tuple of (x, y) starting position
        goal: Tuple of (x, y) goal position
        level: Level object for walkability checks
    
    Returns:
        Tuple of (x, y) for next position, or None if no path
    """
    path = find_path(start, goal, level)
    
    if path and len(path) > 1:
        # Return the second position in the path (first step toward goal)
        return path[1]
    
    return None


def get_distance(pos1, pos2):
    """
    Calculate Manhattan distance between two positions.
    
    Args:
        pos1: Tuple of (x, y)
        pos2: Tuple of (x, y)
    
    Returns:
        Integer Manhattan distance
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def is_adjacent(pos1, pos2):
    """
    Check if two positions are adjacent (including diagonals).
    
    Args:
        pos1: Tuple of (x, y)
        pos2: Tuple of (x, y)
    
    Returns:
        Boolean indicating if positions are adjacent
    """
    dx = abs(pos1[0] - pos2[0])
    dy = abs(pos1[1] - pos2[1])
    
    # Adjacent if within 1 tile (including diagonals)
    return dx <= 1 and dy <= 1 and (dx + dy) > 0


def get_random_adjacent_walkable(position, level):
    """
    Get a random walkable adjacent position.
    
    Args:
        position: Tuple of (x, y)
        level: Level object for walkability checks
    
    Returns:
        Tuple of (x, y) for random adjacent walkable position, or None
    """
    import random
    
    x, y = position
    
    # All 8 directions (including diagonals)
    directions = [
        (x, y - 1),      # Up
        (x, y + 1),      # Down
        (x - 1, y),      # Left
        (x + 1, y),      # Right
        (x - 1, y - 1),  # Up-left
        (x + 1, y - 1),  # Up-right
        (x - 1, y + 1),  # Down-left
        (x + 1, y + 1),  # Down-right
    ]
    
    # Filter to walkable positions
    walkable = [pos for pos in directions if level.is_walkable(pos[0], pos[1])]
    
    if walkable:
        return random.choice(walkable)
    
    return None


def get_cardinal_adjacent_walkable(position, level):
    """
    Get a random walkable cardinal direction (no diagonals).
    
    Args:
        position: Tuple of (x, y)
        level: Level object for walkability checks
    
    Returns:
        Tuple of (x, y) for random adjacent walkable position, or None
    """
    import random
    
    x, y = position
    
    # Only cardinal directions
    directions = [
        (x, y - 1),  # Up
        (x, y + 1),  # Down
        (x - 1, y),  # Left
        (x + 1, y),  # Right
    ]
    
    # Filter to walkable positions
    walkable = [pos for pos in directions if level.is_walkable(pos[0], pos[1])]
    
    if walkable:
        return random.choice(walkable)
    
    return None