
# План рефакторинга domain-слоя проекта Rogue

## 📊 Текущий статус

### ✅ Выполнено

* StateMachine для управления состоянием
* Services: CombatSystem, LevelManager, MovementHandler, InventoryManager, EnemyTurnProcessor
* EventBus + event-based statistics tracking
* SessionCoordinator для координации сервисов
* Position class для координат
* SelectionRequest dataclass
* Централизация конфигурации (GameConfig, ItemConfig, etc.)

### 🔴 Критические проблемы

#### PROBLEM 1: Domain создаёт presentation-объекты

**Файл:** `domain/game_session.py:183-200`

```python
# Domain напрямую создаёт Camera и CameraController
if self._camera_factory is not None:
    self.camera = self._camera_factory(start_x + 0.5, start_y + 0.5, ...)
    self.camera_controller = self._camera_controller_factory(self.camera, self.level)
```

**Проблема:** Domain знает о Camera parameters (angle, fov, offset), нарушает Clean Architecture

**Решение:**

```python
# domain/game_session.py - только события
event_bus.publish(LevelGeneratedEvent(level, (start_x, start_y), level_number))

# presentation/view_manager.py - создание камеры
class ViewManager:
    def on_level_generated(self, event):
        camera = Camera(event.character_position[0] + 0.5, ...)
```

---

#### PROBLEM 2: PositionSynchronizer манипулирует presentation

**Файл:** `domain/services/position_synchronizer.py:68-89`

```python
# Domain-сервис управляет Camera
def sync_camera_to_character(self, camera: Any, character: Character):
    cam_x = float(char_x) + self.center_offset
    camera.set_position(cam_x, cam_y)  # ❌ Domain → Presentation
```

**Проблема:** Domain манипулирует presentation-объектами, `center_offset` — presentation concern

**Решение:**

```python
# domain/entities/position.py - только преобразование координат
class Position:
    def to_camera_coords(self, offset=0.5) -> Tuple[float, float]:
        return (float(self.x) + offset, float(self.y) + offset)

# presentation/camera_sync.py - синхронизация
class CameraSync:
    def sync_to_position(self, camera, position: Position):
        cam_x, cam_y = position.to_camera_coords()
        camera.set_position(cam_x, cam_y)
```

---

#### PROBLEM 3: GameSession 730+ строк, избыточная ответственность

**Файл:** `domain/game_session.py`

**Содержит:**

* State management (StateMachine)
* Camera/Controller factories ❌
* Delegation ко всем services
* Direct service access (`self.combat_system`, `self.movement_handler`, etc.)
* Public + private методы сервисов

**Проблема:** SessionCoordinator уже создан, но GameSession дублирует его API

**Решение:**

```python
class GameSession:
    def __init__(self, ...):
        self.state_machine = StateMachine()
        self.character = None
        self.level = None
        self.stats = Statistics()
        self.coordinator = SessionCoordinator(self, self.stats, difficulty_manager)
  
    # Только state transitions
    def set_game_over(self, reason): ...
    def set_victory(self): ...
  
    # Делегирование к coordinator (не дублирование)
    def process_action(self, action_type, action_data):
        return self.coordinator.process_action(action_type, action_data)
```

Удалить прямой доступ к сервисам: `self.combat_system`, `self.movement_handler`, etc.

---

### 🟡 Важные улучшения

#### PROBLEM 4: Statistics записываются в двух местах

**Файлы:** `domain/services/combat_system.py:43-45` + `StatisticsTracker`

```python
# combat_system.py - публикует события
event_bus.publish(AttackPerformedEvent(...))

# statistics_tracker.py - обрабатывает события
def _on_attack_performed(self, event):
    self.stats.record_attack(event.hit, event.damage)
```

**Проблема:** Нет централизованного аудита, легко забыть публикацию события

**Решение:** Все `stats.record_*()` вызовы заменить на события, удалить прямые вызовы

---

#### PROBLEM 5: Циклические зависимости services ↔ session

**Примеры:**

* `ActionProcessor(session)` → вызывает `session.inventory_manager`
* `MovementHandler(session)` → вызывает `session._get_item_at()`
* Все services держат `self.session`

**Проблема:** Tight coupling, сложное тестирование

**Решение:** Dependency Injection

```python
class MovementHandler:
    def __init__(self, enemy_locator, inventory_manager):
        self.enemies = enemy_locator
        self.inventory = inventory_manager
```

---

### 🟢 Технический долг

#### PROBLEM 6: Magic strings в action types

**Файл:** `domain/services/action_processor.py:8-13`

```python
ACTION_MOVE = "move"
ACTION_USE_FOOD = "use_food"
```

**Решение:** Enum

```python
class ActionType(Enum):
    MOVE = "move"
    USE_FOOD = "use_food"
```

---

#### PROBLEM 7: hasattr/getattr для enemy state

**Файлы:** `domain/enemy_ai.py`, `domain/services/enemy_turn_processor.py`

```python
if hasattr(enemy, 'is_resting'):
    enemy.is_resting = False
```

**Решение:** Dataclass с defaults

```python
@dataclass
class Ogre(Enemy):
    is_resting: bool = False
    will_counterattack: bool = False
```

---

#### PROBLEM 8: Отсутствие логирования state transitions

**Файл:** `domain/services/game_states.py:93`

```python
def transition_to(self, new_state):
    if not self.can_transition_to(new_state):
        raise ValueError(...)  # Silent fail
```

**Решение:**

```python
import logging

def transition_to(self, new_state):
    if not self.can_transition_to(new_state):
        logger.warning(f"Invalid: {self._state.name} -> {new_state.name}")
        raise ValueError(...)
```

---

## 🎯 План рефакторинга

### Этап 1: Вынос Camera из domain (4 часа)

**Приоритет:** 🔴 КРИТИЧЕСКИЙ

1. Создать `presentation/view_manager.py`:
   * `ViewManager.on_level_generated(event)` → создаёт Camera
   * Подписывается на `LevelGeneratedEvent`, `CharacterMovedEvent`
2. Удалить из `GameSession.__init__`:
   * `camera_factory`, `camera_controller_factory`
   * `self.camera = None`, `self.camera_controller = None`
3. Обновить `main.py`:
   * Создать `ViewManager` вне `GameSession`
   * ViewManager подписывается на события

**Результат:** Domain не знает о Camera

---

### Этап 2: Разделить PositionSynchronizer (2 часа)

**Приоритет:** 🔴 КРИТИЧЕСКИЙ

1. Добавить в `Position`:
   ```python
   def to_camera_coords(self, offset=0.5) -> Tuple[float, float]
   def from_camera_coords(cls, x, y, snap_mode='floor') -> Position
   ```
2. Создать `presentation/camera_sync.py`:
   * `CameraSync.sync_camera_to_character(camera, character)`
   * `CameraSync.sync_character_from_camera(character, camera)`
3. Пометить `@deprecated` camera-методы в `PositionSynchronizer`

**Результат:** Чистое разделение координат domain/presentation

---

### Этап 3: Упростить GameSession (3 часа)

**Приоритет:** 🔴 КРИТИЧЕСКИЙ

1. Удалить прямой доступ к сервисам:
   * Убрать `self.combat_system`, `self.movement_handler`, etc.
   * Все вызовы через `self.coordinator`
2. Оставить только:
   * `state_machine`, `character`, `level`, `stats`, `coordinator`
   * State transition методы
   * Делегирование к coordinator
3. Удалить дублирующие `_get_*`, `_request_*` методы

**Результат:** GameSession < 250 строк

---

### Этап 4: Event-only statistics (2 часа)

**Приоритет:** 🟡 ВАЖНЫЙ

1. Найти все `stats.record_*()` вызовы
2. Заменить на `event_bus.publish(Event(...))`
3. Убедиться `StatisticsTracker` обрабатывает все события

**Результат:** Невозможно забыть учесть статистику

---

### Этап 5: Dependency Injection для services (3 часа)

**Приоритет:** 🟡 ВАЖНЫЙ

1. Изменить конструкторы services:
   ```python
   class MovementHandler:
       def __init__(self, enemy_locator, inventory_manager, fog_of_war):
   ```
2. SessionCoordinator инжектит зависимости:
   ```python
   self.movement = MovementHandler(self.enemy_locator, self.inventory, fog_of_war)
   ```

**Результат:** Независимые, тестируемые сервисы

---

### Этап 6: Технический долг (2 часа)

**Приоритет:** 🟢 НЕКРИТИЧЕСКИЙ

1. `ActionType` enum вместо magic strings
2. `@dataclass` для enemy state (Ghost, Ogre, SnakeMage)
3. Logging для state transitions
4. Удалить `@deprecated` методы из Этапа 2

**Результат:** Чище код, меньше runtime ошибок

---

## ✅ Критерии успеха

1. ✅ Domain не импортирует/создаёт presentation-объекты
2. ✅ GameSession < 250 строк
3. ✅ Все services независимы (DI)
4. ✅ Statistics только через события
5. ✅ Все 203 теста проходят
6. ✅ Добавлены тесты для ViewManager, CameraSync

---

## 📝 Оценка трудоёмкости

* **Этап 1:** 4 часа (ViewManager)
* **Этап 2:** 2 часа (PositionSync split)
* **Этап 3:** 3 часа (GameSession refactor)
* **Этап 4:** 2 часа (Event-only stats)
* **Этап 5:** 3 часа (DI)
* **Этап 6:** 2 часа (Technical debt)

**Всего:** 16 часов

---

## 🚀 Следующие шаги

1. ✅ Ознакомиться с планом
2. ⬜ Выбрать этап (рекомендация: начать с Этапа 1)
3. ⬜ Создать feature branch
4. ⬜ Выполнить этап
5. ⬜ Запустить тесты
6. ⬜ Code review → Merge

---

**Дата:** 2026-02-01

**Версия:** 3.0 (финальный план после анализа SessionCoordinator)
