
# План рефакторинга domain-слоя проекта Rogue

## 📋 Статус выполнения предыдущего плана

### ✅ Выполнено (Phases 1-3)

**Phase 1 — Critical Fixes:**

* ✅ Problem 6: Удалён метод `finalize_attack_result` (двойной вызов enemy turns)
* ✅ Problem 4: Добавлена проверка terminal state после боя в `MovementHandler`

**Phase 2 — Original Plan:**

* ✅ Stage 1: Удалены дублирующие константы из `utils/constants.py`
* ✅ Stage 2: Функция `create_synced_pair` перемещена из domain в `utils/sync_helpers.py`

**Phase 3 — Technical Debt:**

* ✅ Problem 3: Использование `PlayerConfig.ADJACENT_OFFSETS` в `inventory_manager.py`
* ✅ Problem 8: Упрощено сравнение с `EnemyType.MIMIC` в `enemy_locator.py`
* ✅ Problem 2: Создан `@dataclass SelectionRequest` в `item_selection.py`

---

## 🔍 Обнаруженные проблемы

### 🔴 КРИТИЧЕСКИЕ

#### PROBLEM A: Нарушение Single Responsibility в `GameSession`

**Файл:** `domain/game_session.py`

**Описание:**
`GameSession` содержит 700+ строк и нарушает принцип единственной ответственности:

* Управление состоянием игры
* Создание и управление презентационными объектами (Camera, CameraController)
* Логика генерации уровней
* Логика движения (2D и 3D)
* Логика инвентаря и предметов
* Логика боя
* Сохранение/загрузка

**Последствия:**

* Сложность тестирования
* Высокая связанность с другими слоями
* Нарушение архитектурных границ

**Решение:**
Уже частично выполнено через сервисы:

* ✅ `ActionProcessor` — обработка действий игрока
* ✅ `CombatSystem` — боевая система
* ✅ `LevelManager` — управление уровнями
* ✅ `MovementHandler` — обработка движения
* ✅ `InventoryManager` — управление инвентарем
* ✅ `EnemyTurnProcessor` — ходы врагов
* ✅ `EnemyLocator` — поиск врагов/предметов

**Оставшиеся задачи:**

1. Переместить создание Camera/CameraController в presentation layer
2. Создать `SessionCoordinator` для координации сервисов
3. Оставить в `GameSession` только управление состоянием через `StateMachine`

---

#### PROBLEM B: Factory injection создаёт presentation-объекты в domain

**Файл:** `domain/game_session.py`, метод `_generate_new_level()`

**Код:**

```python
# Domain-слой создаёт presentation-объекты
self.camera = self._camera_factory(
    start_x + 0.5,
    start_y + 0.5,
    angle=GameConfig.DEFAULT_CAMERA_ANGLE,
    fov=GameConfig.DEFAULT_CAMERA_FOV,
)
self.camera_controller = self._camera_controller_factory(self.camera, self.level)
```

**Проблема:**

* Domain знает о параметрах создания Camera (углы, FOV, смещения)
* Domain управляет lifecycle presentation-объектов
* Нарушается инверсия зависимостей

**Решение:**
Создать `ViewManager` в presentation-слое:

```python
# presentation/view_manager.py
class ViewManager:
    def create_camera_for_level(self, level, character, mode='2d'):
        if mode == '3d':
            start_room = level.get_starting_room()
            center_x, center_y = start_room.get_center()
            camera = Camera(center_x + 0.5, center_y + 0.5)
            controller = CameraController(camera, level)
            return camera, controller
        return None, None
  
    def sync_camera_to_character(self, camera, character):
        # Sync logic
```

Domain только уведомляет presentation через события:

```python
# domain/events.py
@dataclass
class LevelGeneratedEvent:
    level: Level
    character_position: Tuple[int, int]
```

---

### 🟡 ВАЖНЫЕ

#### PROBLEM C: Смешивание координатных систем в `PositionSynchronizer`

**Файл:** `domain/services/position_synchronizer.py`

**Проблема:**

```python
# PositionSynchronizer находится в domain, но оперирует Camera
def sync_camera_to_character(self, camera: Any, character: Character, ...):
    cam_x = float(char_x) + self.center_offset
    camera.set_position(cam_x, cam_y)  # Управляет presentation-объектом
```

**Последствия:**

* Domain манипулирует presentation-объектами
* `center_offset` — это presentation concern (где центрировать камеру)
* Неявная зависимость от реализации Camera

**Решение:**
Разделить на две части:

1. `domain/entities/position.py` — Position с методами преобразования координат
2. `presentation/camera_sync.py` — CameraSync использует Position для синхронизации

```python
# domain/entities/position.py
class Position:
    def to_camera_coords(self, offset=0.5) -> Tuple[float, float]:
        return (float(self.x) + offset, float(self.y) + offset)

# presentation/camera_sync.py
class CameraSync:
    def sync_camera_to_position(self, camera, position: Position):
        cam_x, cam_y = position.to_camera_coords()
        camera.set_position(cam_x, cam_y)
```

---

#### PROBLEM D: Statistics tracking разбросан по коду

**Файлы:** Множество мест в domain и services

**Проблема:**

```python
# В разных местах:
session.stats.record_movement()
session.stats.record_item_collected()
session.stats.record_attack(hit, damage)
# etc.
```

**Последствия:**

* Легко забыть записать статистику
* Дублирование кода учёта
* Нет централизованного аудита статистики

**Решение:**
Использовать паттерн Observer через события:

```python
# domain/events.py
@dataclass
class PlayerMovedEvent:
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]

@dataclass
class ItemCollectedEvent:
    item_type: str
    item: Any

# domain/services/statistics_tracker.py
class StatisticsTracker:
    def __init__(self, stats: Statistics, event_bus: EventBus):
        self.stats = stats
        event_bus.subscribe(PlayerMovedEvent, self._on_player_moved)
        event_bus.subscribe(ItemCollectedEvent, self._on_item_collected)
  
    def _on_player_moved(self, event: PlayerMovedEvent):
        self.stats.record_movement()
  
    def _on_item_collected(self, event: ItemCollectedEvent):
        self.stats.record_item_collected()
```

---

### 🟢 НЕКРИТИЧНЫЕ (технический долг)

#### PROBLEM E: Hardcoded magic strings для selection types

**Файл:** `domain/services/item_selection.py`

**Проблема:**

```python
selection_type='food'  # Магическая строка
selection_type='weapon'
selection_type='elixir'
```

**Решение:**

```python
# domain/services/item_selection.py
class SelectionType:
    FOOD = 'food'
    WEAPON = 'weapon'
    ELIXIR = 'elixir'
    SCROLL = 'scroll'

# Использование:
selection_type=SelectionType.FOOD
```

---

#### PROBLEM F: Избыточное использование getattr/hasattr

**Файлы:** `enemy_ai.py`, `combat_system.py`

**Проблема:**

```python
# Неявные проверки атрибутов
if hasattr(enemy, 'is_resting'):
    enemy.is_resting = False

teleport_cooldown = getattr(enemy, 'teleport_cooldown', 0)
```

**Последствия:**

* Нет явного контракта для атрибутов врагов
* Ошибки видны только в runtime
* Сложно понять, какие атрибуты требуются

**Решение:**
Использовать @dataclass с default values:

```python
@dataclass
class Ghost(Enemy):
    teleport_cooldown: int = 0
    invisibility_cooldown: int = 0
    is_invisible: bool = False
```

---

#### PROBLEM G: Циклические импорты между services

**Файлы:** Несколько services импортируют друг друга

**Проблема:**

```python
# action_processor.py импортирует session
# session импортирует action_processor
# Работает только благодаря lazy imports
```

**Решение:**
Использовать Dependency Injection вместо прямых импортов:

```python
class ActionProcessor:
    def __init__(self, combat_system, movement_handler, inventory_manager):
        self.combat = combat_system
        self.movement = movement_handler
        self.inventory = inventory_manager
```

---

#### PROBLEM H: Отсутствие валидации GameState transitions

**Файл:** `domain/services/game_states.py`

**Проблема:**

```python
# Нет логирования невалидных переходов
def transition_to(self, new_state: GameState) -> bool:
    if not self.can_transition_to(new_state):
        raise ValueError(f"Invalid transition...")  # Silent fail
```

**Улучшение:**

```python
import logging

def transition_to(self, new_state: GameState) -> bool:
    if not self.can_transition_to(new_state):
        logger.warning(
            f"Invalid state transition attempted: "
            f"{self._state.name} -> {new_state.name}"
        )
        raise ValueError(...)
```

---

## 📊 Приоритизация проблем

### Немедленно (блокируют развитие):

1. **PROBLEM A** — Рефакторинг GameSession (большой, но критичный)
2. **PROBLEM B** — Вынести создание Camera из domain

### Важные (улучшают архитектуру):

3. **PROBLEM C** — Разделить PositionSynchronizer на domain/presentation части
4. **PROBLEM D** — Event-based statistics tracking

### Технический долг (можно постепенно):

5. **PROBLEM E** — SelectionType constants
6. **PROBLEM F** — Dataclasses для enemy state
7. **PROBLEM G** — Явная DI между services
8. **PROBLEM H** — Логирование state transitions

---

## 🎯 План рефакторинга по этапам

### Этап 1: Вынос презентационной логики из domain

**Цель:** Устранить создание Camera/CameraController в domain-слое

**Шаги:**

1. Создать `presentation/view_manager.py` с методами создания камеры
2. Создать `domain/events.py` с событиями `LevelGeneratedEvent`, `CharacterMovedEvent`
3. Добавить `EventBus` для публикации событий из domain
4. Переместить логику создания Camera в ViewManager (подписка на события)
5. Удалить `_camera_factory` и `_camera_controller_factory` из `GameSession.__init__`

**Результат:** Domain не знает о Camera, использует только события

---

### Этап 2: Разделение PositionSynchronizer

**Цель:** Убрать manipulation presentation-объектов из domain

**Шаги:**

1. Добавить методы `to_camera_coords()` и `from_camera_coords()` в `Position`
2. Создать `presentation/camera_sync.py` с классом `CameraSync`
3. Переместить логику синхронизации из `PositionSynchronizer` в `CameraSync`
4. Обновить тесты для `Position` (domain) и `CameraSync` (presentation)
5. Удалить camera-related методы из `PositionSynchronizer`

**Результат:** Чистое разделение координатных систем между слоями

---

### Этап 3: Рефакторинг GameSession через SessionCoordinator

**Цель:** Уменьшить размер и ответственность GameSession

**Шаги:**

1. Создать `domain/session_coordinator.py` с классом `SessionCoordinator`
2. Переместить координацию сервисов из GameSession в Coordinator
3. Оставить в GameSession только:
   * `state_machine: StateMachine`
   * `character: Character`
   * `level: Level`
   * `stats: Statistics`
   * Методы делегирования к coordinator
4. Обновить `main.py` для работы с новой структурой

**Результат:** GameSession < 200 строк, фокус на state management

---

### Этап 4: Event-based statistics tracking

**Цель:** Централизовать учёт статистики через события

**Шаги:**

1. Расширить `domain/events.py` событиями для всех статистических действий
2. Создать `domain/services/statistics_tracker.py` с подписками на события
3. Заменить прямые вызовы `stats.record_*()` на публикацию событий
4. Добавить тесты для `StatisticsTracker`

**Результат:** Невозможно забыть учесть статистику, централизованный аудит

---

### Этап 5: Технический долг (постепенно)

**Цель:** Улучшить качество кода без изменения архитектуры

**Шаги (можно выполнять независимо):**

1. Создать `SelectionType` constants вместо magic strings
2. Добавить @dataclass для enemy state attributes (Ghost, Ogre, etc.)
3. Использовать явную DI между services (убрать session-dependencies)
4. Добавить логирование для state transitions и важных событий

**Результат:** Более явный код, меньше runtime ошибок

---

## ✅ Критерии успеха

После завершения рефакторинга должно быть выполнено:

1. ✅ Domain-слой не импортирует presentation-объекты (Camera, CameraController)
2. ✅ Domain-слой не создаёт presentation-объекты
3. ✅ GameSession < 200 строк, фокус на state management
4. ✅ Все services независимы друг от друга (явная DI)
5. ✅ Statistics tracking централизован через события
6. ✅ Все существующие тесты проходят (203 теста)
7. ✅ Добавлены новые тесты для новых компонентов (EventBus, ViewManager, etc.)

---

## 📝 Примечания

### Совместимость с существующим кодом

Рефакторинг выполняется итеративно с сохранением backward compatibility:

* Старые методы помечаются `@deprecated` с указанием замены
* Новая функциональность добавляется параллельно
* Миграция выполняется постепенно
* Тесты обновляются вместе с кодом

### Оценка трудоёмкости

* **Этап 1** (ViewManager): ~2-3 часа
* **Этап 2** (PositionSync split): ~2 часа
* **Этап 3** (SessionCoordinator): ~4-5 часов ⚠️ (самый большой)
* **Этап 4** (Event-based stats): ~3 часа
* **Этап 5** (Technical debt): ~2-3 часа

**Всего:** ~13-16 часов работы

### Риски

1. **Этап 3** может потребовать значительных изменений в presentation-слое (`main.py`, `game_ui.py`)
2. Необходимо тщательное тестирование после каждого этапа
3. Сохранение/загрузка игры может требовать обновления при изменении структуры

---

## 🔄 Следующие шаги

1. ✅ Ознакомиться с планом
2. ⬜ Выбрать этап для начала (рекомендация: Этап 1 или Этап 5)
3. ⬜ Создать feature branch для рефакторинга
4. ⬜ Выполнить этап
5. ⬜ Запустить все тесты
6. ⬜ Code review
7. ⬜ Merge и переход к следующему этапу

---

**Дата создания:** 2026-02-01

**Версия:** 2.0 (обновлённый план после Phase 1-3)
