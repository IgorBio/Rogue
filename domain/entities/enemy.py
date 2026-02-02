"""
Enemy entities with unique behaviors and attributes.

This module defines the Enemy base class and all enemy types,
including their special mechanics and AI behaviors.
"""
from typing import TYPE_CHECKING, Optional
from domain.entities.position import Position

if TYPE_CHECKING:
    from config.game_config import EnemyType


class Enemy:
    """
    Base class for all enemy types.
    
    Attributes:
        enemy_type (str): Type identifier from EnemyType
        _position (Position): Position object for coordinate management
        health (int): Current health points
        max_health (int): Maximum health capacity
        strength (int): Base damage stat
        dexterity (int): Affects hit chance
        hostility (int): Aggro range in tiles
        char (str): Display character
        color (str): Display color
        is_chasing (bool): Whether actively pursuing player
    """
    
    def __init__(self, enemy_type: str, x: int, y: int):
        """
        Initialize an enemy.
        
        Args:
            enemy_type: Enemy type from EnemyType constants
            x: Starting X coordinate
            y: Starting Y coordinate
        """
        self.enemy_type = enemy_type
        self._position = Position(x, y)
        
        from config.game_config import ENEMY_STATS
        stats = ENEMY_STATS[enemy_type]
        self.health = stats['health']
        self.max_health = stats['health']
        self.strength = stats['strength']
        self.dexterity = stats['dexterity']
        self.hostility = stats['hostility']
        self.char = stats['char']
        self.color = stats['color']
        
        self.is_chasing = False
        
        # Universal optional attributes (initialized with defaults)
        # These allow enemy-specific behaviors without hasattr checks
        self.is_disguised = False  # For Mimic
        self.is_invisible = False  # For Ghost
        self.is_resting = False  # For Ogre
        self.will_counterattack = False  # For Ogre
        self.first_attack_against = False  # For Vampire
        self.teleport_cooldown = 0  # For Ghost
        self.invisibility_cooldown = 0  # For Ghost
        self.diagonal_direction = None  # For Snake
        self.direction_cooldown = 0  # For Snake
    
    @property
    def position(self) -> Position:
        """Get enemy position as Position object."""
        return self._position
    
    @position.setter
    def position(self, value):
        """Set position from tuple or Position."""
        if isinstance(value, Position):
            self._position = value
        else:
            self._position = Position(value[0], value[1])
    
    def is_alive(self) -> bool:
        """Check if enemy is still alive."""
        return self.health > 0
    
    def take_damage(self, damage: int) -> None:
        """
        Apply damage to the enemy.
        
        Args:
            damage: Amount of damage to apply
        """
        self.health -= damage
        if self.health < 0:
            self.health = 0
    
    def move_to(self, x: int, y: int) -> None:
        """
        Update enemy position.
        
        Args:
            x: New X coordinate
            y: New Y coordinate
        """
        self._position.update(x, y)
    
    def get_x(self) -> int:
        """Get enemy's X coordinate."""
        return self._position.x
    
    def get_y(self) -> int:
        """Get enemy's Y coordinate."""
        return self._position.y
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(pos={self._position.tuple}, "
                f"hp={self.health}/{self.max_health})")


class Zombie(Enemy):
    """
    Zombie enemy: low dexterity, medium strength and hostility, high health.
    Standard chasing behavior with no special abilities.
    """
    
    def __init__(self, x: int, y: int):
        from config.game_config import EnemyType
        super().__init__(EnemyType.ZOMBIE, x, y)


class Vampire(Enemy):
    """
    Vampire enemy: high dexterity, hostility, and health; medium strength.
    
    Special abilities:
    - Steals max health on successful attack
    - First attack against vampire always misses
    """
    
    def __init__(self, x: int, y: int):
        from config.game_config import EnemyType
        super().__init__(EnemyType.VAMPIRE, x, y)
        self.first_attack_against = True


class Ghost(Enemy):
    """
    Ghost enemy: high dexterity, low strength, hostility, and health.
    
    Special abilities:
    - Teleports within room periodically
    - Can become invisible until combat begins
    """
    
    def __init__(self, x: int, y: int):
        from config.game_config import EnemyType
        super().__init__(EnemyType.GHOST, x, y)
        self.is_invisible = False
        self.teleport_cooldown = 0


class Ogre(Enemy):
    """
    Ogre enemy: very high strength and health, low dexterity, medium hostility.
    
    Special abilities:
    - Moves two tiles per turn
    - Rests for one turn after attacking
    - Guaranteed counterattack after resting
    """
    
    def __init__(self, x: int, y: int):
        from config.game_config import EnemyType
        super().__init__(EnemyType.OGRE, x, y)
        self.is_resting = False
        self.will_counterattack = False


class SnakeMage(Enemy):
    """
    Snake Mage enemy: very high dexterity, high hostility.
    
    Special abilities:
    - Moves diagonally
    - Constantly switches direction
    - Can put player to sleep for one turn on successful attack
    """
    
    def __init__(self, x: int, y: int):
        from config.game_config import EnemyType
        super().__init__(EnemyType.SNAKE_MAGE, x, y)
        self.direction = 1


class Mimic(Enemy):
    """
    Mimic enemy: high dexterity, low strength, high health, low hostility.
    
    Special abilities:
    - Disguises as items until revealed
    - Only reveals when player is adjacent or attacks
    """
    
    REVEAL_DISTANCE = 1
    DEFAULT_DISGUISE = '%'
    
    def __init__(self, x: int, y: int, disguise_type: Optional[str] = None):
        """
        Initialize a Mimic enemy.
        
        Args:
            x: X coordinate
            y: Y coordinate
            disguise_type: Character to display as disguise
        """
        from config.game_config import EnemyType
        super().__init__(EnemyType.MIMIC, x, y)
        self.is_disguised = True
        self.disguise_char = disguise_type or self.DEFAULT_DISGUISE
        self.reveal_distance = self.REVEAL_DISTANCE
    
    def reveal(self) -> None:
        """Reveal the mimic's true form."""
        self.is_disguised = False
    
    def should_reveal(self, player_pos) -> bool:
        """
        Check if mimic should reveal based on player proximity.
        
        Args:
            player_pos: (x, y) player position or Position object
            
        Returns:
            True if mimic should reveal itself
        """
        if not self.is_disguised:
            return False
        
        return self._position.is_adjacent_to(player_pos)


def create_enemy(enemy_type: str, x: int, y: int, **kwargs) -> Enemy:
    """
    Factory function to create enemy instances.
    
    Args:
        enemy_type: Enemy type from EnemyType constants
        x: X coordinate
        y: Y coordinate
        **kwargs: Additional arguments for specific enemy types
        
    Returns:
        Instance of the appropriate enemy class
        
    Raises:
        ValueError: If enemy_type is unknown
    """
    from config.game_config import EnemyType
    
    enemy_classes = {
        EnemyType.ZOMBIE: Zombie,
        EnemyType.VAMPIRE: Vampire,
        EnemyType.GHOST: Ghost,
        EnemyType.OGRE: Ogre,
        EnemyType.SNAKE_MAGE: SnakeMage,
        EnemyType.MIMIC: Mimic
    }
    
    enemy_class = enemy_classes.get(enemy_type)
    if enemy_class:
        if enemy_type == EnemyType.MIMIC:
            disguise = kwargs.get('disguise_type', '%')
            return enemy_class(x, y, disguise)
        else:
            return enemy_class(x, y)
    
    raise ValueError(f"Unknown enemy type: {enemy_type}")
