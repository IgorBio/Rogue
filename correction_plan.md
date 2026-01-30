
# Domain Layer Analysis & Refactoring Plan

## Executive Summary

The domain layer contains **core game logic** but has several architectural issues that violate clean architecture principles. This analysis identifies problems and provides a comprehensive refactoring plan.

---

## Current Architecture Overview

### Layer Structure

```
domain/
├── entities/          # Core game objects
├── services/          # Business logic services
├── level_generator.py # Procedural generation
├── combat.py          # Combat mechanics
├── enemy_ai.py        # Enemy behaviors
├── fog_of_war.py      # Visibility system
├── dynamic_difficulty.py
├── key_door_system.py
└── game_session.py    # Main coordinator
```

---

## Critical Issues Identified

### 1. **Domain Layer Contamination** ❌

 **Problem** : Domain imports from presentation/data layers, violating dependency inversion.

 **Evidence** :

* `game_session.py` imports `Camera` from `utils.raycasting` (presentation concern)
* `game_session.py` imports `Statistics` from `data.statistics` (data layer)
* `level_generator.py` uses presentation-specific constants

 **Impact** :

* Cannot test domain logic in isolation
* Presentation changes break domain tests
* Violates hexagonal architecture principles

---

### 2. **God Object Anti-Pattern** 🔴

 **Problem** : `GameSession` is a 1300+ line monolithic class doing everything.

 **Responsibilities** :

* Level generation
* Combat resolution
* Movement handling
* Inventory management
* State management
* 2D/3D mode switching
* Enemy turn processing
* Item selection workflows
* Save/load coordination

 **Impact** :

* Difficult to test individual features
* High coupling between unrelated concerns
* Hard to extend or modify

---

### 3. **State Management Chaos** 🔴

 **Problem** : Boolean flags scattered everywhere instead of explicit state machine.

 **Current approach** :

```python
self.game_over = False
self.victory = False
self.player_asleep = False
self.pending_selection = None
```

 **Issues** :

* No validation of state transitions
* Can have invalid combinations (e.g., `game_over=True, victory=True`)
* Implicit state logic scattered across methods
* Hard to reason about game flow

---

### 4. **Mixed Coordinate Systems** ⚠️

 **Problem** : Character uses `int` coordinates, Camera uses `float`, causing sync issues.

**Evidence** from `domain/entities/character.py`:

```python
self.position = (x, y)  # tuple of ints
```

**Evidence** from `utils/raycasting.py`:

```python
class Camera:
    def __init__(self, x: float, y: float):
        self.x = x  # float
        self.y = y  # float
```

 **Impact** :

* Bugs when switching between 2D ↔ 3D modes
* Position desync between character and camera
* Rounding errors accumulate

---

### 5. **Presentation Logic Leaking into Domain** ⚠️

 **Problem** : Domain entities know about rendering.

**Evidence** from `domain/entities/enemy.py`:

```python
self.char = stats['char']  # Display character
self.color = stats['color']  # Display color
```

 **Impact** :

* Domain tied to specific UI technology (curses)
* Cannot switch to GUI without touching domain

---

### 6. **Missing Service Layer** ⚠️

 **Problem** : Business logic scattered across entities and `GameSession`.

 **Missing services** :

* **CombatService** : Resolve attacks, calculate damage
* **MovementService** : Handle movement logic, collision
* **InventoryService** : Item selection, usage
* **LevelService** : Generation, progression

---

### 7. **Tight Coupling Between Entities** ⚠️

 **Problem** : Entities directly manipulate each other.

**Example** from `game_session.py`:

```python
enemy.take_damage(damage)
character.backpack.add_item(treasure)
```

 **Better** : Use domain events or services as intermediaries.

---

## Refactoring Plan

### Phase 1: Extract State Machine ✅ **DONE**

 **Status** : Already implemented in `domain/services/game_states.py`

 **What exists** :

```python
class GameState(Enum):
    INITIALIZING, PLAYING, PLAYER_ASLEEP, 
    ITEM_SELECTION, LEVEL_TRANSITION, 
    GAME_OVER, VICTORY
```

 **Next step** : Ensure all code uses `state_machine.transition_to()` instead of boolean flags.

---

### Phase 2: Fix Coordinate System 🔧 **IN PROGRESS**

 **Goal** : Unified coordinate representation.

 **Solution** : Create `Position` value object:

```python
# domain/entities/position.py
class Position:
    def __init__(self, x: int, y: int):
        self._x = int(x)  # Always store as int
        self._y = int(y)
  
    @property
    def x(self) -> int:
        return self._x
  
    @property
    def y(self) -> int:
        return self._y
  
    @property
    def tuple(self) -> tuple[int, int]:
        return (self._x, self._y)
  
    def distance_to(self, other: 'Position') -> float:
        dx = self._x - other._x
        dy = self._y - other._y
        return (dx*dx + dy*dy)**0.5
```

 **Migration** :

1. Update `Character` to use `Position` internally
2. Update `Camera` to store grid-aligned `Position` + fractional offset
3. Create `PositionSynchronizer` service for 2D ↔ 3D sync

 **Status** : Tests already exist in `tests/domain/test_position.py`

---

### Phase 3: Decompose GameSession 🏗️

 **Goal** : Split into focused services.

#### 3.1 Extract CombatService

```python
# domain/services/combat_service.py
class CombatService:
    def resolve_player_attack(self, player, enemy, weapon):
        # Calculate hit chance
        # Calculate damage
        # Apply damage
        # Generate combat result
        return CombatResult(...)
  
    def resolve_enemy_attack(self, enemy, player):
        ...
```

 **Moves from GameSession** :

* `_handle_combat()`
* Attack resolution logic

#### 3.2 Extract MovementService

```python
# domain/services/movement_service.py
class MovementService:
    def __init__(self, level_provider):
        self.level = level_provider
  
    def can_move_to(self, position: Position) -> bool:
        return self.level.is_walkable(position)
  
    def move_character(self, character, direction):
        new_pos = character.position + direction
        if self.can_move_to(new_pos):
            character.move_to(new_pos)
            return True
        return False
```

#### 3.3 Extract InventoryService

```python
# domain/services/inventory_service.py
class InventoryService:
    def request_item_selection(self, item_type):
        # Return selection request DTO
        ...
  
    def use_item(self, character, item):
        # Polymorphic item usage
        ...
```

#### 3.4 Extract LevelService

```python
# domain/services/level_service.py
class LevelService:
    def __init__(self, difficulty_manager):
        self.difficulty = difficulty_manager
  
    def generate_level(self, level_number):
        adjustments = self.difficulty.calculate_adjustments()
        return generate_level(level_number, adjustments)
  
    def advance_to_next_level(self):
        ...
```

---

### Phase 4: Remove Presentation Dependencies 🔌

#### 4.1 Extract Rendering Concerns from Entities

 **Before** :

```python
class Enemy:
    self.char = 'z'
    self.color = 'green'
```

 **After** :

```python
# Domain
class Enemy:
    @property
    def enemy_type(self) -> EnemyType:
        return EnemyType.ZOMBIE

# Presentation
class EnemyRenderer:
    SYMBOLS = {
        EnemyType.ZOMBIE: ('z', Colors.GREEN),
        ...
    }
```

#### 4.2 Move Camera to Presentation

 **Current** : `Camera` in `utils.raycasting` (wrong layer)

 **Solution** :

* Keep `Camera` in presentation
* Create domain `ViewState` for 2D/3D mode
* Use `PositionSynchronizer` to sync coordinates

---

### Phase 5: Introduce Domain Events 📡

 **Goal** : Decouple entities via events.

```python
# domain/events.py
class DomainEvent:
    pass

class EnemyDefeated(DomainEvent):
    def __init__(self, enemy, treasure):
        self.enemy = enemy
        self.treasure = treasure

class ItemPickedUp(DomainEvent):
    def __init__(self, item):
        self.item = item
```

 **Usage** :

```python
# In CombatService
if enemy.health <= 0:
    treasure = calculate_treasure(enemy)
    event_bus.publish(EnemyDefeated(enemy, treasure))
```

---

### Phase 6: Add Domain Validators 🛡️

 **Goal** : Enforce business rules at domain boundary.

```python
# domain/validators/game_rules.py
class GameRuleValidator:
    @staticmethod
    def can_use_item(character, item):
        if not character.is_alive():
            raise GameRuleViolation("Dead characters cannot use items")
        ...
  
    @staticmethod
    def can_attack(character, enemy):
        if not character.position.is_adjacent_to(enemy.position):
            raise GameRuleViolation("Enemy not adjacent")
```

---

## Detailed Migration Steps

### Step 1: State Machine Integration

 **Files to modify** :

* `domain/game_session.py`

 **Changes** :

1. Replace all `self.game_over = True` → `self.state_machine.transition_to(GameState.GAME_OVER)`
2. Replace all `if self.game_over:` → `if self.state_machine.is_game_over():`
3. Remove `game_over`, `victory`, `player_asleep` properties
4. Add validation in state transitions

 **Tests to update** :

* `tests/domain/test_game_session_state.py` ✅ (already exists)

---

### Step 2: Position Unification

 **Files to modify** :

1. `domain/entities/character.py`
   ```python
   # Before
   self.position = (x, y)

   # After
   self._position = Position(x, y)

   @property
   def position(self) -> tuple[int, int]:
       return self._position.tuple  # Backward compat
   ```
2. `utils/raycasting.py`
   ```python
   class Camera:
       def __init__(self, x: float, y: float):
           self._grid_pos = Position(int(x), int(y))
           self._offset_x = x - int(x)
           self._offset_y = y - int(y)
   ```
3. Create `domain/services/position_synchronizer.py`
   ```python
   class PositionSynchronizer:
       def sync_camera_to_character(self, camera, character):
           camera.set_position(
               character.position.x + 0.5,
               character.position.y + 0.5
           )
   ```

 **Tests** :

* `tests/domain/test_position.py` ✅
* `tests/domain/test_character_position.py` ✅
* `tests/utils/test_camera_position.py` ✅

---

### Step 3: Extract Combat Service

 **New file** : `domain/services/combat_service.py`

 **Extract from `GameSession`** :

* `_handle_combat()` → `CombatService.resolve_player_attack()`
* Combat result construction
* Treasure calculation

 **Update** :

```python
# In GameSession
def _handle_combat(self, enemy):
    result = self.combat_service.resolve_player_attack(
        self.character, enemy
    )
    # Handle result
```

---

### Step 4: Extract Movement Service

 **New file** : `domain/services/movement_service.py`

 **Extract** :

* Movement validation
* Collision detection
* Door unlocking logic
* Mimic reveal logic

---

### Step 5: Extract Inventory Service

 **New file** : `domain/services/inventory_service.py`

 **Extract** :

* Item selection workflows
* Item usage polymorphism
* Backpack management

---

## Testing Strategy

### Unit Tests

* Each service in isolation
* Mock dependencies
* Test state transitions explicitly

### Integration Tests

* Services working together
* Full game flows (e.g., combat → loot → level up)

### Regression Tests

* Run existing tests after each refactoring step
* Ensure backward compatibility during migration

---

## Risk Mitigation

### High-Risk Changes

1. **Position system** : Affects everything

* **Mitigation** : Comprehensive test suite already exists

1. **GameSession decomposition** : Many dependencies

* **Mitigation** : Incremental extraction, one service at a time

### Low-Risk Changes

1. **State machine** : Already implemented
2. **Combat service** : Well-defined boundaries

---

## Success Criteria

### Completion Checklist

* [ ] No imports from presentation → domain
* [ ] No imports from data → domain
* [ ] `GameSession` < 500 lines
* [ ] All entities use `Position`
* [ ] Explicit state machine everywhere
* [ ] 90%+ test coverage on domain
* [ ] All existing tests pass

---

## Estimated Timeline

| Phase                       | Effort | Risk       |
| --------------------------- | ------ | ---------- |
| 1. State Machine            | 1 day  | Low (done) |
| 2. Position System          | 2 days | Medium     |
| 3. Extract Services         | 5 days | Medium     |
| 4. Remove Presentation Deps | 2 days | Low        |
| 5. Domain Events            | 3 days | Low        |
| 6. Validators               | 2 days | Low        |

 **Total** : ~15 days

---

## Conclusion

The domain layer has solid foundations but violates clean architecture principles. The refactoring plan addresses:

1. ✅  **State management** : Explicit state machine
2. 🔧  **Coordinates** : Unified Position system
3. 🏗️  **Decomposition** : Service extraction
4. 🔌  **Dependencies** : Remove presentation/data imports
5. 📡  **Decoupling** : Domain events
6. 🛡️  **Validation** : Business rule enforcement

 **Priority** : Start with **Position system** (Phase 2), as it unblocks everything else. The state machine is already implemented, making Phase 1 validation-only.
