from types import SimpleNamespace

from presentation.camera.camera import Camera
from presentation.camera.controller import CameraController


class _DummyLevel:
    def __init__(self, item):
        self.rooms = [SimpleNamespace(enemies=[], items=[item])]
        self.exit_position = None

    @staticmethod
    def is_wall(x, y):
        return False

    @staticmethod
    def is_walkable(x, y):
        return True


def test_get_entity_in_front_uses_last_viewport_width_when_not_passed():
    camera = Camera(10.0, 10.0, angle=0.0, fov=60.0)

    # Center is ~4 degrees off-axis at distance ~1.35:
    # visible for narrow viewport cone (~20 cols), not visible for fallback 80 cols.
    item = SimpleNamespace(position=(10.85, 9.595))
    level = _DummyLevel(item)
    controller = CameraController(camera, level)

    entity, entity_type, _ = controller.get_entity_in_front(
        level, check_distance=2.0, viewport_width=20
    )
    assert entity_type == "item"
    assert entity is item

    # No viewport_width passed: should still use last viewport width (20), not fallback 80.
    entity2, entity_type2, _ = controller.get_entity_in_front(level, check_distance=2.0)
    assert entity_type2 == "item"
    assert entity2 is item


def test_get_entity_in_front_has_minimum_aim_cone_for_wide_viewport():
    camera = Camera(10.0, 10.0, angle=0.0, fov=60.0)

    # Target at ~4 degrees off-axis and within interaction range.
    # Without a minimum cone, wide viewports make this too strict and miss.
    item = SimpleNamespace(position=(10.846, 9.594))
    level = _DummyLevel(item)
    controller = CameraController(camera, level)

    entity, entity_type, _ = controller.get_entity_in_front(
        level, check_distance=2.0, viewport_width=70
    )
    assert entity_type == "item"
    assert entity is item
