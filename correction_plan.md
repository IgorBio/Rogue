# План исправлений 3D Rogue

## Анализ ручного тестирования

1. **W/S не работают в 3D**
   - Вероятная причина: после 3D-шага публикуется `CharacterMovedEvent`, а `ViewManager._on_character_moved()` всегда синхронизирует камеру с персонажем и сбрасывает дробное смещение в центр клетки. При `move_speed=0.3` камера не переходит в следующую клетку, поэтому движение визуально "откатывается".
   - Затронутые файлы: `presentation/view_manager.py`, `domain/services/movement_handler.py`, `presentation/camera/controller.py`.

2. **При возврате в 2D позиция сбрасывается на начало уровня**
   - Следствие пункта выше: персонаж фактически не двигается по сетке, поэтому в 2D отображается исходная клетка.

## Приоритизированный план исправлений

### High

1. **Убрать "snap back" камеры при 3D-движении**
   - Добавить признак 3D-движения в событие или отдельный флаг, чтобы `ViewManager` не пересинхронизировал камеру в 3D.
   - Варианты:
     - Расширить `CharacterMovedEvent` (например, `is_3d` или `sync_camera`) и заполнять при 3D-движении.
     - В `ViewManager._on_character_moved()` пропускать синхронизацию камеры при 3D.
   - Файлы: `domain/events.py`, `domain/game_session.py` (publish), `domain/services/movement_handler.py`, `presentation/view_manager.py`.

2. **Открытые двери не рендерятся в 3D**
   - В `raycasting.cast_ray()` луч останавливается только на `is_wall()` или `not is_walkable()`. Открытая дверь walkable, поэтому луч проходит.
   - Исправить: считать дверь "хитом" независимо от `is_walkable`.
   - Файлы: `presentation/rendering/raycasting.py` (при необходимости `domain/entities/level.py`).

3. **`CameraController.set_position()` не изменяет реальную позицию камеры**
   - Сейчас пишет в `camera.x`/`camera.y`, но у `Camera` нет сеттеров.
   - Исправить на `camera.set_position(x, y)`.
   - Файл: `presentation/camera/controller.py`.

4. **Валидация позиции камеры при загрузке**
   - `ViewManager.apply_camera_state()` не проверяет, что позиция камеры проходима.
   - Добавить проверку `level.is_walkable()` и корректный fallback.
   - Файл: `presentation/view_manager.py`.

### Medium

5. **Приоритеты взаимодействия F/Space**
   - Сейчас враги/предметы перекрывают двери.
   - Задать явный приоритет: двери > враги > предметы > выход.
   - Файл: `domain/services/action_processor.py`.

6. **Индикация интерактивных объектов в 3D**
   - Reticle реагирует только на врагов.
   - Добавить состояния для `item/door/exit`.
   - Файлы: `presentation/ui/combat_feedback.py`, `presentation/game_ui.py`.

7. **Кэш raycasting при неподвижной камере**
   - `cast_fov_rays()` вызывается каждый кадр.
   - Ввести кэш по (позиция, угол) камеры.
   - Файл: `presentation/renderer_3d.py`.

8. **FOV спрайтов фиксирован на 60**
   - `SpriteRenderer` не учитывает `camera.fov`.
   - Передавать реальное значение при рендере.
   - Файлы: `presentation/renderer_3d.py`, `presentation/rendering/sprite_renderer_3d.py`.

9. **`collision_radius` не используется**
   - `_is_position_valid()` не вызывается.
   - Использовать его внутри `_try_move()`.
   - Файл: `presentation/camera/controller.py`.

### Low

10. **Текстуры дверей по цветам ключей**
    - Добавить уникальные текстуры/паттерны для цветов.
    - Файл: `presentation/rendering/texture_system.py`.

11. **Плавное движение/повороты (UX)**
    - Опциональная интерполяция.
    - Файл: `presentation/camera/controller.py`.

12. **Более выразительная 3D-обратная связь**
    - Реализовать flash/overlay вместо заглушки.
    - Файл: `presentation/ui/combat_feedback.py`.

