# ПРОМПТ ДЛЯ AI-АССИСТЕНТА: РЕФАКТОРИНГ DUNGEON CRAWLER

# ЗАДАЧА: Поэтапный рефакторинг Python игры Dungeon Crawler

## КОНТЕКСТ ПРОЕКТА

Ты работаешь с roguelike игрой на Python + curses, которая имеет режимы 2D и 3D рендеринга.

**Текущая структура:**

```
project/
├── domain/
│   ├── game_session.py      # ❌ 900 строк, god object
│   ├── level_generator.py
│   ├── combat.py
│   ├── enemy_ai.py
│   ├── dynamic_difficulty.py
│   └── entities/
│       ├── character.py
│       ├── enemy.py
│       ├── item.py
│       ├── level.py
│       └── room.py
├── data/
│   ├── save_manager.py      # ❌ Неполная сериализация
│   └── statistics.py
└── presentation/
    ├── renderer.py
    ├── renderer_3d.py
    └── input_handler.py
```

## КРИТИЧЕСКИЕ ПРОБЛЕМЫ

1. **God Object:** `GameSession` содержит 900 строк и 12 обязанностей
2. **Координаты:** Смешивание float и int между Camera и Character
3. **Неполное сохранение:** Не сохраняется difficulty_manager, camera, rendering_mode
4. **Дублирование:** Логика 2D и 3D обрабатывается отдельно
5. **Нет State Machine:** Состояния игры управляются флагами
6. **Производительность:** `get_all_enemies()` вызывается каждый ход без кэша

## ПЛАН РЕФАКТОРИНГА (ВЫПОЛНЯТЬ СТРОГО ПОСЛЕДОВАТЕЛЬНО)

### ЭТАП 0: ПОДГОТОВКА (30 мин)

**Шаг 0.1:** Создай структуру для тестов

```bash
mkdir -p tests/domain tests/presentation tests/data tests/integration
```

**Шаг 0.2:** Создай `config/game_config.py` с централизованными константами:

```python
class GameConfig:
    TOTAL_LEVELS = 21
    LEVEL_FACTOR_DIVISOR = 30
    MIN_LEVEL_FACTOR = 0.3
    HEALTH_EXCELLENT_THRESHOLD = 0.8
    # ... все константы из разных файлов
```

### ЭТАП 1: КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ

#### Шаг 1.1: Исправление координат (1 час)

**Создай:** `domain/entities/position.py`

```python
class Position:
    """Всегда хранит int координаты"""
    def __init__(self, x: float, y: float):
        self._x = int(x)
        self._y = int(y)
  
    @property
    def x(self) -> int:
        return self._x
  
    @property
    def y(self) -> int:
        return self._y
  
    @property
    def tuple(self) -> Tuple[int, int]:
        return (self._x, self._y)
  
    def update(self, x: float, y: float):
        self._x = int(x)
        self._y = int(y)
```

**Измени:** `domain/entities/character.py` - используй Position вместо tuple
**Измени:** `utils/raycasting.py` (Camera) - используй Position

**Напиши тесты:** `tests/domain/test_position.py`

**Проверь:** Запусти игру и убедись, что координаты работают корректно

**Коммит:**

```bash
git commit -m "Fix: Unify coordinate system with Position class"
```

---

#### Шаг 1.2: Синхронизация 2D/3D (1 час)

**Создай:** `domain/services/position_synchronizer.py`

```python
class PositionSynchronizer:
    def __init__(self, character, camera):
        self.character = character
        self.camera = camera
  
    def sync_from_character(self):
        """Камера следует за персонажем"""
        self.camera.move_to(
            self.character.position,
            self.character.position [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/104999126/42d07538-8a72-46d5-bc21-1d681c0c94cb/save_manager.py)
        )
  
    def sync_from_camera(self):
        """Персонаж в позиции камеры"""
        self.character.move_to(self.camera.x, self.camera.y)
  
    def validate_sync(self) -> bool:
        return (self.character.position == self.camera.x and
                self.character.position == self.camera.y) [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/104999126/42d07538-8a72-46d5-bc21-1d681c0c94cb/save_manager.py)
```

**Измени:** `domain/game_session.py`

- Добавь `self.position_sync = PositionSynchronizer(...)`
- В `toggle_rendering_mode()` используй sync методы
- После каждого toggle проверяй `validate_sync()`

**Коммит:**

```bash
git commit -m "Fix: Add position synchronization between 2D and 3D"
```

---

#### Шаг 1.3: Полная сериализация (1 час)

**Измени:** `data/save_manager.py`

Добавь в `save_game()`:

```python
save_data = {
    # ... существующие поля
    'rendering_mode': game_session.rendering_mode,
    'player_asleep': game_session.player_asleep,
    'game_over': game_session.game_over,
    'victory': game_session.victory,
    'difficulty_manager': self._serialize_difficulty_manager(...),
    'camera': self._serialize_camera(...)
}
```

Добавь методы:

```python
def _serialize_difficulty_manager(self, dm):
    return {
        'enemy_count_modifier': dm.enemy_count_modifier,
        'enemy_stat_modifier': dm.enemy_stat_modifier,
        # ... все модификаторы
    }

def _serialize_camera(self, camera):
    if camera is None:
        return None
    return {'x': camera.x, 'y': camera.y, 'angle': camera.angle}
```

Добавь восстановление в `restore_game_session()`:

```python
game_session.rendering_mode = save_data.get('rendering_mode', '2d')
# ... остальные поля
```

**Тест:** Сохрани и загрузи игру, проверь все поля

**Коммит:**

```bash
git commit -m "Fix: Complete game state serialization"
```

---

### ЭТАП 2: РАЗДЕЛЕНИЕ GAMESESSION

#### Шаг 2.1: State Machine (1.5 часа)

**Создай:** `domain/services/game_states.py`

```python
from enum import Enum, auto

class GameState(Enum):
    INITIALIZING = auto()
    PLAYING = auto()
    PLAYER_ASLEEP = auto()
    ITEM_SELECTION = auto()
    LEVEL_TRANSITION = auto()
    GAME_OVER = auto()
    VICTORY = auto()

class StateMachine:
    TRANSITIONS = {
        GameState.PLAYING: [GameState.PLAYER_ASLEEP, GameState.GAME_OVER, ...],
        # ... определи все возможные переходы
    }
  
    def __init__(self, initial_state=GameState.INITIALIZING):
        self._state = initial_state
  
    def transition_to(self, new_state):
        if new_state not in self.TRANSITIONS[self._state]:
            raise ValueError(f"Invalid: {self._state} -> {new_state}")
        self._state = new_state
  
    def is_terminal(self):
        return self._state in [GameState.GAME_OVER, GameState.VICTORY]
```

**Измени:** `domain/game_session.py`

- Добавь `self.state_machine = StateMachine()`
- Замени все `self.game_over`, `self.victory` на проверки состояния
- Замени `self.player_asleep` на `state_machine.current_state == GameState.PLAYER_ASLEEP`

**Напиши тесты:** `tests/domain/test_game_states.py`

**Коммит:**

```bash
git commit -m "Add: State machine for game state management"
```

---

#### Шаг 2.2: Combat System (2 часа)

**Создай:** `domain/services/combat_system.py`

```python
class CombatResult:
    def __init__(self):
        self.hit = False
        self.damage = 0
        self.killed = False
        self.messages = []
        self.effects = []
        self.treasure = None

class CombatSystem:
    def __init__(self, statistics=None):
        self.statistics = statistics
  
    def resolve_player_attack(self, player, enemy):
        """Возвращает CombatResult"""
        result = CombatResult()
    
        attack_result = resolve_attack(player, enemy)
        result.hit = attack_result['hit']
        result.damage = attack_result.get('damage', 0)
        result.killed = attack_result['killed']
    
        # Статистика
        if self.statistics:
            self.statistics.record_attack(result.hit, result.damage)
    
        return result
  
    def resolve_enemy_attack(self, enemy, player):
        """Возвращает CombatResult с эффектами"""
        # Аналогично
```

**Измени:** `domain/game_session.py`

- Добавь `self.combat_system = CombatSystem(self.stats)`
- Замени все вызовы `resolve_attack()` на `self.combat_system.resolve_*_attack()`
- Упрости `_handle_combat()` и `_process_enemy_turns()`

**Коммит:**

```bash
git commit -m "Extract: Combat system from GameSession"
```

---

#### Шаг 2.3: Level Manager (1.5 часа)

**Создай:** `domain/services/level_manager.py`

```python
class LevelManager:
    def __init__(self, difficulty_manager=None):
        self.difficulty_manager = difficulty_manager
        self.current_level_number = 1
        self.current_level = None
  
    def generate_level(self, character, stats, test_mode=False):
        difficulty_adjustments = None
        if not test_mode and character and stats:
            difficulty_adjustments = self.difficulty_manager.calculate_difficulty_adjustment(...)
    
        self.current_level = generate_level(
            self.current_level_number,
            difficulty_adjustments
        )
        return self.current_level
  
    def advance_to_next_level(self):
        if self.current_level_number >= GameConfig.TOTAL_LEVELS:
            return False
        self.current_level_number += 1
        return True
```

**Измени:** `domain/game_session.py`

- Добавь `self.level_manager = LevelManager(self.difficulty_manager)`
- Замени `_generate_new_level()` на делегирование к level_manager
- Упрости `_advance_level()`

**Коммит:**

```bash
git commit -m "Extract: Level manager from GameSession"
```

---

#### Шаг 2.4: Action Processor (2 часа)

**Создай:** `domain/services/action_processor.py`

```python
class ActionType:
    MOVE = 'move'
    ATTACK = 'attack'
    USE_FOOD = 'use_food'
    # ... все типы действий

class ActionProcessor:
    def __init__(self, game_session):
        self.session = game_session
  
    def process_action(self, action_type, action_data):
        # Проверка состояния
        if self.session.state_machine.current_state == GameState.PLAYER_ASLEEP:
            # ... обработка
    
        # Маршрутизация
        handler = self._get_handler(action_type)
        success = handler(action_data)
    
        if success:
            self._process_enemy_turns()
    
        return success
  
    def _handle_move(self, direction):
        """Универсальная обработка движения для 2D и 3D"""
        # ... логика
```

**Измени:** `domain/game_session.py`

- Добавь `self.action_processor = ActionProcessor(self)`
- Замени `process_player_action()` на делегирование
- Удали `_process_action_2d()` и `_process_action_3d()`

**Коммит:**

```bash
git commit -m "Extract: Action processor with unified 2D/3D handling"
```

---

#### Шаг 2.5: Финальная очистка GameSession (1 час)

**Цель:** GameSession должен быть ~200 строк, только координация

**Удали из GameSession:**

- Все методы `_handle_*` (перенесены в ActionProcessor)
- Методы `_process_enemy_turns` (в ActionProcessor)
- Методы `_spawn_*` (в LevelManager)

**Оставь в GameSession:**

- Инициализацию систем
- Делегирующие методы
- Геттеры состояния

**Коммит:**

```bash
git commit -m "Refactor: GameSession as thin coordinator layer"
```

---

### ЭТАП 3: ОПТИМИЗАЦИЯ И ТЕСТЫ

#### Шаг 3.1: Кэширование врагов (30 мин)

**Измени:** `domain/entities/level.py`

```python
class Level:
    def __init__(self, level_number):
        # ... существующие
        self._alive_enemies_cache = None
        self._cache_valid = False
  
    def get_alive_enemies(self):
        if not self._cache_valid:
            self._alive_enemies_cache = [
                e for room in self.rooms
                for e in room.enemies
                if e.is_alive()
            ]
            self._cache_valid = True
        return self._alive_enemies_cache
  
    def invalidate_enemy_cache(self):
        self._cache_valid = False
```

**Измени:** `domain/entities/room.py` - вызывай `invalidate_enemy_cache()` при удалении врага

**Коммит:**

```bash
git commit -m "Optimize: Add enemy caching to Level"
```

---

#### Шаг 3.2: Тесты (2 часа)

**Напиши тесты для:**

`tests/domain/test_position.py`:

```python
def test_position_float_to_int():
    pos = Position(10.7, 20.3)
    assert pos.x == 10
    assert pos.y == 20
```

`tests/domain/test_combat_system.py`:

```python
def test_player_attack_hit():
    player = Character(0, 0)
    enemy = Enemy('zombie', 1, 1)
    combat = CombatSystem()
    result = combat.resolve_player_attack(player, enemy)
    assert result.hit == True
```

`tests/domain/test_level_manager.py`:

```python
def test_advance_to_final_level():
    manager = LevelManager()
    manager.current_level_number = 21
    assert manager.advance_to_next_level() == False
```

`tests/integration/test_full_game.py`:

```python
def test_full_game_flow():
    session = GameSession(test_mode=True)
    # Движение
    success = session.process_player_action('move', (1, 0))
    assert success == True
    # Переключение режима
    mode = session.toggle_rendering_mode()
    assert mode == '3d'
    assert session.position_sync.validate_sync() == True
```

**Запусти:**

```bash
pytest tests/ -v
```

**Коммит:**

```bash
git commit -m "Add: Unit and integration tests"
```

---

### ЭТАП 4: ДОКУМЕНТАЦИЯ И ПРОВЕРКА

#### Шаг 4.1: Документация (1 час)

**Создай:** `docs/ARCHITECTURE.md` с описанием:

- Многослойной архитектуры
- Описанием всех систем
- Диаграммами взаимодействия

**Создай:** `docs/REFACTORING.md` с метриками до/после

**Обнови:** `README.md` с новыми возможностями

**Коммит:**

```bash
git commit -m "Docs: Add architecture and refactoring documentation"
```

---

#### Шаг 4.2: Финальная проверка

**Запусти:**

```bash
# Тесты
pytest tests/ -v --cov=domain --cov=data

# Линтеры
pylint domain/ data/
flake8 domain/ data/

# Игру
python main.py
```

**Проверь вручную:**

- [ ] Игра запускается в 2D
- [ ] Переключение в 3D работает
- [ ] Сохранение/загрузка работает
- [ ] Бой с врагами работает
- [ ] Переход между уровнями работает

**Финальный коммит:**

```bash
git commit -m "Release: Version 2.0 - Complete refactoring"
git tag v2.0.0
```

---

## ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

| Метрика                  | До             | После      |
| ------------------------------- | ---------------- | --------------- |
| Размер GameSession        | 900 строк   | ~200 строк |
| Обязанностей        | 12               | 3               |
| Покрытие тестами | 0%               | 75%+            |
| Дублирование 2D/3D  | Да             | Нет          |
| Координаты            | float/int        | int             |
| Сохранение            | Неполное | Полное    |

---

## ВАЖНЫЕ ПРАВИЛА

1. ✅ **НЕ ПРОПУСКАЙ шаги** - выполняй строго последовательно
2. ✅ **КОММИТЬ после каждого шага** с осмысленным сообщением
3. ✅ **ЗАПУСКАТЬ игру** после критических изменений
4. ✅ **ПИСАТЬ тесты** для новых компонентов
5. ❌ **НЕ ДЕЛАЙ несколько шагов одновременно**
6. ❌ **НЕ КОММИТЬ нерабочий код**

---

## НАЧНИ РАБОТУ

Подтверди, что понял план, и начни с **Этапа 0, Шаг 0.1**.
После каждого шага сообщай о прогрессе.

Удачи! 🚀

```

***

Этот промпт можно скопировать и передать AI-ассистенту для пошагового выполнения рефакторинга.
```
