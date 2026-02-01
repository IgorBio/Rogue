"""
Item entities for the game.

This module defines all item types that can be found and used by the player,
including consumables, equipment, and collectibles.
"""
from typing import Optional, Union, Tuple
from domain.entities.position import Position


class Item:
    """
    Base class for all items.
    
    Attributes:
        item_type (str): Type identifier from ItemType
        subtype (str): Optional subtype (e.g., stat affected)
        _position (Optional[Position]): Position when placed in world
    """
    
    def __init__(self, item_type: str, subtype: Optional[str] = None):
        """
        Initialize an item.
        
        Args:
            item_type: Item type from ItemType constants
            subtype: Optional subtype identifier
        """
        self.item_type = item_type
        self.subtype = subtype
        self._position: Optional[Position] = None
    
    @property
    def position(self) -> Optional[Position]:
        """Get item position as Position object or None."""
        return self._position
    
    @position.setter
    def position(self, value: Optional[Union[Position, Tuple[int, int]]]):
        """Set position from tuple, Position, or None."""
        if value is None:
            self._position = None
        elif isinstance(value, Position):
            self._position = value
        else:
            self._position = Position(value[0], value[1])
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.item_type}, subtype={self.subtype})"


class Treasure(Item):
    """
    Treasure item that accumulates points for scoring.
    
    Obtained by defeating enemies. Does not take inventory space.
    """
    
    def __init__(self, value: int):
        """
        Initialize treasure.
        
        Args:
            value: Point value of this treasure
        """
        from config.game_config import ItemType
        super().__init__(ItemType.TREASURE)
        self.value = value
    
    def __repr__(self) -> str:
        return f"Treasure(value={self.value})"


class Food(Item):
    """
    Food item that restores health when consumed.
    
    Single-use consumable.
    """
    
    def __init__(self, health_restoration: int):
        """
        Initialize food.
        
        Args:
            health_restoration: Amount of health restored
        """
        from config.game_config import ItemType
        super().__init__(ItemType.FOOD)
        self.health_restoration = health_restoration
    
    def __repr__(self) -> str:
        return f"Food(health_restoration={self.health_restoration})"


class Elixir(Item):
    """
    Elixir that temporarily increases a stat.
    
    Effect lasts for a specified number of turns, then reverts.
    Single-use consumable.
    """
    
    def __init__(self, stat_type: str, bonus: int, duration: int):
        """
        Initialize elixir.
        
        Args:
            stat_type: StatType constant (STRENGTH, DEXTERITY, MAX_HEALTH)
            bonus: Amount of stat increase
            duration: Number of turns effect lasts
        """
        from config.game_config import ItemType
        super().__init__(ItemType.ELIXIR, subtype=stat_type)
        self.stat_type = stat_type
        self.bonus = bonus
        self.duration = duration
    
    def __repr__(self) -> str:
        return f"Elixir(stat={self.stat_type}, bonus={self.bonus}, duration={self.duration})"


class Scroll(Item):
    """
    Scroll that permanently increases a stat.
    
    Effect is permanent and stacks with other bonuses.
    Single-use consumable.
    """
    
    def __init__(self, stat_type: str, bonus: int):
        """
        Initialize scroll.
        
        Args:
            stat_type: StatType constant (STRENGTH, DEXTERITY, MAX_HEALTH)
            bonus: Amount of permanent stat increase
        """
        from config.game_config import ItemType
        super().__init__(ItemType.SCROLL, subtype=stat_type)
        self.stat_type = stat_type
        self.bonus = bonus
    
    def __repr__(self) -> str:
        return f"Scroll(stat={self.stat_type}, bonus={self.bonus})"


class Weapon(Item):
    """
    Weapon that modifies damage calculation.
    
    Can be equipped to increase attack strength.
    Only one weapon can be equipped at a time.
    """
    
    def __init__(self, name: str, strength_bonus: int):
        """
        Initialize weapon.
        
        Args:
            name: Display name of the weapon
            strength_bonus: Bonus added to strength for damage calculation
        """
        from config.game_config import ItemType
        super().__init__(ItemType.WEAPON)
        self.name = name
        self.strength_bonus = strength_bonus
    
    def __repr__(self) -> str:
        return f"Weapon(name={self.name}, strength_bonus={self.strength_bonus})"
