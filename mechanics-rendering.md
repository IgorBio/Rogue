# Code Review: Roguelike Game Project

## Executive Summary

This is a well-structured roguelike dungeon crawler with 2D/3D rendering modes, fog of war, dynamic difficulty, and persistent statistics. The architecture follows clean separation of concerns with domain, presentation, and data layers. However, several critical issues affect gameplay mechanics and rendering.

## Critical Issues

### 1. **3D Sprite Rendering Bug (CRITICAL - Recently Fixed)**

**Location:** `presentation/renderer_3d.py`, `presentation/rendering/sprite_renderer_3d.py`

**Issue:** The Z-buffer was not being properly reset between frames, causing sprites (enemies/items) to not render correctly in 3D mode.

**Status:** ✅ FIXED in the current code

* Z-buffer now resets at start of each frame
* Proper depth checking implemented
* Sprites render correctly behind walls

### 2. **Enemy Position Type Inconsistency (MEDIUM)**

**Location:** Multiple files - `domain/entities/enemy.py`, `domain/enemy_ai.py`, etc.

**Problem:** Enemy positions use the `Position` class internally but expose `.position` as both `Position` objects and tuples inconsistently.

```python
# In enemy.py
@property
def position(self) -> Position:
    """Get enemy position as Position object."""
    return self._position

# But many places expect tuple:
enemy.position == (x, y)  # Sometimes works, sometimes doesn't
```

**Impact:** Can cause bugs in movement, collision detection, and rendering.

**Fix Needed:**

```python
# Option 1: Always return tuples (simpler)
@property
def position(self) -> Tuple[int, int]:
    return self._position.tuple

# Option 2: Ensure Position.__eq__ handles tuples (already implemented)
# Just need to audit all position comparisons
```

### 3. **Camera Synchronization Complexity (MEDIUM)**

**Location:** `domain/game_session.py`, `presentation/view_manager.py`, `presentation/camera/sync.py`

**Problem:** Camera position synchronization between domain (integer grid) and presentation (float coordinates) is overly complex with multiple layers.

**Current Flow:**

```
Character.position (int) 
  → Event published 
    → ViewManager receives event 
      → CameraSync.sync_camera_to_character 
        → Camera updates (float)
```

**Issues:**

* Tight coupling through events
* Offset calculations scattered across multiple files
* Hard to debug desync issues

**Recommendation:** Simplify to direct synchronization in GameSession when mode is 3D.

### 4. **Fog of War Visibility Edge Cases (LOW-MEDIUM)**

**Location:** `domain/fog_of_war.py`

**Problem:** The `is_position_visible()` method has complex logic that may not handle all edge cases correctly:

```python
def is_position_visible(self, x, y):
    if self.current_room_index is not None:
        room = self.level.rooms[self.current_room_index]
        return room.contains_point(x, y)
  
    if self.current_corridor_index is not None:
        in_visible_tiles = (x, y) in self.visible_tiles
        if in_visible_tiles:
            current_corridor = self.level.corridors[self.current_corridor_index]
            if current_corridor.contains_point(x, y):
                return True
          
            # This logic seems fragile
            for room_idx in self.discovered_rooms:
                room = self.level.rooms[room_idx]
                if room.contains_point(x, y):
                    return True
  
    return False
```

**Potential Issues:**

* Items/enemies in corridor tiles but not in visible_tiles won't render
* Boundary conditions between rooms/corridors unclear
* No clear contract for what "visible" means

### 5. **Statistics Tracking Duplication (LOW)**

**Location:** `domain/services/statistics_tracker.py`, various combat/movement handlers

**Problem:** Statistics are now tracked via events (good pattern), but some old direct calls may still exist:

```python
# Old pattern (should be removed):
self.stats.record_movement()

# New pattern (via events):
event_bus.publish(PlayerMovedEvent(from_pos, to_pos))
```

**Fix:** Audit all `stats.record_*()` calls and ensure they're only in `StatisticsTracker`.

### 6. **Exception Swallowing (MEDIUM)**

**Location:** Throughout codebase

**Problem:** Many try-except blocks silently swallow exceptions:

```python
try:
    event_bus.publish(ItemCollectedEvent(...))
except Exception as exc:
    log_exception(exc, __name__)
    # But then what? Should we fail? Continue?
```

**Impact:** Silent failures make debugging difficult.

**Recommendation:**

* Define which exceptions are expected and recoverable
* Re-raise critical exceptions
* Add fallback behavior for recoverable exceptions

## Design Issues

### 7. **Circular Dependency in Service Initialization**

**Location:** `domain/game_session.py`, `domain/session_coordinator.py`

**Problem:** SessionCoordinator needs GameSession reference, but GameSession creates SessionCoordinator.

**Current Workaround:** Delayed initialization via `initialize_services()`

**Better Design:** Use dependency injection more explicitly or split into separate phases.

### 8. **State Machine Complexity**

**Location:** `domain/services/game_states.py`, `domain/game_session.py`

**Issue:** State machine has explicit state validation, but also has backward-compatible property setters that bypass validation:

```python
@property
def game_over(self) -> bool:
    return self.state_machine.is_game_over()

@game_over.setter
def game_over(self, value: bool) -> None:
    if value and not self.state_machine.is_game_over():
        if not self.state_machine.is_victory():
            self.state_machine.transition_to(GameState.GAME_OVER)
```

**Recommendation:** Remove backward-compatible setters or make them raise deprecation warnings.

### 9. **Door Rendering in 2D Mode**

**Location:** `presentation/renderer_2d.py`

**Problem:** Door rendering logic in fog of war mode only checks if door is "near" current room using a fragile proximity check:

```python
def _is_door_near_room(self, door, room):
    dx, dy = door.position
    for x in range(room.x - 2, room.x + room.width + 2):
        for y in range(room.y - 2, room.y + room.height + 2):
            if (x, y) == door.position:
                return True
    return False
```

**Issues:**

* Magic number `2` for proximity
* Doors in discovered corridors might not render
* O(n²) complexity

**Fix:** Check if door's corridor is discovered instead.

## Performance Issues

### 10. **Raycasting Performance (LOW)**

**Location:** `presentation/rendering/raycasting.py`

**Problem:** Each frame casts `viewport_width` rays (typically 70) with DDA algorithm. No optimization for repeated calculations.

**Potential Optimizations:**

* Cache wall distances for static geometry
* Use spatial partitioning for level geometry
* Limit ray distance based on fog of war

### 11. **Fog of War Calculation (LOW)**

**Location:** `domain/fog_of_war.py`

**Problem:** Ray casting for visibility recalculates every movement:

```python
def get_visible_tiles(player_pos, level, max_distance=10):
    visible = set()
    for angle in range(0, 360, 5):  # 72 rays!
        # ... ray casting logic
```

**Impact:** 72 rays cast every movement in corridors.

**Optimization:** Only recalculate when moving in corridors, cache in rooms.

## Code Quality Issues

### 12. **Inconsistent Error Handling**

**Location:** Various

**Examples:**

```python
# Pattern 1: Return None
if not self._camera_factory:
    return None

# Pattern 2: Raise exception
if not callable(statistics_factory):
    raise TypeError("...")

# Pattern 3: Log and continue
except Exception as exc:
    log_exception(exc, __name__)
```

**Fix:** Establish consistent error handling patterns.

### 13. **Magic Numbers**

**Location:** Throughout

**Examples:**

```python
# combat_system.py
if health_percent > 0.8:  # What does 0.8 mean?

# renderer_3d.py
self.SHADE_DISTANCES = [2.0, 4.0, 7.0, 11.0, 16.0, 20.0]  # Why these values?

# fog_of_war.py
RAY_CASTING_ANGLE_STEP = 5  # degrees - why 5?
```

**Fix:** Extract to named constants with comments explaining the values.

### 14. **Type Hints Inconsistency**

**Location:** Various

**Problem:** Some files have comprehensive type hints, others have none:

```python
# Good
def generate_level(level_number: int, ...) -> Level:

# Bad (many places)
def _render_room_walls(self, room):  # No hints
```

**Fix:** Add type hints consistently or use `# type: ignore` where intentionally omitted.

## Architecture Recommendations

### 15. **Event Bus Global State**

**Location:** `domain/event_bus.py`

**Current:**

```python
event_bus = EventBus()  # Global singleton
```

**Issue:** Global state makes testing harder and creates hidden dependencies.

**Recommendation:** Inject EventBus instance or use context manager pattern.

### 16. **Save/Load Coupling**

**Location:** `data/save_manager.py`

**Problem:** SaveManager directly imports and instantiates domain classes. Changes to domain classes require updates to serialization.

**Recommendation:** Use a schema-based approach with versioning:

```python
SAVE_SCHEMA = {
    'version': '2.0',
    'character': CharacterSchema,
    'level': LevelSchema,
    ...
}
```

## Testing Gaps

### 17. **No Unit Tests Found**

**Critical Gap:** No test files found in the project.

**Recommendations:**

* Add tests for combat calculations (hit chance, damage)
* Test fog of war visibility logic
* Test state machine transitions
* Test save/load roundtrip
* Test position synchronization
* Test enemy AI movement patterns

### 18. **No Integration Tests**

**Need tests for:**

* Complete game flow (new game → level progression → game over)
* 2D ↔ 3D mode switching
* Item usage and effects
* Door/key system
* Dynamic difficulty adjustments

## Security/Stability

### 19. **File System Access**

**Location:** `data/save_manager.py`

**Issue:** No validation of save file paths:

```python
def save_game(self, game_session, filename=None):
    if filename is None:
        filename = self.autosave_file
    else:
        filename = os.path.join(self.save_dir, filename)
    # No validation - could write anywhere!
```

**Fix:** Validate filename doesn't contain path traversal.

### 20. **Curses Exception Handling**

**Location:** All rendering files

**Problem:** Many `try-except curses.error: pass` blocks hide real errors:

```python
try:
    self.stdscr.addstr(y, x, text)
except curses.error:
    pass  # What went wrong? Out of bounds? Terminal too small?
```

**Recommendation:** Log failures or provide user feedback for terminal size issues.

## Positive Aspects

### ✅ **Good Architecture**

* Clean separation between domain, presentation, and data layers
* Event-driven statistics tracking
* Service-based organization in domain layer

### ✅ **Good Patterns**

* Position class for coordinate management
* State machine for game states
* Factory pattern for enemy/item creation
* Coordinator pattern for service management

### ✅ **Good Features**

* Both 2D and 3D rendering modes
* Comprehensive fog of war system
* Dynamic difficulty adjustment
* Persistent statistics and leaderboard
* Save/load game functionality
* Multiple enemy types with unique AI
* Key/door puzzle system

## Priority Fix List

1. **HIGH:** Audit and fix position type consistency (enemy.position should reliably work as tuple)
2. **HIGH:** Add unit tests for core mechanics (combat, movement, visibility)
3. **MEDIUM:** Simplify camera synchronization
4. **MEDIUM:** Improve exception handling (don't swallow silently)
5. **MEDIUM:** Fix door rendering in fog of war
6. **LOW:** Extract magic numbers to constants
7. **LOW:** Add type hints consistently
8. **LOW:** Optimize fog of war calculations

## Conclusion

This is a **solid, well-architected roguelike** with impressive features. The main issues are:

* Position type inconsistencies that could cause subtle bugs
* Over-engineered camera synchronization
* Missing tests
* Exception handling could be more robust

The recently fixed Z-buffer bug shows the project is being actively maintained. With the recommended fixes, this would be a very robust codebase.

**Overall Grade: B+**

* Architecture: A
* Code Quality: B+
* Testing: F (no tests found)
* Documentation: B (good docstrings, could use more architectural docs)
