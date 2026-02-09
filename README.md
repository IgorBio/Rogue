# Rogue

A classic rogue-like game in the terminal.


#### 1.1 Нарушение разделения слоев (Layer Separation Violation)

* **Проблема** : Domain layer (`GameSession`) напрямую зависит от presentation layer (`Camera`, `CameraController`)
* **Места нарушения** :
* `domain/game_session.py`: свойства `camera`, `camera_controller`
* Прямая зависимость domain → presentation нарушает Clean Architecture


#### Убрать camera из Domain

 **Цель** : Разорвать зависимость domain → presentation

python

```python
# domain/game_session.py - УДАЛИТЬ свойства camera/camera_controller

# ВМЕСТО:
@property
defcamera(self):
if self._camera_provider isNone:
returnNone
returngetattr(self._camera_provider,'camera',None)

# ИСПОЛЬЗОВАТЬ события для координации:
# presentation/view_manager.py уже подписан на события и управляет камерой
```

 **Изменения** :

1. Удалить `_camera_provider` из `GameSession.__init__()`
2. Удалить свойства `camera`, `camera_controller`, `get_camera()`, `get_camera_controller()`
3. Presentation слой полностью управляет камерой через события
4. `GameUI` передает camera в renderer напрямую, без запроса из session

 **Файлы** :

* `domain/game_session.py`: удалить ~30 строк
* `presentation/game_ui.py`: изменить `_render_game_3d()` для получения camera из ViewManager
* `main.py`: убрать передачу `camera_provider` в GameSession
