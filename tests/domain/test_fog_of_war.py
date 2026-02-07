"""
Tests for FogOfWar visibility behavior.
"""

from domain.fog_of_war import FogOfWar
from domain.entities.level import Level
from domain.entities.room import Room
from domain.entities.corridor import Corridor
from domain.key_door_system import Door, KeyColor


def _build_level():
    level = Level(1)
    room = Room(1, 1, 5, 5)  # interior tiles: x=2..4, y=2..4
    level.add_room(room)
    level.starting_room_index = 0

    corridor = Corridor()
    corridor.add_tile(6, 3)
    corridor.add_tile(7, 3)
    level.add_corridor(corridor)

    level.doors = [Door(KeyColor.RED, 1, 3)]
    return level


def test_room_visibility_includes_doors_on_walls():
    level = _build_level()
    fow = FogOfWar(level)

    fow.update_visibility((2, 2))

    assert (1, 3) in fow.visible_tiles
    assert fow.is_position_visible(1, 3) is True


def test_corridor_visibility_uses_visible_tiles():
    level = _build_level()
    fow = FogOfWar(level)

    fow.update_visibility((6, 3))

    assert (6, 3) in fow.visible_tiles
    assert fow.is_position_visible(6, 3) is True
    assert fow.is_position_visible(0, 0) is False


def test_is_tile_visible_matches_visible_tiles():
    level = _build_level()
    fow = FogOfWar(level)

    fow.update_visibility((2, 2))

    assert fow.is_tile_visible(2, 2) is True
    assert fow.is_tile_visible(1, 1) is False
