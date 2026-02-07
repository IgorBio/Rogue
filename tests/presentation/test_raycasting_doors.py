from domain.entities.level import Level
from domain.key_door_system import Door, KeyColor
from presentation.rendering.raycasting import _determine_wall_hit


def test_determine_wall_hit_locked_and_open_door():
    level = Level(1)
    door = Door(KeyColor.RED, 2, 3)
    level.doors.append(door)

    wall_type, door_hit = _determine_wall_hit(level, 2, 3)
    assert wall_type == "door_locked"
    assert door_hit is door

    door.unlock()
    wall_type, door_hit = _determine_wall_hit(level, 2, 3)
    assert wall_type == "door_open"
    assert door_hit is door


def test_determine_wall_hit_corridor_wall_when_no_room_or_door():
    level = Level(1)
    wall_type, door_hit = _determine_wall_hit(level, 10, 10)
    assert wall_type == "corridor_wall"
    assert door_hit is None
