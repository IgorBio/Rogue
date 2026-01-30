"""
Item entities for the game.

This module defines all item types that can be found and used by the player,
including consumables, equipment, and collectibles.
"""
from config.game_config import ItemType


class Item:
    """
    Base class for all items.
    
    Attributes:
        item_type (str): Type identifier from ItemType
        subtype (str): Optional subtype (e.g., stat affected)
        position (tuple): (x, y) coordinates when placed in world
    """
    
    def __init__(self, item_type, subtype=None):
        """
        Initialize an item.
        
        Args:
            item_type (str): Item type from ItemType constants
            subtype (str): Optional subtype identifier
        """
        self.item_type = item_type
        self.subtype = subtype
        self.position = None
    
    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.item_type}, subtype={self.subtype})"


class Treasure(Item):
    """
    Treasure item that accumulates points for scoring.
    
    Obtained by defeating enemies. Does not take inventory space.
    """
    
    def __init__(self, value):
        """
        Initialize treasure.
        
        Args:
            value (int): Point value of this treasure
        """
        super().__init__(ItemType.TREASURE)
        self.value = value
    
    def __repr__(self):
        return f"Treasure(value={self.value})"


class Food(Item):
    """
    Food item that restores health when consumed.
    
    Single-use consumable.
    """
    
    def __init__(self, health_restoration):
        """
        Initialize food.
        
        Args:
            health_restoration (int): Amount of health restored
        """
        super().__init__(ItemType.FOOD)
        self.health_restoration = health_restoration
    
    def __repr__(self):
        return f"Food(health_restoration={self.health_restoration})"


class Elixir(Item):
    """
    Elixir that temporarily increases a stat.
    
    Effect lasts for a specified number of turns, then reverts.
    Single-use consumable.
    """
    
    def __init__(self, stat_type, bonus, duration):
        """
        Initialize elixir.
        
        Args:
            stat_type (str): StatType constant (STRENGTH, DEXTERITY, MAX_HEALTH)
            bonus (int): Amount of stat increase
            duration (int): Number of turns effect lasts
        """
        super().__init__(ItemType.ELIXIR, subtype=stat_type)
        self.stat_type = stat_type
        self.bonus = bonus
        self.duration = duration
    
    def __repr__(self):
        return f"Elixir(stat={self.stat_type}, bonus={self.bonus}, duration={self.duration})"


class Scroll(Item):
    """
    Scroll that permanently increases a stat.
    
    Effect is permanent and stacks with other bonuses.
    Single-use consumable.
    """
    
    def __init__(self, stat_type, bonus):
        """
        Initialize scroll.
        
        Args:
            stat_type (str): StatType constant (STRENGTH, DEXTERITY, MAX_HEALTH)
            bonus (int): Amount of permanent stat increase
        """
        super().__init__(ItemType.SCROLL, subtype=stat_type)
        self.stat_type = stat_type
        self.bonus = bonus
    
    def __repr__(self):
        return f"Scroll(stat={self.stat_type}, bonus={self.bonus})"


class Weapon(Item):
    """
    Weapon that modifies damage calculation.
    
    Can be equipped to increase attack strength.
    Only one weapon can be equipped at a time.
    """
    
    def __init__(self, name, strength_bonus):
        """
        Initialize weapon.
        
        Args:
            name (str): Display name of the weapon
            strength_bonus (int): Bonus added to strength for damage calculation
        """
        super().__init__(ItemType.WEAPON)
        self.name = name
        self.strength_bonus = strength_bonus
    
    def __repr__(self):
        return f"Weapon(name={self.name}, strength_bonus={self.strength_bonus})"