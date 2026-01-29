"""
Dynamic Difficulty Adjustment System.

This module adapts game difficulty based on player performance,
making the game more challenging for skilled players and more
forgiving for struggling players.
"""


# Performance thresholds
HEALTH_EXCELLENT_THRESHOLD = 0.8
HEALTH_GOOD_THRESHOLD = 0.6
HEALTH_AVERAGE_THRESHOLD = 0.4
HEALTH_LOW_THRESHOLD = 0.2

DAMAGE_RATIO_EXCELLENT = 3.0
DAMAGE_RATIO_STRONG = 2.0
DAMAGE_RATIO_AHEAD = 1.0
DAMAGE_RATIO_BEHIND = 0.5
DAMAGE_RATIO_STRUGGLING = 0.3

ITEM_USAGE_EFFICIENT = 0.5
ITEM_USAGE_AVERAGE = 0.3

COMBAT_MULTIPLIER_LOW = 0.5
COMBAT_MULTIPLIER_HIGH = 1.5

# Performance score thresholds
PERFORMANCE_EXCELLENT = 1.3
PERFORMANCE_STRUGGLING = 0.8

# Difficulty modifier limits
MIN_MODIFIER = 0.5
MAX_MODIFIER = 1.5
ADJUSTMENT_RATE = 0.1
DRIFT_RATE_FACTOR = 0.3

# Emergency healing thresholds
EMERGENCY_HEALTH_THRESHOLD = 0.25
CRITICAL_HEALTH_THRESHOLD = 0.15
EMERGENCY_HEALING_MODIFIER = 1.2


class DifficultyManager:
    """
    Manages dynamic difficulty adjustment based on player performance.
    
    Tracks player metrics across levels and adjusts enemy difficulty
    and item availability to maintain appropriate challenge.
    
    Attributes:
        levels_completed (int): Number of levels finished
        total_damage_taken (int): Cumulative damage received
        total_damage_dealt (int): Cumulative damage dealt
        deaths_this_session (int): Number of deaths
        average_health_per_level (list): Health percentages at level ends
        time_per_level (list): Time spent per level
        enemy_count_modifier (float): Enemy spawn multiplier
        enemy_stat_modifier (float): Enemy strength multiplier
        item_spawn_modifier (float): Item availability multiplier
        healing_modifier (float): Healing item effectiveness multiplier
    """
    
    def __init__(self):
        """Initialize the difficulty manager."""
        self.levels_completed = 0
        self.total_damage_taken = 0
        self.total_damage_dealt = 0
        self.deaths_this_session = 0
        self.average_health_per_level = []
        self.time_per_level = []
        
        self.enemy_count_modifier = 1.0
        self.enemy_stat_modifier = 1.0
        self.item_spawn_modifier = 1.0
        self.healing_modifier = 1.0
        
        self.MIN_MODIFIER = MIN_MODIFIER
        self.MAX_MODIFIER = MAX_MODIFIER
        self.ADJUSTMENT_RATE = ADJUSTMENT_RATE
    
    def update_performance(self, stats, character):
        """
        Update performance tracking with current game state.
        
        Args:
            stats: Statistics object from current session
            character: Character object
        """
        if character.max_health > 0:
            health_percent = character.health / character.max_health
            self.average_health_per_level.append(health_percent)
        
        self.total_damage_taken = stats.damage_received
        self.total_damage_dealt = stats.damage_dealt
    
    def calculate_difficulty_adjustment(self, character, stats, level_number):
        """
        Calculate difficulty adjustments based on player performance.
        
        Args:
            character: Character object
            stats: Statistics object
            level_number (int): Current level number
        
        Returns:
            dict: Difficulty modifiers containing:
                - enemy_count_modifier (float)
                - enemy_stat_modifier (float)
                - item_spawn_modifier (float)
                - healing_modifier (float)
                - performance_score (float)
        """
        performance_score = self._calculate_performance_score(character, stats, level_number)
        self._adjust_modifiers(performance_score)
        
        return {
            'enemy_count_modifier': self.enemy_count_modifier,
            'enemy_stat_modifier': self.enemy_stat_modifier,
            'item_spawn_modifier': self.item_spawn_modifier,
            'healing_modifier': self.healing_modifier,
            'performance_score': performance_score
        }
    
    def _calculate_performance_score(self, character, stats, level_number):
        """
        Calculate overall performance score.
        
        Evaluates player performance across multiple metrics:
        - Health management
        - Combat efficiency
        - Resource usage
        - Progress speed
        
        Returns:
            float: Score between 0.0 (struggling) and 2.0 (excelling)
                   1.0 = balanced performance
        """
        scores = []
        
        health_score = self._calculate_health_score(character)
        if health_score is not None:
            scores.append(health_score)
        
        combat_score = self._calculate_combat_score(stats)
        if combat_score is not None:
            scores.append(combat_score)
        
        resource_score = self._calculate_resource_score(stats)
        if resource_score is not None:
            scores.append(resource_score)
        
        speed_score = self._calculate_speed_score(stats, level_number)
        scores.append(speed_score)
        
        if scores:
            weights = [1.5, 1.2, 1.0, 0.8][:len(scores)]
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            total_weight = sum(weights[:len(scores)])
            return weighted_sum / total_weight
        
        return 1.0
    
    def _calculate_health_score(self, character):
        """
        Calculate health management score.
        
        Args:
            character: Character object
            
        Returns:
            float: Score between 0.4 and 1.8, or None if no data
        """
        if character.max_health <= 0:
            return None
        
        health_percent = character.health / character.max_health
        
        if health_percent > HEALTH_EXCELLENT_THRESHOLD:
            return 1.8
        elif health_percent > HEALTH_GOOD_THRESHOLD:
            return 1.3
        elif health_percent > HEALTH_AVERAGE_THRESHOLD:
            return 1.0
        elif health_percent > HEALTH_LOW_THRESHOLD:
            return 0.7
        else:
            return 0.4
    
    def _calculate_combat_score(self, stats):
        """
        Calculate combat efficiency score.
        
        Args:
            stats: Statistics object
            
        Returns:
            float: Score between 0.4 and 1.8, or None if no data
        """
        if stats.hits_taken <= 0 or stats.attacks_made <= 0:
            return None
        
        damage_ratio = stats.damage_dealt / max(1, stats.damage_received)
        
        if damage_ratio > DAMAGE_RATIO_EXCELLENT:
            return 1.8
        elif damage_ratio > DAMAGE_RATIO_STRONG:
            return 1.4
        elif damage_ratio > DAMAGE_RATIO_AHEAD:
            return 1.1
        elif damage_ratio > DAMAGE_RATIO_BEHIND:
            return 0.9
        elif damage_ratio > DAMAGE_RATIO_STRUGGLING:
            return 0.6
        else:
            return 0.4
    
    def _calculate_resource_score(self, stats):
        """
        Calculate resource management score.
        
        Args:
            stats: Statistics object
            
        Returns:
            float: Score between 0.8 and 1.4, or None if no data
        """
        if stats.items_collected <= 0:
            return None
        
        total_items_used = (
            stats.food_consumed + 
            stats.elixirs_used + 
            stats.scrolls_read
        )
        usage_ratio = total_items_used / max(1, stats.items_collected)
        
        if usage_ratio > ITEM_USAGE_EFFICIENT:
            return 1.2
        elif usage_ratio > ITEM_USAGE_AVERAGE:
            return 1.0
        else:
            return 1.4
    
    def _calculate_speed_score(self, stats, level_number):
        """
        Calculate progress speed score.
        
        Args:
            stats: Statistics object
            level_number (int): Current level number
            
        Returns:
            float: Score between 0.8 and 1.3
        """
        expected_enemies = level_number * 3
        
        if stats.enemies_defeated < expected_enemies * COMBAT_MULTIPLIER_LOW:
            return 0.8
        elif stats.enemies_defeated > expected_enemies * COMBAT_MULTIPLIER_HIGH:
            return 1.3
        else:
            return 1.0
    
    def _adjust_modifiers(self, performance_score):
        """
        Adjust difficulty modifiers based on performance score.
        
        Args:
            performance_score (float): Score between 0.0 and 2.0
        """
        if performance_score > PERFORMANCE_EXCELLENT:
            self._increase_difficulty()
        elif performance_score < PERFORMANCE_STRUGGLING:
            self._decrease_difficulty()
        else:
            self._drift_toward_neutral()
    
    def _increase_difficulty(self):
        """Increase difficulty for excelling players."""
        self.enemy_count_modifier = min(
            self.MAX_MODIFIER,
            self.enemy_count_modifier + self.ADJUSTMENT_RATE
        )
        self.enemy_stat_modifier = min(
            self.MAX_MODIFIER,
            self.enemy_stat_modifier + self.ADJUSTMENT_RATE * 0.5
        )
        
        self.item_spawn_modifier = max(
            self.MIN_MODIFIER,
            self.item_spawn_modifier - self.ADJUSTMENT_RATE
        )
        self.healing_modifier = max(
            self.MIN_MODIFIER,
            self.healing_modifier - self.ADJUSTMENT_RATE * 0.5
        )
    
    def _decrease_difficulty(self):
        """Decrease difficulty for struggling players."""
        self.enemy_count_modifier = max(
            self.MIN_MODIFIER,
            self.enemy_count_modifier - self.ADJUSTMENT_RATE
        )
        self.enemy_stat_modifier = max(
            self.MIN_MODIFIER,
            self.enemy_stat_modifier - self.ADJUSTMENT_RATE * 0.5
        )
        
        self.item_spawn_modifier = min(
            self.MAX_MODIFIER,
            self.item_spawn_modifier + self.ADJUSTMENT_RATE
        )
        self.healing_modifier = min(
            self.MAX_MODIFIER,
            self.healing_modifier + self.ADJUSTMENT_RATE * 0.5
        )
    
    def _drift_toward_neutral(self):
        """Gradually drift modifiers back to neutral (1.0)."""
        drift_rate = self.ADJUSTMENT_RATE * DRIFT_RATE_FACTOR
        
        if self.enemy_count_modifier > 1.0:
            self.enemy_count_modifier -= drift_rate
        elif self.enemy_count_modifier < 1.0:
            self.enemy_count_modifier += drift_rate
        
        if self.item_spawn_modifier > 1.0:
            self.item_spawn_modifier -= drift_rate
        elif self.item_spawn_modifier < 1.0:
            self.item_spawn_modifier += drift_rate
    
    def should_spawn_emergency_healing(self, character):
        """
        Determine if emergency healing should spawn.
        
        Spawns emergency healing when player is critically low on health
        and difficulty adjustments indicate they're struggling.
        
        Args:
            character: Character object
        
        Returns:
            bool: True if emergency healing should spawn
        """
        if character.max_health <= 0:
            return False
        
        health_percent = character.health / character.max_health
        
        if health_percent < EMERGENCY_HEALTH_THRESHOLD and self.healing_modifier > EMERGENCY_HEALING_MODIFIER:
            return True
        
        if health_percent < CRITICAL_HEALTH_THRESHOLD:
            return True
        
        return False
    
    def get_difficulty_description(self):
        """
        Get a human-readable description of current difficulty.
        
        Returns:
            str: Difficulty level description
        """
        avg_modifier = (
            self.enemy_count_modifier + 
            self.enemy_stat_modifier + 
            (2.0 - self.item_spawn_modifier)
        ) / 3.0
        
        if avg_modifier > 1.3:
            return "Very Hard"
        elif avg_modifier > 1.15:
            return "Hard"
        elif avg_modifier > 0.95:
            return "Normal"
        elif avg_modifier > 0.75:
            return "Easy"
        else:
            return "Very Easy"
    
    def reset(self):
        """Reset difficulty manager for new game session."""
        self.__init__()