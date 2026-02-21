import pytest
from domain.entities.character import Character
from domain.entities.position import Position


class TestCharacterPositionIntegration:
    def test_character_creation_with_int(self):
        char = Character(10, 20)
        assert char.position == (10, 20)
        assert char.get_x() == 10
        assert char.get_y() == 20

    def test_character_creation_with_float(self):
        char = Character(10.7, 20.3)
        assert char.position == (10, 20)
        assert char.get_x() == 10
        assert char.get_y() == 20

    def test_position_property_returns_tuple(self):
        char = Character(15, 25)
        pos = char.position
        assert isinstance(pos, tuple)
        assert pos == (15, 25)

    def test_position_obj_property_returns_position(self):
        char = Character(15, 25)
        pos_obj = char.position_obj
        assert isinstance(pos_obj, Position)
        assert pos_obj.x == 15
        assert pos_obj.y == 25

    def test_move_to_with_int(self):
        char = Character(0, 0)
        char.move_to(10, 20)
        assert char.position == (10, 20)
        assert char.get_x() == 10
        assert char.get_y() == 20

    def test_move_to_with_float(self):
        char = Character(0, 0)
        char.move_to(10.9, 20.1)
        assert char.position == (10, 20)
        assert char.get_x() == 10
        assert char.get_y() == 20

    def test_move_by_method(self):
        char = Character(10, 10)
        char.move_by(3, -2)
        assert char.position == (13, 8)
        char.move_by(-5, 5)
        assert char.position == (8, 13)

    def test_move_by_with_float_delta(self):
        char = Character(10, 10)
        char.move_by(2.7, -1.3)
        assert char.position == (12, 9)  # int(2.7)=2, int(-1.3)=-1

    def test_get_x_and_get_y(self):
        char = Character(15, 25)
        x = char.get_x()
        y = char.get_y()
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert x == 15
        assert y == 25


class TestCharacterDistanceMethods:
    def test_distance_to_position(self):
        char = Character(0, 0)
        target = Position(3, 4)
        distance = char.distance_to(target)
        assert distance == 5.0

    def test_distance_to_tuple(self):
        char = Character(0, 0)
        distance = char.distance_to((3, 4))
        assert distance == 5.0

    def test_manhattan_distance_to_position(self):
        char = Character(0, 0)
        target = Position(3, 4)
        distance = char.manhattan_distance_to(target)
        assert distance == 7

    def test_manhattan_distance_to_tuple(self):
        char = Character(0, 0)
        distance = char.manhattan_distance_to((3, 4))
        assert distance == 7

    def test_distance_to_self(self):
        char = Character(10, 10)
        distance = char.distance_to((10, 10))
        assert distance == 0.0
        manhattan = char.manhattan_distance_to((10, 10))
        assert manhattan == 0


class TestCharacterAdjacency:
    def test_adjacent_horizontal(self):
        char = Character(10, 10)
        assert char.is_adjacent_to((11, 10)) == True
        assert char.is_adjacent_to((9, 10)) == True

    def test_adjacent_vertical(self):
        char = Character(10, 10)
        assert char.is_adjacent_to((10, 11)) == True
        assert char.is_adjacent_to((10, 9)) == True

    def test_adjacent_diagonal(self):
        char = Character(10, 10)
        assert char.is_adjacent_to((11, 11)) == True
        assert char.is_adjacent_to((9, 9)) == True

    def test_not_adjacent(self):
        char = Character(10, 10)
        assert char.is_adjacent_to((12, 10)) == False
        assert char.is_adjacent_to((10, 12)) == False
        assert char.is_adjacent_to((12, 12)) == False

    def test_not_adjacent_to_self(self):
        char = Character(10, 10)
        assert char.is_adjacent_to((10, 10)) == False

    def test_adjacent_with_position_object(self):
        char = Character(10, 10)
        adjacent_pos = Position(11, 10)
        not_adjacent_pos = Position(12, 10)
        assert char.is_adjacent_to(adjacent_pos) == True
        assert char.is_adjacent_to(not_adjacent_pos) == False


class TestCharacterBackwardCompatibility:
    def test_position_comparison_with_tuple(self):
        char = Character(10, 20)
        assert char.position == (10, 20)
        assert (10, 20) == char.position

    def test_position_unpacking(self):
        char = Character(15, 25)
        x, y = char.position
        assert x == 15
        assert y == 25

    def test_position_indexing(self):
        char = Character(15, 25)
        assert char.position[0] == 15
        assert char.position[1] == 25

    def test_old_code_still_works(self):
        char = Character(10, 10)
        x, y = char.position
        assert x == 10 and y == 10
        char.move_to(20, 30)
        assert char.position == (20, 30)
        assert char.get_x() == 20
        assert char.get_y() == 30


class TestCharacterRepr:
    def test_repr_shows_tuple_position(self):
        char = Character(10, 20)
        repr_str = repr(char)
        assert "pos=(10, 20)" in repr_str
        assert "hp=" in repr_str
        assert "str=" in repr_str
        assert "dex=" in repr_str


class TestCharacterMovementScenarios:
    def test_movement_sequence(self):
        char = Character(0, 0)
        char.move_to(5, 5)
        assert char.position == (5, 5)
        char.move_by(3, -2)
        assert char.position == (8, 3)
        char.move_to(10, 10)
        assert char.position == (10, 10)
        assert char.get_x() == 10
        assert char.get_y() == 10

    def test_movement_with_mixed_types(self):
        char = Character(10.5, 20.7)
        assert char.position == (10, 20)
        char.move_to(15.9, 25.1)
        assert char.position == (15, 25)
        char.move_by(2.8, -1.2)
        assert char.position == (17, 24)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
