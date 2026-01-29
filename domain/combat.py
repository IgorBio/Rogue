"""
Combat mechanics for turn-based battles.

This module handles all combat calculations including hit chance,
damage calculation, and treasure rewards from defeated enemies.
"""
import random


# Combat balance constants
BASE_HIT_CHANCE = 0.5
DEXTERITY_HIT_MODIFIER = 0.02
MIN_HIT_CHANCE = 0.1
MAX_HIT_CHANCE = 0.95

DAMAGE_RANDOMNESS_MIN = 0.8
DAMAGE_RANDOMNESS_MAX = 1.2
MIN_DAMAGE = 1

TREASURE_LEVEL_SCALING = 0.1
TREASURE_RANDOMNESS_MIN = 0.8
TREASURE_RANDOMNESS_MAX = 1.2
BASE_MIN_TREASURE = 10
TREASURE_PER_LEVEL = 2


def calculate_hit_chance(attacker_dex, defender_dex):
    """
    Calculate the probability of an attack hitting.
    
    Formula: 50% base + 2% per point of dexterity difference.
    Result is clamped between 10% and 95%.
    
    Args:
        attacker_dex (int): Attacker's dexterity stat
        defender_dex (int): Defender's dexterity stat
    
    Returns:
        float: Hit probability between 0.0 and 1.0
    """
    dex_difference = attacker_dex - defender_dex
    dex_modifier = dex_difference * DEXTERITY_HIT_MODIFIER
    hit_chance = BASE_HIT_CHANCE + dex_modifier
    
    return max(MIN_HIT_CHANCE, min(MAX_HIT_CHANCE, hit_chance))


def calculate_damage(attacker_strength, weapon=None):
    """
    Calculate damage dealt by an attack.
    
    Base damage comes from strength, with optional weapon bonus.
    Final damage has randomness applied (80%-120%).
    
    Args:
        attacker_strength (int): Attacker's strength stat
        weapon (Weapon): Optional equipped weapon
    
    Returns:
        int: Damage amount (minimum 1)
    """
    base_damage = attacker_strength
    weapon_bonus = weapon.strength_bonus if weapon else 0
    total_damage = base_damage + weapon_bonus
    
    randomness = random.uniform(DAMAGE_RANDOMNESS_MIN, DAMAGE_RANDOMNESS_MAX)
    final_damage = int(total_damage * randomness)
    
    return max(MIN_DAMAGE, final_damage)


def resolve_attack(attacker, defender, attacker_weapon=None):
    """
    Resolve a complete attack from attacker to defender.
    
    Determines hit/miss, calculates damage, and applies it to defender.
    
    Args:
        attacker: Attacking entity (Character or Enemy)
        defender: Defending entity (Character or Enemy)
        attacker_weapon (Weapon): Optional weapon for attacker
    
    Returns:
        dict: Attack results containing:
            - hit (bool): Whether attack hit
            - damage (int): Damage dealt (0 if miss)
            - killed (bool): Whether defender was killed
            - attacker_name (str): Display name of attacker
            - defender_name (str): Display name of defender
            - hit_chance (float): Probability of hit
    """
    attacker_name = _get_entity_name(attacker)
    defender_name = _get_entity_name(defender)
    
    hit_chance = calculate_hit_chance(attacker.dexterity, defender.dexterity)
    hit = random.random() < hit_chance
    
    result = {
        'hit': hit,
        'damage': 0,
        'killed': False,
        'attacker_name': attacker_name,
        'defender_name': defender_name,
        'hit_chance': hit_chance
    }
    
    if not hit:
        return result
    
    damage = calculate_damage(attacker.strength, attacker_weapon)
    defender.take_damage(damage)
    
    result['damage'] = damage
    result['killed'] = not defender.is_alive()
    
    return result


def calculate_treasure_reward(enemy, level_number=1):
    """
    Calculate treasure reward for defeating an enemy.
    
    Treasure scales with enemy difficulty and level depth.
    Higher levels yield 10% more treasure per level.
    
    Args:
        enemy: Defeated enemy instance
        level_number (int): Current level depth (for scaling rewards)
    
    Returns:
        int: Treasure value
    """
    base_value = (
        enemy.max_health +
        enemy.strength * 2 +
        enemy.dexterity * 2 +
        enemy.hostility * 3
    )
    
    level_multiplier = 1.0 + (level_number - 1) * TREASURE_LEVEL_SCALING
    random_multiplier = random.uniform(TREASURE_RANDOMNESS_MIN, TREASURE_RANDOMNESS_MAX)
    
    treasure = int(base_value * level_multiplier * random_multiplier)
    min_treasure = BASE_MIN_TREASURE + (level_number * TREASURE_PER_LEVEL)
    
    return max(min_treasure, treasure)


def get_combat_message(result):
    """
    Generate a readable combat message from attack result.
    
    Args:
        result (dict): Dictionary from resolve_attack()
    
    Returns:
        str: Human-readable combat description
    """
    attacker = result['attacker_name']
    defender = result['defender_name']
    
    if not result['hit']:
        return f"{attacker} attacked {defender} but missed!"
    
    damage = result['damage']
    
    if result['killed']:
        return f"{attacker} hit {defender} for {damage} damage and killed them!"
    else:
        return f"{attacker} hit {defender} for {damage} damage!"


def _get_entity_name(entity):
    """
    Get display name for an entity.
    
    Args:
        entity: Character or Enemy instance
        
    Returns:
        str: Display name
    """
    if hasattr(entity, 'enemy_type'):
        return entity.enemy_type.capitalize()
    else:
        return "You"