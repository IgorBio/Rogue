from types import SimpleNamespace

from domain.services.movement_handler import MovementHandler
from domain.services.action_processor import ActionProcessor


class DummyCamera:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.grid_position = (int(x), int(y))


class DummyController:
    def __init__(self, camera):
        self.camera = camera

    def move_forward(self):
        self.camera.x += 0.5
        self.camera.y += 0.5
        self.camera.grid_position = (int(self.camera.x), int(self.camera.y))
        return True

    def move_backward(self):
        return True

    def strafe_left(self):
        return True

    def strafe_right(self):
        return True

    def get_entity_in_front(self, level):
        return (level.exit_position, "exit", 0.0)

    def try_open_door(self, character):
        return False, "No door nearby"


class DummySession:
    def __init__(self):
        self.character = SimpleNamespace(position=(0, 0), move_to=lambda x, y: None)
        self.level = SimpleNamespace(exit_position=(1, 1))
        self.message = ""
        self._camera = DummyCamera(0.5, 0.5)
        self._controller = DummyController(self._camera)
        self._advanced = False

    def get_camera(self):
        return self._camera

    def get_camera_controller(self):
        return self._controller

    def notify_character_moved(self, from_pos, to_pos, sync_camera=False):
        pass

    def process_enemy_turns(self):
        pass

    def advance_level(self):
        self._advanced = True
        return True

    def is_3d_mode(self):
        return True


def test_movement_handler_triggers_exit():
    session = DummySession()
    handler = MovementHandler(session)
    assert handler.handle_3d_movement("forward") is True
    assert session._advanced is True


def test_action_processor_interact_exit():
    session = DummySession()
    processor = ActionProcessor(session)
    result = processor._handle_3d_interact()
    assert result is True
    assert session._advanced is True
