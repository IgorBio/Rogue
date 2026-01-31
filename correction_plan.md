# Рефакторинг domain-слоя — план коррекции

---

## Этап 1. Устранение дублирования констант

**Проблемы:**

* `ItemType`, `EnemyType`, `StatType`, `ENEMY_STATS` определены одновременно в `config/game_config.py` и `utils/constants.py`.
* `game_session.py` повторно определяет `TEST_MODE_HEALTH/MAX_HEALTH/STRENGTH/DEXTERITY`, `DEFAULT_CAMERA_ANGLE/FOV`, `ADJACENT_OFFSETS` — все они уже есть в `GameConfig`, `PlayerConfig`.

**Действия:**

1. Удалить из `utils/constants.py` классы `ItemType`, `EnemyType`, `StatType` и словарь `ENEMY_STATS` — единственный источник — `config/game_config.py`.
2. В `game_session.py` убрать локальные константы `TEST_MODE_*`, `DEFAULT_CAMERA_*`, `ADJACENT_OFFSETS`; заменить их на `GameConfig.TEST_MODE_STATS[...]`, `GameConfig.DEFAULT_CAMERA_ANGLE`, `PlayerConfig.ADJACENT_OFFSETS`.
3. Поискать и исправить все импорты этих типов из `utils/constants.py` по всему проекту.

---

## Этап 2. Исправление нарушений границ слоёв в domain/services

**Проблемы:**

* `action_processor.py` импортирует `presentation.input_handler.InputHandler` и `utils.input_handler_3d.InputHandler3D` — это пересечение границы domain → presentation/utils.
* `enemy_turn_processor.py` импортирует `utils.pathfinding.get_distance` — утилита используется как зависимость бизнес-логики.
* `position_synchronizer.py` импортирует `utils.raycasting.Camera` — объект презентации попадает в сигнатуры доменного сервиса.

**Действия:**

1. В `action_processor.py` заменить сравнения с `InputHandler.ACTION_*` и `InputHandler3D.ACTION_*` на простые строковые константы, объявленные внутри самого `ActionProcessor`. Удалить оба импорта.
2. В `enemy_turn_processor.py` заменить вызов `get_distance` на `Position.manhattan_distance_to`  — зависимость на `utils.pathfinding` удалить.
3. В `position_synchronizer.py` убрать импорт `Camera`; в сигнатурах заменить `Camera` на обобщённый `duck-type` (любой объект с `.x`, `.y`, `.angle`, `.grid_position`, `.set_position()`). Импорт `Character` оставить — он из того же слоя.

---

## Этап 3. Исправление пропущенного перехода состояния LEVEL_TRANSITION

**Проблема:**
`LevelManager.advance_and_setup()` вызывает `session.complete_level_transition()` (переход из `LEVEL_TRANSITION → PLAYING`), но перед этим никто не вызвал `session.begin_level_transition()`. Состояние `LEVEL_TRANSITION` никогда не наступает; переход `PLAYING → PLAYING` не зарегистрирован в `StateMachine.TRANSITIONS` — код работает только потому, что `complete_level_transition` защищён `if is_waiting_for_selection`, а не проверкой текущего состояния.

**Действия:**

1. В `LevelManager.advance_and_setup()`, сразу после проверки `new_level_num is None` (но перед генерацией уровня), добавить вызов `session.begin_level_transition()`.
2. Убедиться, что `complete_level_transition()` вызывается только после этого и только из состояния `LEVEL_TRANSITION`.

---

## Этап 4. Исправление unsafe-ресторации состояния из сохранения

**Проблема:**
`save_manager.restore_game_session()` восстанавливает `game_over`, `victory`, `player_asleep` через property-сеттеры, которые вызывают `state_machine.transition_to()`. После `__init__` session уже в `PLAYING`. Сеттеры идут подряд: сначала `game_over`, потом `victory`. Если в corrupt-save оба `True` — второй `transition_to(VICTORY)` из `GAME_OVER` выбросит `ValueError` (терминальное состояние).

**Действия:**

1. В `restore_game_session` убрать присвоение через `session.game_over = ...` / `session.victory = ...` / `session.player_asleep = ...`.
2. После полной ресторации всех полей вызвать один метод `session.state_machine.restore_state(saved_state)`, который без валидации переходов просто устанавливает `_state` из сохранённого значения.
3. Добавить в `StateMachine` метод `restore_state(state: GameState)` — он не проверяет допустимость перехода, он для использования исключительно при загрузке сохранения.

---

## Этап 5. Исправление двойного подсчёта статистики и двойной обработки смерти врага в 3D-бою

**Проблемы:**

* `CameraController.attack_entity_in_front()` создаёт свой экземпляр `CombatSystem()` без `statistics`, вызывает `resolve_player_attack`, сам удаляет вражvrага из комнаты и добавляет текст о treasure в сообщение. Затем `ActionProcessor._handle_3d_attack()` вызывает `finalize_attack_result()`, который попытается записать те же stats и снова запустить enemy turns. Treasure добавляется в сообщение, но `backpack.treasure_value` не обновляется в `CameraController`.
* `EnemyTurnProcessor` вызывает `session.stats.record_hit_taken(damage)` после того как `CombatSystem.resolve_enemy_attack()` уже записал тот же удар через `self.statistics.record_hit_taken()`. Результат — `hits_taken` и `damage_received` удваиваются.

**Действия:**

1. В `CameraController.attack_entity_in_front()` убрать создание `CombatSystem`, вызов `resolve_player_attack`, удаление врага и формирование сообщения. Метод должен только обнаружить врага впереди и вернуть его — вся логика боя перенесётся в `ActionProcessor._handle_3d_attack()`.
2. В `ActionProcessor._handle_3d_attack()` использовать уже существующий `session.combat_system` (с `statistics`), вызвать `combat_system.process_player_attack(session, enemy)` — он уже полностью обрабатывает удар, удаление врага, treasure и сообщение.
3. В `EnemyTurnProcessor.process_enemy_turns()` удалить строку `session.stats.record_hit_taken(...)` — эта запись уже делается внутри `CombatSystem.resolve_enemy_attack()` через `self.statistics`.

---

## Этап 6. Удаление мёртвого кода

**Проблемы:**

* Класс `InputMapper3D` в `utils/input_handler_3d.py` полностью не используется — его роль выполняет `ActionProcessor`.
* В `game_session.py` методы `_process_action_2d` и `_process_action_3d` — тонкие обёртки, которые просто делегируют в `ActionProcessor`. Они существуют "для обратной совместимости", но сам `ActionProcessor` уже перенаправляет через `getattr(session, ...)` — круговая индекция.
* `domain/__init__.py` экспортирует `get_visible_tiles`, которая не используется внутри domain.

**Действия:**

1. Удалить класс `InputMapper3D` из `utils/input_handler_3d.py`.
2. Удалить из `game_session.py` методы-обёртки `_process_action_2d`, `_process_action_3d`.
3. В `ActionProcessor.process_action()` убрать `getattr(self.session, '_process_action_3d', None)` — обращаться только к своим `self._process_action_2d` / `self._process_action_3d`.
4. Убрать `get_visible_tiles` из экспорта `domain/__init__.py` (сама функция в `fog_of_war.py` остаётся — она вызывается `FogOfWar` внутри модуля).

---

## Этап 7. Замена bare-except в LevelManager

**Проблема:**
`LevelManager.advance_and_setup()` оборачивает в `try/except Exception: pass` практически каждый вызов. Это маскирует ошибки инвариантов (например, потеря ключей, невалидная генерация уровня) и существенно затрудняет отладку.

**Действия:**

1. Убрать голые `except: pass` вокруг критических операций: очистка ключей, запись уровня в stats, генерация уровня.
2. Для действительно опциональных вызовов (автосохранение, сообщение о сложности) оставить `except Exception` с логированием (`logging.warning(...)` или хотя бы `print`).
