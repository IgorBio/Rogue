"""
Player character and inventory system.

REFACTORING NOTE (Step 1.2):
- Integrated Position class for coordinate management
- Character now uses Position internally instead of tuple
- position property returns tuple for backward compatibility
- All coordinate operations now use Position methods
"""

from domain.entities.position import Position
from utils.constants import (
    INITIAL_PLAYER_HEALTH,
    INITIAL_PLAYER_MAX_HEALTH,
    INITIAL_PLAYER_STRENGTH,
    INITIAL_PLAYER_DEXTERITY,
    MAX_ITEMS_PER_TYPE,
    MIN_HEALTH_AFTER_ELIXIR_EXPIRY,
    ItemType,
    StatType
)


class Backpack:
    """Inventory container for storing items by type."""

    def __init__(self):
        """Initialize empty backpack with storage for all item types."""
        self.items = {
            ItemType.TREASURE: [],
            ItemType.FOOD: [],
            ItemType.ELIXIR: [],
            ItemType.SCROLL: [],
            ItemType.WEAPON: [],
            ItemType.KEY: []
        }
        self.treasure_value = 0

    def add_item(self, item):
        """
        Add an item to the backpack if there's room.

        Args:
            item: Item instance to add

        Returns:
            bool: True if item was added, False if backpack is full
        """
        item_type = item.item_type

        if item_type == ItemType.TREASURE:
            self.treasure_value += item.value
            return True

        if len(self.items[item_type]) < MAX_ITEMS_PER_TYPE:
            self.items[item_type].append(item)
            return True

        return False

    def remove_item(self, item_type, index):
        """
        Remove and return an item by type and index.

        Args:
            item_type: Type of item to remove
            index: Index within that item type's list

        Returns:
            Item instance or None if index invalid
        """
        if item_type in self.items and 0 <= index < len(self.items[item_type]):
            return self.items[item_type].pop(index)
        return None

    def get_items(self, item_type):
        """
        Get all items of a specific type.

        Args:
            item_type: Type of items to retrieve

        Returns:
            list: List of items of that type
        """
        return self.items.get(item_type, [])

    def get_item_count(self, item_type):
        """
        Get count of items of a specific type.

        Args:
            item_type: Type of items to count

        Returns:
            int: Number of items (or treasure value for TREASURE type)
        """
        if item_type == ItemType.TREASURE:
            return self.treasure_value
        return len(self.items.get(item_type, []))

    def __repr__(self):
        counts = {k: len(v) for k, v in self.items.items() if k != ItemType.TREASURE}
        counts[ItemType.TREASURE] = self.treasure_value
        return f"Backpack({counts})"


class Character:
    """
    Player character with stats, inventory, and combat capabilities.

    Attributes:
        _position (Position): Internal Position object (always int coordinates)
        health (int): Current health points
        max_health (int): Maximum health capacity
        strength (int): Base damage stat
        dexterity (int): Affects hit chance
        current_weapon: Equipped weapon or None
        backpack (Backpack): Inventory storage
        active_elixirs (list): Temporary stat bonuses with remaining duration

    Note:
        Position is stored internally as Position object but exposed as tuple
        via the position property for backward compatibility.
    """

    def __init__(self, x=0, y=0):
        """
        Initialize a new character.

        Args:
            x (int or float): Starting X coordinate (will be converted to int)
            y (int or float): Starting Y coordinate (will be converted to int)
        """
        # ✅ CHANGED: Use Position object instead of tuple
        self._position = Position(x, y)

        self.health = INITIAL_PLAYER_HEALTH
        self.max_health = INITIAL_PLAYER_MAX_HEALTH
        self.strength = INITIAL_PLAYER_STRENGTH
        self.dexterity = INITIAL_PLAYER_DEXTERITY
        self.current_weapon = None
        self.backpack = Backpack()
        self.active_elixirs = []

    @property
    def position(self):
        """
        Get character position as tuple (for backward compatibility).

        Returns:
            tuple: (x, y) coordinates
        """
        return self._position.tuple

    @property
    def position_obj(self):
        """
        Get character position as Position object.

        Returns:
            Position: Position object
        """
        return self._position

    def take_damage(self, damage):
        """
        Apply damage to the character.

        Args:
            damage (int): Amount of damage to apply
        """
        self.health -= damage
        if self.health < 0:
            self.health = 0

    def heal(self, amount):
        """
        Restore health, capped at max_health.

        Args:
            amount (int): Amount of health to restore
        """
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def is_alive(self):
        """Check if character is still alive."""
        return self.health > 0

    def move_to(self, x, y):
        """
        Update character position.

        Args:
            x (int or float): New X coordinate
            y (int or float): New Y coordinate
        """
        # ✅ CHANGED: Use Position.update() method
        self._position.update(x, y)

    def move_by(self, dx, dy):
        """
        Move character by delta.

        Args:
            dx (int or float): Change in X coordinate
            dy (int or float): Change in Y coordinate
        """
        # ✅ NEW: Added move_by method using Position
        self._position.move_by(dx, dy)

    def get_x(self):
        """
        Get character's X coordinate.

        Returns:
            int: X coordinate
        """
        # ✅ CHANGED: Use Position.x property
        return self._position.x

    def get_y(self):
        """
        Get character's Y coordinate.

        Returns:
            int: Y coordinate
        """
        # ✅ CHANGED: Use Position.y property
        return self._position.y

    def distance_to(self, other_position):
        """
        Calculate distance to another position.

        Args:
            other_position: Position object or (x, y) tuple

        Returns:
            float: Euclidean distance
        """
        # ✅ NEW: Added distance calculation
        return self._position.distance_to(other_position)

    def manhattan_distance_to(self, other_position):
        """
        Calculate Manhattan distance to another position.

        Args:
            other_position: Position object or (x, y) tuple

        Returns:
            int: Manhattan distance
        """
        # ✅ NEW: Added Manhattan distance calculation
        return self._position.manhattan_distance_to(other_position)

    def is_adjacent_to(self, other_position):
        """
        Check if character is adjacent to a position.

        Args:
            other_position: Position object or (x, y) tuple

        Returns:
            bool: True if adjacent (including diagonals)
        """
        # ✅ NEW: Added adjacency check
        return self._position.is_adjacent_to(other_position)

    def get_total_strength(self):
        """
        Calculate total strength including weapon bonus.

        Returns:
            int: Total strength value
        """
        base_strength = self.strength
        weapon_bonus = self.current_weapon.strength_bonus if self.current_weapon else 0
        return base_strength + weapon_bonus

    def use_food(self, food):
        """
        Consume food to restore health.

        Args:
            food: Food item instance

        Returns:
            str: Message describing the effect
        """
        old_health = self.health
        self.heal(food.health_restoration)
        actual_healing = self.health - old_health
        return f"Ate food and restored {actual_healing} HP!"

    def equip_weapon(self, weapon):
        """
        Equip a weapon, returning the previously equipped weapon.

        Args:
            weapon: Weapon to equip

        Returns:
            tuple: (old_weapon, message)
        """
        old_weapon = self.current_weapon
        self.current_weapon = weapon

        if old_weapon:
            message = f"Equipped {weapon.name}, unequipped {old_weapon.name}"
            return (old_weapon, message)
        else:
            message = f"Equipped {weapon.name}"
            return (old_weapon, message)

    def unequip_weapon(self):
        """
        Unequip current weapon.

        Returns:
            tuple: (weapon, message, should_drop)
        """
        weapon = self.current_weapon
        self.current_weapon = None

        if weapon:
            message = f"Unequipped {weapon.name}"
            return (weapon, message, True)
        else:
            message = "No weapon equipped"
            return (weapon, message, False)

    def use_elixir(self, elixir):
        """
        Drink an elixir for temporary stat boost.

        Args:
            elixir: Elixir item instance

        Returns:
            str: Message describing the effect
        """
        self.active_elixirs.append({
            'stat_type': elixir.stat_type,
            'bonus': elixir.bonus,
            'remaining_turns': elixir.duration
        })

        if elixir.stat_type == StatType.STRENGTH:
            self.strength += elixir.bonus
            return f"Drank elixir! Strength +{elixir.bonus} for {elixir.duration} turns"
        elif elixir.stat_type == StatType.DEXTERITY:
            self.dexterity += elixir.bonus
            return f"Drank elixir! Dexterity +{elixir.bonus} for {elixir.duration} turns"
        elif elixir.stat_type == StatType.MAX_HEALTH:
            self.max_health += elixir.bonus
            self.health += elixir.bonus
            return f"Drank elixir! Max Health +{elixir.bonus} for {elixir.duration} turns"

        return "Drank elixir!"

    def use_scroll(self, scroll):
        """
        Read a scroll for permanent stat increase.

        Args:
            scroll: Scroll item instance

        Returns:
            str: Message describing the effect
        """
        if scroll.stat_type == StatType.STRENGTH:
            self.strength += scroll.bonus
            return f"Read scroll! Strength +{scroll.bonus} (permanent)"
        elif scroll.stat_type == StatType.DEXTERITY:
            self.dexterity += scroll.bonus
            return f"Read scroll! Dexterity +{scroll.bonus} (permanent)"
        elif scroll.stat_type == StatType.MAX_HEALTH:
            self.max_health += scroll.bonus
            self.health += scroll.bonus
            return f"Read scroll! Max Health +{scroll.bonus} (permanent)"

        return "Read scroll!"

    def update_elixirs(self):
        """
        Update elixir durations and remove expired ones.

        Returns:
            list: Messages about expired elixirs
        """
        messages = []
        expired = []

        for i, elixir_effect in enumerate(self.active_elixirs):
            elixir_effect['remaining_turns'] -= 1

            if elixir_effect['remaining_turns'] <= 0:
                expired.append(i)
                stat_type = elixir_effect['stat_type']
                bonus = elixir_effect['bonus']

                if stat_type == StatType.STRENGTH:
                    self.strength -= bonus
                    messages.append(f"Elixir wore off: Strength -{bonus}")
                elif stat_type == StatType.DEXTERITY:
                    self.dexterity -= bonus
                    messages.append(f"Elixir wore off: Dexterity -{bonus}")
                elif stat_type == StatType.MAX_HEALTH:
                    self.max_health -= bonus
                    if self.health > self.max_health:
                        self.health = self.max_health
                    if self.health <= 0:
                        self.health = MIN_HEALTH_AFTER_ELIXIR_EXPIRY
                    messages.append(f"Elixir wore off: Max Health -{bonus}")

        for i in reversed(expired):
            self.active_elixirs.pop(i)

        return messages

    def __repr__(self):
        # ✅ CHANGED: Use _position.tuple for display
        return (f"Character(pos={self._position.tuple}, hp={self.health}/{self.max_health}, "
                f"str={self.strength}, dex={self.dexterity}, weapon={self.current_weapon})")
