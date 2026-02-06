# Код-ревью проекта Rogue

## 🔴 Критические проблемы

### 1. Небезопасное подавление исключений

 **Местоположение** : Повсеместно в проекте (движок событий, обработчики, рендеринг)

```python
# domain/event_bus.py
def publish(self, event: Any) -> None:
    for callback in callbacks:
        try:
            callback(event)
        except Exception:
            pass  # ❌ Полностью скрывает ошибки
```

 **Проблемы** :

* Невозможно отладить баги в подписчиках событий
* Критические ошибки игнорируются молча
* Нарушает принцип "fail fast"

 **Рекомендация** :

```python
def publish(self, event: Any) -> None:
    for callback in callbacks:
        try:
            callback(event)
        except Exception as e:
            log_exception(e, f"Event handler for {type(event).__name__}")
            # Опционально: re-raise для критических ошибок
```

### 2. Утечка памяти через глобальные синглтоны

 **Местоположение** : `domain/event_bus.py`, `presentation/view_manager.py`

```python
# Глобальные экземпляры никогда не очищаются
event_bus = EventBus()
view_manager = ViewManager()
```

 **Проблемы** :

* Подписки накапливаются между сессиями игры
* Невозможно полностью сбросить состояние
* Проблемы в тестах из-за shared state

 **Рекомендация** :

* Использовать dependency injection вместо глобалов
* Добавить явное управление жизненным циклом
* В тестах обязательно вызывать `reset_event_bus()`

### 3. Неконтролируемая обработка ошибок сохранения

 **Местоположение** : `domain/services/level_manager.py:149`

```python
try:
    session.save_to_file()
except (OSError, IOError):
    pass  # ❌ Игнорируем провал сохранения
```

 **Проблема** : Игрок не знает, что прогресс не сохранился.

 **Рекомендация** :

```python
try:
    session.save_to_file()
except (OSError, IOError) as e:
    log_exception(e, "Autosave failed")
    session.message += " [Warning: Autosave failed]"
```

---

## 🟡 Серьёзные проблемы

### 4. Неявная сериализация позиций

 **Местоположение** : `domain/entities/position.py`, сохранения

```python
# Position хранит только int, но Camera требует float
self._x = int(x)  # Теряем точность для камеры!
```

 **Проблемы** :

* Рассинхронизация между `Position` (int) и `Camera` (float)
* Сложная логика конвертации в нескольких местах
* При загрузке save-файла камера телепортируется

 **Рекомендация** :

* Сделать `Position` immutable value object
* Добавить явный `CameraPosition(Position, offset_x, offset_y)`
* Документировать координатные системы

### 5. Circular dependency через type hints

 **Местоположение** : Множество файлов

```python
if TYPE_CHECKING:
    from domain.game_session import GameSession
```

 **Проблема** : Циклические импорты скрыты через `TYPE_CHECKING`, затрудняет рефакторинг.

 **Рекомендация** :

* Вынести интерфейсы/протоколы в отдельные модули
* Использовать `Protocol` для зависимостей
* Пересмотреть архитектуру для устранения циклов

### 6. Хрупкая десериализация состояния машины

 **Местоположение** : `data/save_manager.py:195-210`

```python
# Сложная логика определения состояния при загрузке
if saved_victory:
    _saved_state = GameState.VICTORY
elif saved_game_over:
    _saved_state = GameState.GAME_OVER
# ... 5 уровней if/elif
```

 **Проблемы** :

* Легко сломать добавлением нового состояния
* Не сохраняется фактическое состояние машины
* Потенциальные баги при загрузке старых сохранений

 **Рекомендация** :

```python
# В save:
'game_state': self.state_machine.current_state.name

# В load:
state = GameState[save_data['game_state']]
game_session.state_machine.restore_state(state)
```

### 7. Неоптимальная FOW проверка

 **Местоположение** : `domain/fog_of_war.py:148-178`

```python
def is_position_visible(self, x, y):
    # Проверяется для каждого врага/предмета при каждом рендере
    if self.current_room_index is not None:
        room = self.level.rooms[self.current_room_index]
        return room.contains_point(x, y)
    # ... ещё логика
```

 **Проблема** : O(n) проверки для каждой сущности каждый кадр.

 **Рекомендация** :

* Кэшировать `visible_positions: Set[Tuple[int, int]]`
* Обновлять только при движении игрока
* Использовать `(x, y) in visible_positions`

---

## 🟢 Улучшения кода

### 8. Магические строки вместо enum

 **Местоположение** : Много мест

```python
# domain/services/action_processor.py
if action_type == 'toggle_mode':  # ❌ Строка
    ...
```

 **Есть частично** : `ActionType` enum уже создан, но используется непоследовательно.

 **Рекомендация** : Строго использовать `ActionType` повсюду.

### 9. Избыточная вложенность в рендеринге

 **Местоположение** : `presentation/renderer_2d.py:150-250`

```python
def _render_with_fog(self, level, character, fog_of_war):
    in_corridor = fog_of_war.get_current_corridor() is not None
    if in_corridor:
        self._render_corridor_line_of_sight(...)
    else:
        self._render_room_based_fog(...)
        # 100+ строк вложенных условий
```

 **Рекомендация** :

* Извлечь методы для каждого типа рендеринга
* Использовать pattern Visitor или Strategy

### 10. Хардкод размеров экрана

 **Местоположение** : `presentation/renderer_3d.py:30`

```python
def __init__(self, stdscr, viewport_width=70, viewport_height=20, ...):
```

 **Проблема** : Не адаптируется под размер терминала.

 **Рекомендация** :

```python
max_y, max_x = stdscr.getmaxyx()
viewport_width = min(70, max_x - 10)
viewport_height = min(20, max_y - 15)
```

---

## 📊 Статистика проблем

| Категория                   | Критические | Серьёзные | Улучшения | Итого |
| ------------------------------------ | ---------------------- | ------------------ | ------------------ | ---------- |
| Ошибки                         | 3                      | 4                  | 0                  | 7          |
| Архитектура               | 0                      | 2                  | 3                  | 5          |
| Производительность | 0                      | 1                  | 0                  | 1          |
| Читаемость                 | 0                      | 0                  | 2                  | 2          |

---

## ✅ Что сделано хорошо

1. **Разделение слоёв** : Domain/Presentation/Data чётко разделены
2. **Event-driven статистика** : Отличное использование EventBus
3. **Dependency injection** : Фабрики для Statistics и SaveManager
4. **State Machine** : Явное управление состояниями игры
5. **Coordinator pattern** : `SessionCoordinator` разгружает `GameSession`
6. **Тестируемость** : Много кода можно тестировать без curses

---

## 🎯 Приоритеты исправлений

### Немедленно (до следующего релиза):

1. Добавить логирование в `event_bus.publish()`
2. Предупреждать игрока о провале автосохранения
3. Фиксить десериализацию GameState

### Скоро (следующий спринт):

4. Кэширование FOW проверок
5. Устранение утечек памяти в глобалах
6. Валидация в конструкторах
7. Устранение циклических зависимостей
8. Оптимизация рендеринга

---

## 📝 Итоговая оценка

**Оценка кода: 7/10**

 **Плюсы** :

* Продуманная архитектура
* Хорошее разделение ответственности
* Event-driven подход
* Поддержка 2D/3D режимов

 **Минусы** :

* Подавление критических ошибок
* Утечки памяти в глобалах
* Сложность `GameSession`
* Хрупкая сериализация

 **Вывод** : Солидный проект с хорошей архитектурой, но требующий доработки обработки ошибок и устранения технического долга.
