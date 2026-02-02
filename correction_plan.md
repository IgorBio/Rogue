# План исправления архитектуры Rogue (Clean Architecture)

## Анализ текущей структуры

### Текущие слои
```
config/       - Конфигурация игры
├── game_config.py

data/         - Слой данных (Data Layer)
├── save_manager.py      ⚠️ Импортирует из utils/
├── statistics.py

domain/       - Доменный слой (Domain Layer)
├── entities/             - Сущности
├── services/             - Доменные сервисы
├── enemy_ai.py          ⚠️ Импортирует из utils/
├── *.py                  - Другая бизнес-логика

presentation/ - Слой представления (Presentation Layer)
├── renderer_3d.py       ⚠️ Импортирует из utils/
├── *.py                  - UI, рендеринг, ввод

utils/        - ⚠️ Микс разных ответственностей
├── raycasting.py        - 3D рендеринг (Presentation)
├── camera_controller.py - Управление камерой (Presentation)
├── combat_ui_3d.py      - UI обратная связь (Presentation)
├── input_handler_3d.py  - Обработка ввода (Presentation)
├── minimap_renderer.py  - Рендеринг миникарты (Presentation)
├── sprite_renderer_3d.py- Рендеринг спрайтов (Presentation)
├── texture_system.py    - Система текстур (Presentation)
├── pathfinding.py       - Поиск пути (Domain)
├── sync_helpers.py      - Синхронизация (Presentation)
```

---

## Нарушения принципов Clean Architecture

### 1. Нарушение Dependency Rule
**Проблема:** Слой `data/` импортирует из `utils/`
```python
# data/save_manager.py
from utils.raycasting import Camera              # ❌ Нарушение
from utils.camera_controller import CameraController  # ❌ Нарушение
```

**Проблема:** Слой `domain/` импортирует из `utils/`
```python
# domain/enemy_ai.py
from utils.pathfinding import (
    get_distance,
    get_next_step,
    get_random_adjacent_walkable
)  # ❌ Нарушение
```

### 2. Нарушение Single Responsibility / Layer Boundaries
Папка `utils/` содержит код разных слоев:
- **Presentation**: raycasting, camera_controller, combat_ui_3d, input_handler_3d, minimap_renderer, sprite_renderer_3d, texture_system, sync_helpers
- **Domain**: pathfinding

### 3. Нарушение Abstraction Principle
`data/save_manager.py` работает напрямую с presentation-объектами (Camera), вместо работы через доменные сущности или DTO.

---

## План изменений

### Фаза 1: Перенос pathfinding в Domain Layer

**Исходное место:** `utils/pathfinding.py`
**Новое место:** `domain/services/pathfinding_service.py`

**Действия:**
1. Создать `domain/services/pathfinding_service.py` с содержимым из `utils/pathfinding.py`
2. Обновить импорты в `domain/enemy_ai.py`:
   ```python
   # Было:
   from utils.pathfinding import get_distance, get_next_step, ...
   
   # Стало:
   from domain.services.pathfinding_service import get_distance, get_next_step, ...
   ```
3. Удалить `utils/pathfinding.py`

**Обоснование:** Поиск пути - это бизнес-логика перемещения существ в игре (Domain). Не зависит от UI/рендеринга.

---

### Фаза 2: Перенос presentation-утилит в Presentation Layer

Создать подпакеты в `presentation/` для лучшей организации:

```
presentation/
├── __init__.py
├── rendering/
│   ├── __init__.py
│   ├── raycasting.py           # ← из utils/
│   ├── sprite_renderer_3d.py   # ← из utils/
│   ├── texture_system.py       # ← из utils/
│   └── minimap_renderer.py     # ← из utils/
├── camera/
│   ├── __init__.py
│   ├── camera.py               # ← Camera из utils/raycasting.py
│   ├── controller.py           # ← из utils/camera_controller.py
│   └── sync.py                 # ← объединить camera_sync.py + sync_helpers.py
├── input/
│   ├── __init__.py
│   ├── handler.py              # ← существующий input_handler.py
│   └── handler_3d.py           # ← из utils/input_handler_3d.py
├── ui/
│   ├── __init__.py
│   ├── combat_feedback.py      # ← из utils/combat_ui_3d.py
│   ├── components.py           # ← существующий ui_components.py
│   └── game_ui.py              # ← существующий game_ui.py
├── colors.py
├── renderer.py
├── renderer_3d.py
└── view_manager.py
```

**Действия для каждого файла:**

#### 1. `utils/raycasting.py` → `presentation/rendering/raycasting.py` + `presentation/camera/camera.py`
- Вынести класс `Camera` в `presentation/camera/camera.py`
- Оставить raycast-функции в `presentation/rendering/raycasting.py`

#### 2. `utils/camera_controller.py` → `presentation/camera/controller.py`
- Перенести класс `CameraController`

#### 3. `utils/sync_helpers.py` + `presentation/camera_sync.py` → `presentation/camera/sync.py`
- Объединить синхронизацию в один модуль
- `presentation/camera_sync.py` пометить как deprecated

#### 4. `utils/combat_ui_3d.py` → `presentation/ui/combat_feedback.py`
- Перенести класс `CombatFeedback`

#### 5. `utils/input_handler_3d.py` → `presentation/input/handler_3d.py`
- Перенести класс `InputHandler3D`

#### 6. `utils/minimap_renderer.py` → `presentation/rendering/minimap_renderer.py`
- Перенести класс `MiniMapRenderer`

#### 7. `utils/sprite_renderer_3d.py` → `presentation/rendering/sprite_renderer_3d.py`
- Перенести классы `Sprite` и `SpriteRenderer`

#### 8. `utils/texture_system.py` → `presentation/rendering/texture_system.py`
- Перенести классы `WallTexture` и `TextureManager`

---

### Фаза 3: Обновление зависимостей

#### Обновить `data/save_manager.py`:
```python
# Было:
from utils.raycasting import Camera
from utils.camera_controller import CameraController

# Стало:
from presentation.camera.camera import Camera
from presentation.camera.controller import CameraController
```

**Примечание:** В долгосрочной перспективе, `save_manager.py` должен работать с DTO/словарями, а не напрямую с presentation-объектами. Это требует создания сериализационных мапперов.

#### Обновить `presentation/renderer_3d.py`:
```python
# Было:
from utils.raycasting import Camera, cast_fov_rays, calculate_wall_height
from utils.texture_system import get_texture_manager, TexturedRenderer
from utils.minimap_renderer import MiniMapRenderer
from utils.sprite_renderer_3d import SpriteRenderer

# Стало:
from presentation.camera.camera import Camera
from presentation.rendering.raycasting import cast_fov_rays, calculate_wall_height
from presentation.rendering.texture_system import get_texture_manager, TexturedRenderer
from presentation.rendering.minimap_renderer import MiniMapRenderer
from presentation.rendering.sprite_renderer_3d import SpriteRenderer
```

#### Обновить `main.py`:
```python
# Было:
from utils.raycasting import Camera
from utils.camera_controller import CameraController

# Стало:
from presentation.camera.camera import Camera
from presentation.camera.controller import CameraController
```

#### Обновить `domain/services/position_synchronizer.py` (deprecated методы):
Убрать импорты из presentation, оставить только core-синхронизацию.

---

### Фаза 4: Рефакторинг импортов в тестах

Обновить тестовые файлы:
- `tests/utils/test_camera_position.py` → `tests/presentation/camera/`

---

### Фаза 5: Удаление пустой папки utils/

После переноса всех модулей:
```bash
rm -rf utils/
```

---

## Итоговая архитектура

```
config/         - Конфигурация (без изменений)
data/           - Data Layer (исправлены импорты)
domain/         - Domain Layer (+ pathfinding_service)
presentation/   - Presentation Layer (+ подпакеты)
tests/          - Тесты (обновлены импорты)
main.py         - Точка входа (обновлены импорты)
```

### Правила зависимостей (после исправления)
```
main.py → presentation → domain → config
              ↓              ↓
           data (через абстракции)
```

**Запрещено:**
- ❌ domain → presentation
- ❌ domain → data
- ❌ data → presentation
- ❌ config → что-либо (кроме констант)

**Разрешено:**
- ✅ presentation → domain
- ✅ presentation → config
- ✅ data → domain
- ✅ domain → config
- ✅ main → все слои (композиция)

---

## Приоритеты

1. **Высокий:** Перенос `pathfinding.py` в domain (нарушает Dependency Rule)
2. **Высокий:** Перенос `raycasting.py`, `camera_controller.py` в presentation
3. **Средний:** Обновление импортов в `save_manager.py`, `main.py`
4. **Средний:** Реорганизация presentation в подпакеты
5. **Низкий:** Удаление папки `utils/`

---

## Риски и замечания

1. **Циклические импорты:** При перемещении `pathfinding.py` проверить отсутствие циклов (использовать TYPE_CHECKING если нужно)
2. **Тесты:** Все тесты использующие `utils/` нужно обновить
3. **SaveManager:** Нужен рефакторинг для работы через DTO вместо прямых зависимостей от Camera
