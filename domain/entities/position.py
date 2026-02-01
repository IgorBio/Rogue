"""
Система координат для игры.

Этот модуль решает проблему смешивания типов координат (float vs int)
между Character и Camera. Position гарантирует, что все координаты
всегда будут целыми числами (int).

Проблема до рефакторинга:
- Character.position был tuple[int, int]
- Camera.x и Camera.y были float
- При переключении между 2D и 3D возникали рассинхронизации
- Сравнение позиций могло давать false negative: (1.9, 2.1) != (1, 2)

Решение:
- Position всегда хранит int координаты
- Автоматическое приведение float к int при установке
- Единый интерфейс для работы с позициями
"""

from typing import Tuple, Union


class Position:
    """
    Класс для управления позицией в игре.

    Гарантирует, что координаты всегда являются целыми числами,
    даже если передаются float значения (например, из Camera).

    Attributes:
        _x (int): X координата
        _y (int): Y координата

    Examples:
        >>> pos = Position(10.7, 20.3)
        >>> pos.x
        10
        >>> pos.y
        20
        >>> pos.tuple
        (10, 20)
        >>> pos == (10, 20)
        True
    """

    def __init__(self, x: Union[int, float], y: Union[int, float]):
        """
        Инициализировать позицию.

        Args:
            x: X координата (будет приведена к int)
            y: Y координата (будет приведена к int)
        """
        self._x = int(x)
        self._y = int(y)

    @property
    def x(self) -> int:
        """Получить X координату"""
        return self._x

    @property
    def y(self) -> int:
        """Получить Y координату"""
        return self._y

    @property
    def tuple(self) -> Tuple[int, int]:
        """Получить позицию как кортеж (x, y)"""
        return (self._x, self._y)

    def update(self, x: Union[int, float], y: Union[int, float]) -> None:
        """
        Обновить позицию (с автоматическим приведением к int).

        Args:
            x: Новая X координата
            y: Новая Y координата
        """
        self._x = int(x)
        self._y = int(y)

    def move_by(self, dx: Union[int, float], dy: Union[int, float]) -> None:
        """
        Переместить позицию на delta.

        Args:
            dx: Изменение X координаты
            dy: Изменение Y координаты
        """
        self._x += int(dx)
        self._y += int(dy)

    def distance_to(self, other: Union['Position', Tuple[int, int]]) -> float:
        """
        Вычислить Евклидово расстояние до другой позиции.

        Args:
            other: Другая позиция или кортеж координат

        Returns:
            float: Расстояние
        """
        if isinstance(other, Position):
            dx = self._x - other._x
            dy = self._y - other._y
        else:
            dx = self._x - other[0]
            dy = self._y - other[1]

        return (dx * dx + dy * dy) ** 0.5

    def manhattan_distance_to(self, other: Union['Position', Tuple[int, int]]) -> int:
        """
        Вычислить Манхэттенское расстояние до другой позиции.

        Args:
            other: Другая позиция или кортеж координат

        Returns:
            int: Манхэттенское расстояние
        """
        if isinstance(other, Position):
            return abs(self._x - other._x) + abs(self._y - other._y)
        else:
            return abs(self._x - other[0]) + abs(self._y - other[1])

    def copy(self) -> 'Position':
        """
        Создать копию позиции.

        Returns:
            Position: Новый объект с теми же координатами
        """
        return Position(self._x, self._y)

    def to_camera_coords(self, offset: float = 0.5) -> Tuple[float, float]:
        """
        Преобразовать grid позицию в camera координаты.

        Camera использует float координаты с offset для центрирования
        в ячейке сетки (например, 10.5 вместо 10).

        Args:
            offset: Смещение для центрирования (default 0.5)

        Returns:
            Tuple[float, float]: Camera координаты (x, y)

        Example:
            >>> pos = Position(10, 20)
            >>> pos.to_camera_coords()
            (10.5, 20.5)
            >>> pos.to_camera_coords(offset=0.0)
            (10.0, 20.0)
        """
        return (float(self._x) + offset, float(self._y) + offset)

    @classmethod
    def from_camera_coords(cls, x: float, y: float,
                          snap_mode: str = 'floor') -> 'Position':
        """
        Создать Position из camera координат.

        Args:
            x: Camera X координата (float)
            y: Camera Y координата (float)
            snap_mode: Способ приведения к int:
                      'floor' — округление вниз (int())
                      'round' — округление к ближайшему

        Returns:
            Position: Новая позиция с int координатами

        Example:
            >>> Position.from_camera_coords(10.7, 20.3)
            Position(10, 20)  # floor mode
            >>> Position.from_camera_coords(10.7, 20.3, snap_mode='round')
            Position(11, 20)  # round mode
        """
        if snap_mode == 'floor':
            return cls(int(x), int(y))
        elif snap_mode == 'round':
            return cls(round(x), round(y))
        else:
            raise ValueError(f"Unknown snap_mode: {snap_mode}")

    def is_adjacent_to(self, other: Union['Position', Tuple[int, int]]) -> bool:
        """
        Проверить, является ли позиция соседней (включая диагонали).

        Соседними считаются позиции, которые отличаются максимум на 1 по каждой оси.
        Например, для (10, 10) соседними будут:
        - (9, 9), (10, 9), (11, 9)
        - (9, 10),         (11, 10)
        - (9, 11), (10, 11), (11, 11)

        Args:
            other: Другая позиция или кортеж координат

        Returns:
            bool: True если позиции соседние
        """
        if isinstance(other, Position):
            other_x, other_y = other._x, other._y
        else:
            other_x, other_y = other[0], other[1]

        # Проверяем, что разница по каждой оси <= 1
        dx = abs(self._x - other_x)
        dy = abs(self._y - other_y)

        # Соседняя если оба <= 1 но не оба == 0 (не сама себе)
        return dx <= 1 and dy <= 1 and (dx != 0 or dy != 0)

    def __eq__(self, other) -> bool:
        """
        Сравнить позицию с другой позицией или кортежем.

        Args:
            other: Position, tuple или любой объект

        Returns:
            bool: True если позиции равны
        """
        if isinstance(other, Position):
            return self._x == other._x and self._y == other._y
        if isinstance(other, tuple) and len(other) == 2:
            return self._x == other[0] and self._y == other[1]
        return False

    def __ne__(self, other) -> bool:
        """Проверка неравенства"""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Хэш для использования в множествах и словарях"""
        return hash((self._x, self._y))

    def __repr__(self) -> str:
        """Строковое представление для отладки"""
        return f"Position({self._x}, {self._y})"

    def __str__(self) -> str:
        """Строковое представление для пользователя"""
        return f"({self._x}, {self._y})"

    def __iter__(self):
        """Позволяет распаковку: x, y = position"""
        return iter((self._x, self._y))

    def __getitem__(self, index: int) -> int:
        """Позволяет индексацию: position[0], position[1]"""
        if index == 0:
            return self._x
        elif index == 1:
            return self._y
        else:
            raise IndexError("Position index out of range (0-1)")


def create_position(x: Union[int, float], y: Union[int, float]) -> Position:
    """
    Фабричная функция для создания Position.

    Args:
        x: X координата
        y: Y координата

    Returns:
        Position: Новый объект Position
    """
    return Position(x, y)


def positions_equal(pos1: Union[Position, Tuple[int, int]], 
                   pos2: Union[Position, Tuple[int, int]]) -> bool:
    """
    Проверить равенство двух позиций.

    Утилита для сравнения позиций различных типов.

    Args:
        pos1: Первая позиция
        pos2: Вторая позиция

    Returns:
        bool: True если позиции равны
    """
    if isinstance(pos1, Position):
        return pos1 == pos2
    if isinstance(pos2, Position):
        return pos2 == pos1
    return pos1 == pos2
