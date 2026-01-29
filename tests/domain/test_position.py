"""
Тесты для системы координат Position.
"""

import pytest
from domain.entities.position import Position, create_position, positions_equal


class TestPositionCreation:
    """Тесты создания Position"""
    
    def test_create_from_int(self):
        pos = Position(10, 20)
        assert pos.x == 10
        assert pos.y == 20
    
    def test_create_from_float(self):
        """Float автоматически приводится к int"""
        pos = Position(10.7, 20.3)
        assert pos.x == 10
        assert pos.y == 20
        assert isinstance(pos.x, int)


class TestPositionEquality:
    """Тесты сравнения"""
    
    def test_equality_with_tuple(self):
        pos = Position(10, 20)
        assert pos == (10, 20)
    
    def test_float_to_int_equality(self):
        """Position(10.7, 20.3) == (10, 20)"""
        pos = Position(10.7, 20.3)
        assert pos == (10, 20)
    
    def test_hash_for_set(self):
        """Position можно использовать в set"""
        pos1 = Position(10, 20)
        pos2 = Position(10, 20)
        pos_set = {pos1, pos2}
        assert len(pos_set) == 1  # Дубликат


class TestPositionUpdate:
    """Тесты обновления"""
    
    def test_update_from_float(self):
        pos = Position(0, 0)
        pos.update(5.9, 7.1)
        assert pos.x == 5
        assert pos.y == 7
    
    def test_move_by(self):
        pos = Position(10, 10)
        pos.move_by(3, -2)
        assert pos == (13, 8)


class TestPositionDistance:
    """Тесты расстояний"""
    
    def test_euclidean_distance(self):
        pos1 = Position(0, 0)
        pos2 = Position(3, 4)
        assert pos1.distance_to(pos2) == 5.0
    
    def test_manhattan_distance(self):
        pos1 = Position(0, 0)
        pos2 = Position(3, 4)
        assert pos1.manhattan_distance_to(pos2) == 7


class TestPositionAdjacency:
    """Тесты соседства"""
    
    def test_adjacent_horizontal(self):
        pos1 = Position(10, 10)
        pos2 = Position(11, 10)
        assert pos1.is_adjacent_to(pos2) == True
    
    def test_not_adjacent(self):
        pos1 = Position(10, 10)
        pos2 = Position(12, 10)
        assert pos1.is_adjacent_to(pos2) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
