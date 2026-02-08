"""
Тесты для Camera с интеграцией Position.

Проверяет корректность работы Camera после интеграции Position класса.
"""

import pytest
import math
from presentation.camera import Camera
from domain.entities.position import Position
from config.game_config import CameraConfig


class TestCameraPositionIntegration:
    """Тесты интеграции Position в Camera"""

    def test_camera_creation_with_int(self):
        """Создание камеры с int координатами"""
        cam = Camera(10, 20)
        assert cam.x == 10.0
        assert cam.y == 20.0
        assert cam.grid_position == (10, 20)

    def test_camera_creation_with_float(self):
        """Создание камеры с float координатами"""
        cam = Camera(10 + CameraConfig.CAMERA_OFFSET, 20.7)
        assert cam.x == 10 + CameraConfig.CAMERA_OFFSET
        assert cam.y == 20.7
        assert cam.grid_position == (10, 20)  # Grid-aligned

    def test_position_property_returns_float_tuple(self):
        """position property должно возвращать float tuple"""
        cam = Camera(15.3, 25.8)
        pos = cam.position
        assert isinstance(pos, tuple)
        assert pos == (15.3, 25.8)
        assert isinstance(pos[0], float)
        assert isinstance(pos[1], float)

    def test_position_obj_property_returns_position(self):
        """position_obj property должно возвращать Position объект"""
        cam = Camera(15.5, 25.5)
        pos_obj = cam.position_obj
        assert isinstance(pos_obj, Position)
        assert pos_obj.x == 15  # Grid-aligned (int)
        assert pos_obj.y == 25

    def test_grid_position_returns_int_tuple(self):
        """grid_position должно возвращать int tuple"""
        cam = Camera(15.9, 25.1)
        grid_pos = cam.grid_position
        assert isinstance(grid_pos, tuple)
        assert grid_pos == (15, 25)
        assert isinstance(grid_pos[0], int)
        assert isinstance(grid_pos[1], int)

    def test_x_y_properties_return_float(self):
        """x и y properties должны возвращать float"""
        cam = Camera(15.5, 25.5)
        x = cam.x
        y = cam.y

        assert isinstance(x, float)
        assert isinstance(y, float)
        assert x == 15.5
        assert y == 25.5


class TestCameraMovement:
    """Тесты методов перемещения камеры"""

    def test_set_position_with_int(self):
        """Установка позиции с int координатами"""
        cam = Camera(0, 0)
        cam.set_position(10, 20)
        assert cam.x == 10.0
        assert cam.y == 20.0
        assert cam.grid_position == (10, 20)

    def test_set_position_with_float(self):
        """Установка позиции с float координатами"""
        cam = Camera(0, 0)
        cam.set_position(10.7, 20.3)
        assert cam.x == 10.7
        assert cam.y == 20.3
        assert cam.grid_position == (10, 20)

    def test_move_to(self):
        """Метод move_to"""
        cam = Camera(0, 0)
        cam.move_to(15.5, 25.5)
        assert cam.x == 15.5
        assert cam.y == 25.5

    def test_move_forward(self):
        """Движение вперед"""
        cam = Camera(10.0, 10.0, angle=0.0)  # Facing East
        new_x, new_y = cam.move_forward(1.0)

        # Should move 1.0 unit East (positive X)
        assert abs(new_x - 11.0) < 0.01
        assert abs(new_y - 10.0) < 0.01

    def test_move_backward(self):
        """Движение назад"""
        cam = Camera(10.0, 10.0, angle=0.0)  # Facing East
        new_x, new_y = cam.move_backward(1.0)

        # Should move 1.0 unit West (negative X)
        assert abs(new_x - 9.0) < 0.01
        assert abs(new_y - 10.0) < 0.01

    def test_move_strafe(self):
        """Боковое движение (strafe)"""
        cam = Camera(10.0, 10.0, angle=0.0)  # Facing East

        # Strafe right (positive distance)
        new_x, new_y = cam.move_strafe(1.0)
        # Right is perpendicular to East = South (negative Y)
        assert abs(new_x - 10.0) < 0.01
        assert abs(new_y - 11.0) < 0.01  # Note: Y increases south in many coordinate systems

    def test_move_forward_with_angle(self):
        """Движение вперед под углом"""
        cam = Camera(0.0, 0.0, angle=45.0)  # Northeast
        new_x, new_y = cam.move_forward(math.sqrt(2))

        # Should move ~1 unit in both X and Y
        assert abs(new_x - 1.0) < 0.1
        assert abs(new_y - 1.0) < 0.1


class TestCameraRotation:
    """Тесты вращения камеры"""

    def test_rotate_positive(self):
        """Вращение против часовой стрелки"""
        cam = Camera(10, 10, angle=0.0)
        cam.rotate(90.0)
        assert cam.angle == 90.0

    def test_rotate_negative(self):
        """Вращение по часовой стрелке"""
        cam = Camera(10, 10, angle=90.0)
        cam.rotate(-45.0)
        assert cam.angle == 45.0

    def test_rotate_wraparound(self):
        """Вращение с переходом через 360°"""
        cam = Camera(10, 10, angle=350.0)
        cam.rotate(20.0)
        assert cam.angle == 10.0  # 350 + 20 = 370 % 360 = 10

    def test_get_direction_vector(self):
        """Получение вектора направления"""
        cam = Camera(10, 10, angle=0.0)  # East
        dx, dy = cam.get_direction_vector()

        assert abs(dx - 1.0) < 0.01
        assert abs(dy - 0.0) < 0.01


class TestCameraDistanceCalculation:
    """Тесты расчета расстояния"""

    def test_distance_to_same_position(self):
        """Расстояние до той же позиции"""
        cam = Camera(10.0, 10.0)
        distance = cam.distance_to(10.0, 10.0)
        assert distance == 0.0

    def test_distance_to_horizontal(self):
        """Расстояние по горизонтали"""
        cam = Camera(0.0, 0.0)
        distance = cam.distance_to(3.0, 0.0)
        assert distance == 3.0

    def test_distance_to_vertical(self):
        """Расстояние по вертикали"""
        cam = Camera(0.0, 0.0)
        distance = cam.distance_to(0.0, 4.0)
        assert distance == 4.0

    def test_distance_to_diagonal(self):
        """Расстояние по диагонали (3-4-5 треугольник)"""
        cam = Camera(0.0, 0.0)
        distance = cam.distance_to(3.0, 4.0)
        assert abs(distance - 5.0) < 0.01


class TestCameraFloatPrecision:
    """Тесты точности float координат"""

    def test_fractional_position_preserved(self):
        """Дробная часть координат сохраняется"""
        cam = Camera(10.25, 20.75)
        assert cam.x == 10.25
        assert cam.y == 20.75

    def test_fractional_position_after_set(self):
        """Дробная часть сохраняется после set_position"""
        cam = Camera(0, 0)
        cam.set_position(5.123, 7.456)
        assert abs(cam.x - 5.123) < 0.001
        assert abs(cam.y - 7.456) < 0.001

    def test_grid_position_always_int(self):
        """grid_position всегда int независимо от дробной части"""
        cam = Camera(10.999, 20.001)
        assert cam.grid_position == (10, 20)
        assert isinstance(cam.grid_position[0], int)
        assert isinstance(cam.grid_position[1], int)


class TestCameraBackwardCompatibility:
    """Тесты обратной совместимости"""

    def test_position_tuple_access(self):
        """Доступ к position как к tuple"""
        cam = Camera(15.5, 25.5)
        x, y = cam.position
        assert x == 15.5
        assert y == 25.5

    def test_position_indexing(self):
        """Индексация position"""
        cam = Camera(15.5, 25.5)
        assert cam.position[0] == 15.5
        assert cam.position[1] == 25.5

    def test_old_style_access_still_works(self):
        """Старый стиль доступа работает"""
        cam = Camera(10 + CameraConfig.CAMERA_OFFSET, 20 + CameraConfig.CAMERA_OFFSET)

        # Старый стиль через свойства x, y
        assert cam.x == 10 + CameraConfig.CAMERA_OFFSET
        assert cam.y == 20 + CameraConfig.CAMERA_OFFSET

        # Доступ через position
        x, y = cam.position
        assert x == 10 + CameraConfig.CAMERA_OFFSET and y == 20 + CameraConfig.CAMERA_OFFSET


class TestCameraRepr:
    """Тест строкового представления"""

    def test_repr_shows_float_and_grid(self):
        """__repr__ должен показывать float и grid позиции"""
        cam = Camera(10 + CameraConfig.CAMERA_OFFSET, 20.7, angle=45.0, fov=60.0)
        repr_str = repr(cam)

        expected_x = 10 + CameraConfig.CAMERA_OFFSET
        assert (f"pos=({expected_x:.2f}, 20.70)" in repr_str or
                f"pos=({expected_x}, 20.7)" in repr_str)
        assert "grid=(10, 20)" in repr_str
        assert "angle=45" in repr_str
        assert "fov=60" in repr_str


class TestCameraIntegrationScenarios:
    """Интеграционные сценарии"""

    def test_camera_follows_character(self):
        """Камера следует за персонажем"""
        # Character at int position
        char_pos = (10, 20)

        # Camera at character center (fractional position)
        cam = Camera(char_pos[0] + CameraConfig.CAMERA_OFFSET, char_pos[1] + CameraConfig.CAMERA_OFFSET)

        assert cam.grid_position == char_pos
        assert cam.x == 10 + CameraConfig.CAMERA_OFFSET
        assert cam.y == 20 + CameraConfig.CAMERA_OFFSET

    def test_camera_movement_sequence(self):
        """Последовательность движений камеры"""
        cam = Camera(5 + CameraConfig.CAMERA_OFFSET, 5 + CameraConfig.CAMERA_OFFSET, angle=0.0)

        # Move forward (East)
        new_x, new_y = cam.move_forward(1.0)
        cam.set_position(new_x, new_y)
        assert abs(cam.x - (6 + CameraConfig.CAMERA_OFFSET)) < 0.01

        # Rotate and move
        cam.rotate(90.0)  # Now facing North
        new_x, new_y = cam.move_forward(1.0)
        cam.set_position(new_x, new_y)
        assert abs(cam.y - (6 + CameraConfig.CAMERA_OFFSET)) < 0.01

    def test_raycasting_position_compatibility(self):
        """Позиция камеры совместима с raycasting"""
        cam = Camera(5 + CameraConfig.CAMERA_OFFSET, 5 + CameraConfig.CAMERA_OFFSET, angle=0.0)

        # В raycasting используется int(camera.x) для grid
        grid_x = int(cam.x)
        grid_y = int(cam.y)

        assert grid_x == 5
        assert grid_y == 5
        assert cam.grid_position == (5, 5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
