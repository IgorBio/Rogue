"""
Tests for door visibility under Fog of War in 2D rendering.
"""

from domain.fog_of_war import FogOfWar
from domain.entities.level import Level
from domain.entities.room import Room
from domain.entities.corridor import Corridor
from domain.key_door_system import Door, KeyColor


def _build_level_with_door():
    level = Level(1)
    room = Room(1, 1, 5, 5)
    level.add_room(room)
    level.starting_room_index = 0

    corridor = Corridor()
    corridor.add_tile(6, 3)
    corridor.add_tile(7, 3)
    level.add_corridor(corridor)

    level.doors = [Door(KeyColor.RED, 1, 3)]
    return level


def test_door_visible_in_room_tiles():
    level = _build_level_with_door()
    fow = FogOfWar(level)

    fow.update_visibility((2, 2))

    assert fow.is_position_visible(1, 3) is True


def test_door_not_visible_outside_fow():
    level = _build_level_with_door()
    fow = FogOfWar(level)

    fow.update_visibility((6, 3))

    assert fow.is_position_visible(1, 3) is False
