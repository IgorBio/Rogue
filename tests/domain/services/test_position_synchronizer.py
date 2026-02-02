"""
Тесты для PositionSynchronizer.

Проверяет корректность синхронизации позиций между Character и Camera.
"""

import pytest
from domain.entities.character import Character
from presentation.camera import Camera
from domain.services.position_synchronizer import (
    PositionSynchronizer,
    PositionSyncValidator,
    quick_sync_to_2d,
    quick_sync_to_3d
)
from presentation.camera import create_synced_pair


class TestPositionSynchronizerInit:
    """Тесты инициализации PositionSynchronizer"""

    def test_default_init(self):
        """Инициализация с параметрами по умолчанию"""
        sync = PositionSynchronizer()
        assert sync.center_offset == 0.5
        assert sync._last_character_pos is None
        assert sync._last_camera_pos is None

    def test_custom_offset(self):
        """Инициализация с пользовательским offset"""
        sync = PositionSynchronizer(center_offset=0.25)
        assert sync.center_offset == 0.25


class TestSyncCameraToCharacter:
    """Тесты синхронизации Character → Camera"""

    def test_basic_sync(self):
        """Базовая синхронизация Character → Camera"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        sync.sync_camera_to_character(cam, char)

        # Camera должна быть в центре клетки character
        assert cam.x == 10.5
        assert cam.y == 20.5
        assert cam.grid_position == (10, 20)

    def test_sync_preserves_angle(self):
        """Синхронизация сохраняет угол камеры"""
        char = Character(10, 20)
        cam = Camera(0, 0, angle=45.0)
        sync = PositionSynchronizer()

        sync.sync_camera_to_character(cam, char, preserve_angle=True)

        assert cam.angle == 45.0
        assert cam.x == 10.5
        assert cam.y == 20.5

    def test_sync_updates_angle(self):
        """Синхронизация может обновить угол"""
        char = Character(10, 20)
        cam = Camera(0, 0, angle=45.0)
        sync = PositionSynchronizer()

        sync.sync_camera_to_character(cam, char, preserve_angle=False)

        # Угол может измениться (зависит от реализации)
        assert cam.x == 10.5
        assert cam.y == 20.5

    def test_sync_with_custom_offset(self):
        """Синхронизация с пользовательским offset"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer(center_offset=0.25)

        sync.sync_camera_to_character(cam, char)

        assert cam.x == 10.25
        assert cam.y == 20.25

    def test_sync_updates_tracking(self):
        """Синхронизация обновляет отслеживание"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        sync.sync_camera_to_character(cam, char)

        assert sync._last_character_pos == (10, 20)
        assert sync._last_camera_pos == (10.5, 20.5)


class TestSyncCharacterToCamera:
    """Тесты синхронизации Camera → Character"""

    def test_sync_with_snap_to_grid(self):
        """Синхронизация с snap_to_grid=True (floor)"""
        char = Character(0, 0)
        cam = Camera(10.7, 20.3)
        sync = PositionSynchronizer()

        sync.sync_character_to_camera(char, cam, snap_to_grid=True)

        # Используется grid_position (floor)
        assert char.position == (10, 20)

    def test_sync_without_snap_to_grid(self):
        """Синхронизация с snap_to_grid=False (round)"""
        char = Character(0, 0)
        cam = Camera(10.7, 20.3)
        sync = PositionSynchronizer()

        sync.sync_character_to_camera(char, cam, snap_to_grid=False)

        # Используется round
        assert char.position == (11, 20)

    def test_sync_updates_tracking(self):
        """Синхронизация обновляет отслеживание"""
        char = Character(0, 0)
        cam = Camera(10.5, 20.5)
        sync = PositionSynchronizer()

        sync.sync_character_to_camera(char, cam)

        assert sync._last_character_pos == (10, 20)
        assert sync._last_camera_pos == (10.5, 20.5)


class TestMovementTracking:
    """Тесты отслеживания движения"""

    def test_is_character_moved_initially(self):
        """Character считается движущимся до первой синхронизации"""
        char = Character(10, 20)
        sync = PositionSynchronizer()

        assert sync.is_character_moved(char) == True

    def test_is_character_moved_after_sync(self):
        """Character не движется после синхронизации"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        sync.sync_camera_to_character(cam, char)
        assert sync.is_character_moved(char) == False

    def test_is_character_moved_after_movement(self):
        """Character движется после перемещения"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        sync.sync_camera_to_character(cam, char)
        char.move_to(15, 25)

        assert sync.is_character_moved(char) == True

    def test_is_camera_moved_initially(self):
        """Camera считается движущейся до первой синхронизации"""
        cam = Camera(10.5, 20.5)
        sync = PositionSynchronizer()

        assert sync.is_camera_moved(cam) == True

    def test_is_camera_moved_after_sync(self):
        """Camera не движется после синхронизации"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        sync.sync_character_to_camera(char, cam)
        assert sync.is_camera_moved(cam) == False

    def test_is_camera_moved_after_movement(self):
        """Camera движется после перемещения"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        sync.sync_character_to_camera(char, cam)
        cam.set_position(15.5, 25.5)

        assert sync.is_camera_moved(cam) == True


class TestAutoSync:
    """Тесты автоматической синхронизации"""

    def test_auto_sync_character_to_camera(self):
        """Автоматическая синхронизация Character → Camera"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        result = sync.auto_sync_if_needed(char, cam, mode='character_to_camera')

        assert result == True
        assert cam.grid_position == (10, 20)

    def test_auto_sync_camera_to_character(self):
        """Автоматическая синхронизация Camera → Character"""
        char = Character(0, 0)
        cam = Camera(10.5, 20.5)
        sync = PositionSynchronizer()

        result = sync.auto_sync_if_needed(char, cam, mode='camera_to_character')

        assert result == True
        assert char.position == (10, 20)

    def test_auto_sync_no_movement(self):
        """Автосинхронизация не выполняется если нет движения"""
        char = Character(10, 20)
        cam = Camera(10.5, 20.5)
        sync = PositionSynchronizer()

        # Первая синхронизация
        sync.auto_sync_if_needed(char, cam, mode='character_to_camera')

        # Вторая попытка - движения нет
        result = sync.auto_sync_if_needed(char, cam, mode='character_to_camera')

        assert result == False


class TestUtilityMethods:
    """Тесты вспомогательных методов"""

    def test_get_sync_offset(self):
        """Расчет offset между character и camera"""
        char = Character(10, 20)
        cam = Camera(10.5, 20.7)
        sync = PositionSynchronizer()

        offset_x, offset_y = sync.get_sync_offset(char, cam)

        assert offset_x == 0.5
        assert abs(offset_y - 0.7) < 0.01

    def test_are_positions_synced_true(self):
        """Проверка синхронизации - позиции синхронизированы"""
        char = Character(10, 20)
        cam = Camera(10.5, 20.5)
        sync = PositionSynchronizer()

        assert sync.are_positions_synced(char, cam) == True

    def test_are_positions_synced_false(self):
        """Проверка синхронизации - позиции не синхронизированы"""
        char = Character(10, 20)
        cam = Camera(15.5, 25.5)
        sync = PositionSynchronizer()

        assert sync.are_positions_synced(char, cam) == False

    def test_reset_tracking(self):
        """Сброс отслеживания"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        sync.sync_camera_to_character(cam, char)
        sync.reset_tracking()

        assert sync._last_character_pos is None
        assert sync._last_camera_pos is None


class TestPositionSyncValidator:
    """Тесты валидатора синхронизации"""

    def test_validate_sync_synced(self):
        """Валидация синхронизированных позиций"""
        char = Character(10, 20)
        cam = Camera(10.5, 20.5)

        result = PositionSyncValidator.validate_sync(char, cam)

        assert result['is_synced'] == True
        assert result['character_pos'] == (10, 20)
        assert result['camera_grid_pos'] == (10, 20)
        assert len(result['issues']) == 0

    def test_validate_sync_not_synced(self):
        """Валидация несинхронизированных позиций"""
        char = Character(10, 20)
        cam = Camera(15.5, 25.5)

        result = PositionSyncValidator.validate_sync(char, cam)

        assert result['is_synced'] == False
        assert result['character_pos'] == (10, 20)
        assert result['camera_grid_pos'] == (15, 25)
        assert len(result['issues']) > 0

    def test_validate_sync_large_offset(self):
        """Валидация с большим offset"""
        char = Character(10, 20)
        cam = Camera(15.5, 25.5)

        result = PositionSyncValidator.validate_sync(char, cam)

        # Должно быть предупреждение о большом offset
        issues_str = ' '.join(result['issues'])
        assert 'offset' in issues_str.lower()

    def test_suggest_sync_direction_none(self):
        """Предложение направления - уже синхронизировано"""
        char = Character(10, 20)
        cam = Camera(10.5, 20.5)

        direction = PositionSyncValidator.suggest_sync_direction(char, cam)

        assert direction == 'none'

    def test_suggest_sync_direction_camera_centered(self):
        """Предложение направления - camera в центре"""
        char = Character(10, 20)
        cam = Camera(15.5, 25.5)  # В центре клетки

        direction = PositionSyncValidator.suggest_sync_direction(char, cam)

        assert direction == 'camera_to_character'

    def test_suggest_sync_direction_default(self):
        """Предложение направления - по умолчанию"""
        char = Character(10, 20)
        cam = Camera(15.2, 25.8)  # Не в центре

        direction = PositionSyncValidator.suggest_sync_direction(char, cam)

        assert direction == 'character_to_camera'


class TestConvenienceFunctions:
    """Тесты вспомогательных функций"""

    def test_create_synced_pair(self):
        """Создание синхронизированной пары"""
        char, cam = create_synced_pair((10, 20), angle=45.0, fov=60.0)

        assert char.position == (10, 20)
        assert cam.grid_position == (10, 20)
        assert cam.x == 10.5
        assert cam.y == 20.5
        assert cam.angle == 45.0
        assert cam.fov == 60.0

    def test_create_synced_pair_custom_offset(self):
        """Создание пары с пользовательским offset"""
        char, cam = create_synced_pair((10, 20), center_offset=0.25)

        assert char.position == (10, 20)
        assert cam.x == 10.25
        assert cam.y == 20.25

    def test_quick_sync_to_2d(self):
        """Быстрая синхронизация в 2D"""
        char = Character(0, 0)
        cam = Camera(10.5, 20.5)

        quick_sync_to_2d(char, cam)

        assert char.position == (10, 20)

    def test_quick_sync_to_3d(self):
        """Быстрая синхронизация в 3D"""
        char = Character(10, 20)
        cam = Camera(0, 0, angle=45.0)

        quick_sync_to_3d(cam, char)

        assert cam.grid_position == (10, 20)
        assert cam.angle == 45.0  # Угол сохранен


class TestIntegrationScenarios:
    """Интеграционные сценарии"""

    def test_view_switching_2d_to_3d(self):
        """Переключение 2D → 3D"""
        char = Character(10, 20)
        cam = Camera(0, 0)
        sync = PositionSynchronizer()

        # Пользователь переключается на 3D вид
        sync.sync_camera_to_character(cam, char)

        assert cam.grid_position == char.position
        assert sync.are_positions_synced(char, cam)

    def test_view_switching_3d_to_2d(self):
        """Переключение 3D → 2D"""
        char = Character(0, 0)
        cam = Camera(10.5, 20.7)
        sync = PositionSynchronizer()

        # Пользователь переключается на 2D вид
        sync.sync_character_to_camera(char, cam)

        assert char.position == cam.grid_position
        assert sync.are_positions_synced(char, cam)

    def test_continuous_movement_sync(self):
        """Непрерывная синхронизация при движении"""
        char = Character(10, 20)
        cam = Camera(10.5, 20.5)
        sync = PositionSynchronizer()

        # Начальная синхронизация
        sync.sync_camera_to_character(cam, char)
        assert sync.are_positions_synced(char, cam)

        # Движение персонажа
        char.move_to(11, 21)

        # Автосинхронизация
        sync.auto_sync_if_needed(char, cam, mode='character_to_camera')
        assert sync.are_positions_synced(char, cam)

    def test_bidirectional_sync(self):
        """Двунаправленная синхронизация"""
        char = Character(10, 20)
        cam = Camera(10.5, 20.5)
        sync = PositionSynchronizer()

        # Character → Camera
        sync.sync_camera_to_character(cam, char)
        assert cam.grid_position == (10, 20)

        # Camera движется
        cam.set_position(15.5, 25.5)

        # Camera → Character
        sync.sync_character_to_camera(char, cam)
        assert char.position == (15, 25)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
