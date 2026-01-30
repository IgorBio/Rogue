
# Анализ архитектуры и план рефакторинга

## 🔍 Выявленные проблемы

### 1. **Нарушения разделения слоев (Layer Violations)**

#### Критические зависимости:

* ❌ `domain/game_session.py` импортирует `presentation`:
  ```python
  from presentation.input_handler import InputHandler  # Line 43from utils.input_handler_3d import InputHandler3D   # Line 3D actions
  ```
* ❌ `domain/services/action_processor.py` импортирует `presentation`:
  ```python
  from presentation.input_handler import InputHandlerfrom utils.input_handler_3d import InputHandler3D
  ```
* ❌ `domain/services/movement_handler.py` содержит логику UI (messages)
* ❌ `utils/camera_controller.py` импортирует domain и presentation

### 2. **God Object: GameSession (900+ строк)**

* Отвечает за 12+ обязанностей
* Смешивает координацию, бизнес-логику и взаимодействие с UI
* Сложно тестировать изолированно

### 3. **Координаты: float vs int хаос**

* `Camera` использует float (x=10.5, y=20.3)
* `Character` использует int Position (x=10, y=20)
* При переключении 2D↔3D возникают рассинхронизации
* `PositionSynchronizer` частично решает, но проблема в корне

### 4. **Action Types как строки**

* `InputHandler.ACTION_MOVE = "move"` (magic strings)
* Нет типобезопасности
* Легко допустить опечатку

### 5. **Circular Dependencies Risk**

```
domain/game_session → presentation/input_handler
presentation/game_ui → domain/game_session
```

---

## 📋 План рефакторинга (поэтапный)

### **ЭТАП 0: Подготовка (30 мин)**

#### Шаг 0.1: Создать структуру для абстракций

```bash
mkdir -p domain/interfaces
mkdir -p domain/value_objects
mkdir -p tests/domain/interfaces
```

#### Шаг 0.2: Добавить Protocol для типизации

```python
# domain/interfaces/input_protocol.py
from typing import Protocol, Tuple, Optional

class InputAction(Protocol):
    """Абстракция действия игрока (независимая от UI)."""
    action_type: str
    data: Optional[Tuple[int, int]]

class InputProvider(Protocol):
    """Интерфейс для получения ввода (реализуется в presentation)."""
    def get_action(self) -> InputAction:
        ...
```

---

### **ЭТАП 1: Устранение прямых зависимостей domain → presentation**

#### Шаг 1.1: Создать enum для действий в domain (1 час)

```python
# domain/value_objects/player_action.py
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Tuple

class ActionType(Enum):
    """Типы действий игрока (domain-layer constants)."""
    MOVE = auto()
    USE_FOOD = auto()
    USE_WEAPON = auto()
    USE_ELIXIR = auto()
    USE_SCROLL = auto()
    ATTACK = auto()
    INTERACT = auto()
    ROTATE_LEFT = auto()
    ROTATE_RIGHT = auto()
    TOGGLE_MODE = auto()
    QUIT = auto()
    NONE = auto()

@dataclass(frozen=True)
class PlayerAction:
    """Value object для действия игрока."""
    action_type: ActionType
    direction: Optional[Tuple[int, int]] = None
    target_index: Optional[int] = None
  
    @classmethod
    def move(cls, dx: int, dy: int):
        return cls(ActionType.MOVE, direction=(dx, dy))
  
    @classmethod
    def use_item(cls, item_type: ActionType, index: int):
        return cls(item_type, target_index=index)
```

**Тесты:**

```python
# tests/domain/test_player_action.py
def test_player_action_move():
    action = PlayerAction.move(1, 0)
    assert action.action_type == ActionType.MOVE
    assert action.direction == (1, 0)

def test_player_action_immutable():
    action = PlayerAction.move(0, 1)
    with pytest.raises(AttributeError):
        action.direction = (1, 1)
```

**Коммит:**

```bash
git add domain/value_objects/player_action.py tests/domain/test_player_action.py
git commit -m "Add domain-layer PlayerAction value object"
```

---

#### Шаг 1.2: Рефакторинг ActionProcessor (2 часа)

**Изменить:** `domain/services/action_processor.py`

```python
# domain/services/action_processor.py
from domain.value_objects.player_action import PlayerAction, ActionType
from domain.services.game_states import GameState

class ActionProcessor:
    def __init__(self, session):
        self.session = session
  
    def process_action(self, action: PlayerAction) -> bool:
        """Process player action (domain layer only)."""
        # State checks
        if self.session.state_machine.is_asleep():
            self.session.message = "You are asleep!"
            self.session.state_machine.transition_to(GameState.PLAYING)
            self.session._process_enemy_turns()
            return False
      
        if self.session.state_machine.is_terminal():
            return False
      
        # Route to handler
        if self.session.is_3d_mode():
            return self._handle_3d_action(action)
        else:
            return self._handle_2d_action(action)
  
    def _handle_2d_action(self, action: PlayerAction) -> bool:
        """Handle 2D actions."""
        if action.action_type == ActionType.MOVE:
            return self.session.movement_handler.handle_2d_movement(action.direction)
        elif action.action_type == ActionType.USE_FOOD:
            return self.session.inventory_manager.request_food_selection()
        # ... остальные действия
        return False
  
    def _handle_3d_action(self, action: PlayerAction) -> bool:
        """Handle 3D actions."""
        if action.action_type == ActionType.MOVE:
            return self.session.movement_handler.handle_3d_movement('forward')
        # ... остальные действия
        return False
```

**Удалить импорты:** Убрать `from presentation.input_handler import InputHandler`

**Тесты:**

```python
# tests/domain/test_action_processor_refactored.py
def test_action_processor_uses_domain_actions():
    from domain.game_session import GameSession
    from domain.value_objects.player_action import PlayerAction, ActionType
  
    session = GameSession(test_mode=True)
    action = PlayerAction(ActionType.MOVE, direction=(1, 0))
  
    result = session.action_processor.process_action(action)
    assert isinstance(result, bool)
```

**Коммит:**

```bash
git commit -am "Refactor ActionProcessor to use domain PlayerAction"
```

---

#### Шаг 1.3: Создать адаптер в presentation (1 час)

**Создать:** `presentation/input_adapter.py`

```python
# presentation/input_adapter.py
"""Адаптер: преобразует curses input → domain PlayerAction."""
from domain.value_objects.player_action import PlayerAction, ActionType
from presentation.input_handler import InputHandler

class InputAdapter:
    """Converts presentation-layer input to domain actions."""
  
    # Mapping: presentation constants → domain ActionType
    ACTION_MAP = {
        InputHandler.ACTION_MOVE: ActionType.MOVE,
        InputHandler.ACTION_USE_FOOD: ActionType.USE_FOOD,
        InputHandler.ACTION_USE_WEAPON: ActionType.USE_WEAPON,
        InputHandler.ACTION_USE_ELIXIR: ActionType.USE_ELIXIR,
        InputHandler.ACTION_USE_SCROLL: ActionType.USE_SCROLL,
        InputHandler.ACTION_QUIT: ActionType.QUIT,
        InputHandler.ACTION_NONE: ActionType.NONE,
    }
  
    @classmethod
    def convert_2d_input(cls, input_type: str, input_data) -> PlayerAction:
        """Convert 2D input to PlayerAction."""
        action_type = cls.ACTION_MAP.get(input_type, ActionType.NONE)
      
        if action_type == ActionType.MOVE:
            return PlayerAction(ActionType.MOVE, direction=input_data)
        else:
            return PlayerAction(action_type)
  
    @classmethod
    def convert_3d_input(cls, input_type: str, input_data) -> PlayerAction:
        """Convert 3D input to PlayerAction."""
        from utils.input_handler_3d import InputHandler3D
      
        mapping = {
            InputHandler3D.ACTION_MOVE_FORWARD: ActionType.MOVE,
            InputHandler3D.ACTION_ROTATE_LEFT: ActionType.ROTATE_LEFT,
            # ... остальные маппинги
        }
      
        action_type = mapping.get(input_type, ActionType.NONE)
        return PlayerAction(action_type)
```

**Изменить:** `presentation/game_ui.py`

```python
# presentation/game_ui.py (метод get_player_action)
def get_player_action(self, game_session):
    """Get player action (returns domain PlayerAction)."""
    from presentation.input_adapter import InputAdapter
  
    if game_session.is_3d_mode():
        raw_action = self.input_handler_3d.get_action()
        # Special UI actions handled here
        if raw_action == InputHandler3D.ACTION_TOGGLE_MODE:
            new_mode = game_session.toggle_rendering_mode()
            return PlayerAction(ActionType.TOGGLE_MODE)
      
        return InputAdapter.convert_3d_input(raw_action, None)
    else:
        key = self.stdscr.getch()
        if key == 9:  # Tab
            game_session.toggle_rendering_mode()
            return PlayerAction(ActionType.TOGGLE_MODE)
      
        raw_type, raw_data = self._map_key_to_action(key)
        return InputAdapter.convert_2d_input(raw_type, raw_data)
```

**Коммит:**

```bash
git add presentation/input_adapter.py
git commit -am "Add InputAdapter to decouple presentation from domain"
```

---

### **ЭТАП 2: Устранение координатной рассинхронизации**

#### Шаг 2.1: Унификация координат через Position (1.5 часа)

**Проблема:** `Camera` использует float для raycasting, но это вызывает проблемы при синхронизации с Character.

**Решение:** Camera должен использовать `Position` внутри, но экспонировать float для рейкастинга.

**Изменить:** `utils/raycasting.py` (уже частично сделано в документе)

```python
# utils/raycasting.py (улучшение)
class Camera:
    def __init__(self, x: float, y: float, angle: float = 0.0, fov: float = 60.0):
        # Используем Position для grid-aligned координат
        self._grid_position = Position(int(x), int(y))
        self._fractional_x = x - int(x)  # 0.0 - 1.0
        self._fractional_y = y - int(y)
  
    @property
    def x(self) -> float:
        """Raycasting coordinate (grid + fractional)."""
        return float(self._grid_position.x) + self._fractional_x
  
    @property
    def y(self) -> float:
        return float(self._grid_position.y) + self._fractional_y
  
    @property
    def grid_position(self) -> Tuple[int, int]:
        """Grid-aligned position for Character sync."""
        return self._grid_position.tuple
  
    def set_position(self, x: float, y: float):
        self._grid_position.update(int(x), int(y))
        self._fractional_x = x - int(x)
        self._fractional_y = y - int(y)
```

**Тесты:**

```python
# tests/utils/test_camera_coordinates.py
def test_camera_float_coordinates():
    cam = Camera(10.7, 20.3)
    assert cam.x == 10.7
    assert cam.y == 20.3
    assert cam.grid_position == (10, 20)

def test_camera_sync_with_character():
    from domain.entities.character import Character
    char = Character(10, 20)
    cam = Camera(10.5, 20.5)
  
    assert char.position == cam.grid_position
```

**Коммит:**

```bash
git commit -am "Unify Camera coordinates with Position internally"
```

---

#### Шаг 2.2: Упростить PositionSynchronizer (1 час)

**Проблема:** Текущий `PositionSynchronizer` слишком сложен и дублирует логику.

**Решение:** Упростить до двух методов: `sync_to_2d()` и `sync_to_3d()`.

```python
# domain/services/position_synchronizer.py (упрощенная версия)
class PositionSynchronizer:
    """Simplified 2D ↔ 3D coordinate sync."""
  
    @staticmethod
    def sync_to_2d(character: Character, camera: Camera):
        """When switching to 2D: Character follows Camera grid."""
        character.move_to(*camera.grid_position)
  
    @staticmethod
    def sync_to_3d(camera: Camera, character: Character, preserve_angle=True):
        """When switching to 3D: Camera centers on Character."""
        char_x, char_y = character.position
        camera.set_position(char_x + 0.5, char_y + 0.5)
        # angle preserved by default
```

**Коммит:**

```bash
git commit -am "Simplify PositionSynchronizer to two methods"
```

---

### **ЭТАП 3: Разбиение God Object GameSession**

#### Шаг 3.1: Выделить SystemCoordinator (2 часа)

**Создать:** `domain/services/system_coordinator.py`

```python
# domain/services/system_coordinator.py
"""Координатор систем (замена GameSession как god object)."""
from domain.services.level_manager import LevelManager
from domain.services.combat_system import CombatSystem
from domain.services.movement_handler import MovementHandler
from domain.services.inventory_manager import InventoryManager
from domain.services.enemy_turn_processor import EnemyTurnProcessor
from domain.services.action_processor import ActionProcessor
from domain.services.game_states import StateMachine

class SystemCoordinator:
    """Thin coordinator: delegates to specialized systems."""
  
    def __init__(self, character, level, fog_of_war, stats, difficulty_manager):
        self.character = character
        self.level = level
        self.fog_of_war = fog_of_war
        self.stats = stats
        self.difficulty_manager = difficulty_manager
      
        # Initialize systems
        self.state_machine = StateMachine()
        self.combat_system = CombatSystem(stats)
        self.level_manager = LevelManager(difficulty_manager)
        self.movement_handler = MovementHandler(self)
        self.inventory_manager = InventoryManager(self)
        self.enemy_processor = EnemyTurnProcessor(self)
        self.action_processor = ActionProcessor(self)
      
        self.message = ""
  
    def process_action(self, action: PlayerAction) -> bool:
        """Delegate to ActionProcessor."""
        return self.action_processor.process_action(action)
  
    def is_game_over(self) -> bool:
        return self.state_machine.is_terminal()
```

**Изменить:** `domain/game_session.py`

```python
# domain/game_session.py (теперь тонкий фасад)
class GameSession:
    """Facade for game state (delegates to SystemCoordinator)."""
  
    def __init__(self, test_mode=False, test_level=1, test_fog_of_war=False):
        self.test_mode = test_mode
        # ... инициализация
      
        self.coordinator = SystemCoordinator(
            self.character, self.level, self.fog_of_war,
            self.stats, self.difficulty_manager
        )
  
    def process_player_action(self, action: PlayerAction) -> bool:
        return self.coordinator.process_action(action)
  
    # Делегирующие методы
    def is_game_over(self) -> bool:
        return self.coordinator.is_game_over()
```

**Коммит:**

```bash
git add domain/services/system_coordinator.py
git commit -am "Extract SystemCoordinator from GameSession"
```

---

### **ЭТАП 4: Устранение циклических зависимостей**

#### Шаг 4.1: Dependency Injection для UI (1 час)

**Проблема:** `GameUI` создает зависимости напрямую.

**Решение:** Передавать зависимости через конструктор.

```python
# main.py
def main(stdscr):
    from presentation.game_ui import GameUI
    from domain.game_session import GameSession
  
    ui = GameUI(stdscr)
    session = None
  
    while True:
        selection = ui.show_main_menu(save_manager)
      
        if selection == 'new':
            session = GameSession()
        elif selection == 'continue':
            session = load_session()
      
        # Game loop
        while not session.is_game_over():
            ui.render_game(session)
          
            # UI → domain через адаптер
            action = ui.get_player_action(session)
            session.process_player_action(action)
```

**Коммит:**

```bash
git commit -am "Apply dependency injection in main loop"
```

---

### **ЭТАП 5: Финальная проверка и тесты**

#### Шаг 5.1: Интеграционные тесты (1.5 часа)

```python
# tests/integration/test_layer_separation.py
def test_domain_has_no_presentation_imports():
    """Domain layer must not import presentation."""
    import ast
    import os
  
    for root, dirs, files in os.walk('domain'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file)) as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                assert not alias.name.startswith('presentation'), \
                                    f"Domain imports presentation in {file}"

def test_full_game_flow_with_adapters():
    """Test complete game flow with refactored architecture."""
    from domain.game_session import GameSession
    from domain.value_objects.player_action import PlayerAction, ActionType
  
    session = GameSession(test_mode=True)
  
    # Domain action (no presentation dependency)
    action = PlayerAction.move(1, 0)
    result = session.process_player_action(action)
  
    assert isinstance(result, bool)
    assert session.character.position[0] > 0
```

**Коммит:**

```bash
git add tests/integration/test_layer_separation.py
git commit -m "Add integration tests for layer separation"
```

---

## 📊 Метрики до/после рефакторинга

| Метрика                                             | До               | После                        |
| ---------------------------------------------------------- | ------------------ | --------------------------------- |
| Domain → Presentation imports                             | 3                  | 0 ✅                              |
| GameSession LOC                                            | 900                | ~200                              |
| Координатная система                    | float/int хаос | Position унифицирован |
| Action Types                                               | Magic strings      | Type-safe Enum                    |
| Циклические зависимости              | Да               | Нет ✅                         |
| Тестируемость domain изолированно | ❌                 | ✅                                |

---

## ✅ Финальная валидация

```bash
# 1. Проверка импортов
python -c "import ast; import domain.game_session" # Должен работать без presentation

# 2. Тесты
pytest tests/domain -v  # Все domain тесты должны проходить БЕЗ curses
pytest tests/integration -v

# 3. Запуск игры
python main.py  # Должна работать с новой архитектурой
```

---

## 🎯 Ключевые принципы рефакторинга

1. **Dependency Inversion** : Domain определяет интерфейсы (Protocol), presentation реализует.
2. **Value Objects** : `PlayerAction`, `Position` — immutable, type-safe.
3. **Thin Coordinator** : `GameSession` → фасад, делегирует `SystemCoordinator`.
4. **Adapter Pattern** : `InputAdapter` преобразует UI events → domain actions.
5. **Single Responsibility** : Каждый сервис отвечает за одну область.

Этот план устраняет **все архитектурные проблемы** с минимальным риском для стабильности кода. Выполняйте шаги **последовательно** с коммитами после каждого.
