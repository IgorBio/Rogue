# План рефакторинга Rogue (упрощение без потери функциональности)

## Краткий вывод
Проект уже избавился от папки `utils`, но остались дублирующие и неиспользуемые компоненты, которые усложняют поддержку. Ниже — обновленные предложения с учетом замечаний: оставить доменную часть `PositionSynchronizer`, выбрать единый источник action-констант (вариант B), а глубокую перестройку `GameSession` и `SaveManager` отложить как техдолг.

## Что можно убрать целиком
1. `domain/services/service_container.py`
Нет использований в коде и тестах. Оставляет ложное ощущение, что есть DI-контейнер.
Действия: удалить файл, убрать упоминания в комментариях/доках.

2. `domain/services/session_protocol.py`
Не используется нигде. Усложняет чтение, не приносит пользы.
Действия: удалить файл.

3. `presentation/camera_sync.py`
Полный дубль `presentation/camera/sync.py`.
Действия: удалить `presentation/camera_sync.py`, все импорты перевести на `presentation.camera.sync`.

4. `presentation/input/handler_3d.py` (частично)
Блоки `if __name__ == "__main__":` и `test_input_handler_3d()` — неиспользуемый тестовый код в runtime-модуле.
Действия: вынести в `tests/` или удалить.

## Что нельзя удалять сейчас
1. `domain/services/action_types.py`
С учетом замечаний рекомендуется сделать его единым источником action-констант (вариант B), а не удалять.

## Что убрать/сжать частично
1. `domain/services/position_synchronizer.py`
Содержит deprecated-обертки поверх `presentation.camera_sync`, из-за чего domain зависит от presentation.
Действия: удалить deprecated-обертки и оставить только доменную логику:
`sync_character_to_position`, `is_character_moved`, `are_positions_aligned`, `get_character_offset`, `reset_tracking`.

2. `presentation/input_handler.py`
Экземпляр создается, но фактически не используется: `GameUI` делает собственное сопоставление клавиш.
Действия: использовать `InputHandler.get_action()` в `GameUI` (и удалить ручной mapping), либо удалить `InputHandler` целиком. Рекомендуется использовать `InputHandler` для консолидации логики.

## Что можно объединить
1. Camera Sync
Оставить единственный модуль `presentation/camera/sync.py` и использовать его везде.
Файлы для перевода импортов:
- `presentation/view_manager.py`
- `tests/presentation/test_camera_sync.py`
- `domain/services/position_synchronizer.py` (если оставляем)

2. Обработка действий (Action constants)
Сейчас есть дубли строк в:
- `domain/services/action_processor.py`
- `presentation/input_handler.py`
- `presentation/input/handler_3d.py`
- `presentation/game_ui.py`

Рекомендуемый вариант (B):
Использовать `domain/services/action_types.py` как единственный источник.
Для UI и `ActionProcessor`:
- заменить строковые литералы на `ActionType` или алиасы из `action_types.py`.
- централизовать преобразование `str -> ActionType` в одном месте (например, в `GameUI`).

## Что заменить
1. Синхронизацию камеры при смене режима
Сейчас `GameSession.toggle_rendering_mode()` напрямую синхронизирует камеру через `PositionSynchronizer`.
Действия:
1. Упростить `GameSession.toggle_rendering_mode()` до смены режима и сообщения.
2. Синхронизацию выполнять в presentation-слое (например, в `ViewManager`) с использованием `presentation.camera.sync`.
3. Оставить `PositionSynchronizer` в domain только как доменный утилитарный компонент (без обращения к presentation).

2. Зависимость SaveManager от presentation
`data/save_manager.py` напрямую импортирует `Camera` и `CameraController`.
С учетом замечаний это часть более глубокой проблемы: `GameSession` хранит presentation-объекты.
Действия (как техдолг):
1. Перенести `camera`/`camera_controller` полностью в `ViewManager`.
2. В `SaveManager` хранить только примитивный `camera_state`.
3. Восстановление камеры делегировать presentation-слою.

## Подробный план по этапам

### Фаза 1: Чистка мертвого кода
1. Удалить `domain/services/service_container.py`.
2. Удалить `domain/services/session_protocol.py`.
3. Удалить `presentation/camera_sync.py`, обновить импорты на `presentation.camera.sync`.
4. Удалить тестовый код из `presentation/input/handler_3d.py` (перенос в `tests/` при необходимости).

### Фаза 2: Консолидация синхронизации камеры
1. Удалить deprecated-обертки в `domain/services/position_synchronizer.py`, оставить только доменные методы.
2. Обновить `GameSession.toggle_rendering_mode()`:
1. Только смена режима и сообщение.
2. Синхронизацию перенести в presentation-слой (`ViewManager`).
3. Обновить тесты `tests/domain/services/test_position_synchronizer.py` под обновленный, доменный интерфейс.

### Фаза 3: Упрощение input-слоя
1. Использовать `domain/services/action_types.py` как единый источник.
2. Удалить дубли в `InputHandler`, `InputHandler3D`, `ActionProcessor`, `GameUI`.
3. Обновить `tests/domain/test_action_processor.py` на новый источник констант.

### Фаза 4: Архитектурный техдолг (отложить)
1. Убрать `camera` и `camera_controller` из `GameSession`.
2. Перенести управление камерой полностью в `ViewManager`.
3. В `SaveManager` хранить только примитивный `camera_state`.
4. Обновить сериализацию/десериализацию и тесты сохранения.

## Точки изменения (файлы)
- `main.py`
- `presentation/game_ui.py`
- `presentation/view_manager.py`
- `presentation/camera/sync.py`
- `presentation/input_handler.py`
- `presentation/input/handler_3d.py`
- `domain/game_session.py`
- `domain/services/action_processor.py`
- `domain/services/position_synchronizer.py`
- `data/save_manager.py`
- `tests/presentation/test_camera_sync.py`
- `tests/domain/test_action_processor.py`
- `tests/domain/services/test_position_synchronizer.py`

## Риски и проверки
1. Проверить смену режима 2D/3D (камера должна синхронизироваться корректно).
2. Проверить сохранение/загрузку (включая восстановление камеры).
3. Прогнать тесты: `tests/domain`, `tests/presentation`, `tests/data`, `tests/integration`.
