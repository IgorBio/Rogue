"""
Statistics tracking and leaderboard persistence.

This module tracks detailed gameplay metrics during each run and maintains
a persistent leaderboard of all completed runs, enabling progress tracking
and performance analysis.
"""
import json
import os
from datetime import datetime
from common.logging_utils import get_logger


# Persistence configuration
DEFAULT_SAVE_DIR = 'saves'
LEADERBOARD_FILENAME = 'leaderboard.json'
_logger = get_logger(__name__)

# Display configuration
DEFAULT_TOP_RUNS_COUNT = 10
HIT_EFFICIENCY_PERCENT = 100


class Statistics:
    """
    Tracks comprehensive statistics for a single game run.
    
    Records all player actions, combat outcomes, progression metrics,
    and final character state. Can be serialized to JSON for persistence.
    
    Attributes:
        treasure_collected (int): Total treasure accumulated
        level_reached (int): Deepest level reached (1-21)
        enemies_defeated (int): Number of enemies killed
        food_consumed (int): Food items used
        elixirs_used (int): Elixir items consumed
        scrolls_read (int): Scroll items used
        weapons_equipped (int): Times weapons were equipped
        attacks_made (int): Total attacks attempted
        hits_taken (int): Times player was hit
        damage_dealt (int): Total damage dealt to enemies
        damage_received (int): Total damage taken
        tiles_moved (int): Distance traveled in tiles
        items_collected (int): Items picked up
        deaths (int): Number of deaths (0 or 1 per run)
        victory (bool): Whether player completed all levels
        final_health (int): Health at game end
        final_strength (int): Strength at game end
        final_dexterity (int): Dexterity at game end
        timestamp (str): ISO format datetime of game end
        playtime_seconds (int): Reserved for future timing feature
    """
    
    def __init__(self):
        """Initialize statistics with zero values."""
        # Core progression
        self.treasure_collected = 0
        self.level_reached = 1
        self.enemies_defeated = 0
        
        # Item usage
        self.food_consumed = 0
        self.elixirs_used = 0
        self.scrolls_read = 0
        self.weapons_equipped = 0
        
        # Combat metrics
        self.attacks_made = 0
        self.hits_taken = 0
        self.damage_dealt = 0
        self.damage_received = 0
        
        # Exploration
        self.tiles_moved = 0
        self.items_collected = 0
        
        # Run outcome
        self.deaths = 0
        self.victory = False
        
        # Final state
        self.final_health = 0
        self.final_strength = 0
        self.final_dexterity = 0
        
        # Metadata
        self.timestamp = None
        self.playtime_seconds = 0
    
    def record_enemy_defeated(self, treasure_reward):
        """
        Record enemy defeat and treasure gain.
        
        Args:
            treasure_reward (int): Treasure dropped by enemy
        """
        self.enemies_defeated += 1
        self.treasure_collected += treasure_reward
    
    def record_food_used(self):
        """Record food consumption."""
        self.food_consumed += 1
    
    def record_elixir_used(self):
        """Record elixir usage."""
        self.elixirs_used += 1
    
    def record_scroll_used(self):
        """Record scroll reading."""
        self.scrolls_read += 1
    
    def record_weapon_equipped(self):
        """Record weapon equipping."""
        self.weapons_equipped += 1
    
    def record_attack(self, hit, damage):
        """
        Record attack attempt and outcome.
        
        Args:
            hit (bool): Whether attack landed
            damage (int): Damage dealt (0 if missed)
        """
        self.attacks_made += 1
        if hit:
            self.damage_dealt += damage
    
    def record_hit_taken(self, damage):
        """
        Record damage taken from enemy.
        
        Args:
            damage (int): Damage received
        """
        self.hits_taken += 1
        self.damage_received += damage
    
    def record_movement(self):
        """Record one tile of movement."""
        self.tiles_moved += 1
    
    def record_item_collected(self):
        """Record item pickup."""
        self.items_collected += 1
    
    def record_level_reached(self, level):
        """
        Update deepest level reached.
        
        Args:
            level (int): Level number reached
        """
        self.level_reached = max(self.level_reached, level)
    
    def record_game_end(self, character, victory=False):
        """
        Record final game state at completion.
        
        Args:
            character: Character instance at game end
            victory (bool): Whether player won the game
        """
        self.final_health = character.health
        self.final_strength = character.strength
        self.final_dexterity = character.dexterity
        self.victory = victory
        self.timestamp = datetime.now().isoformat()
        
        if not victory:
            self.deaths = 1
    
    def get_summary_text(self):
        """
        Generate human-readable statistics summary.
        
        Returns:
            list: Formatted strings for display
        """
        summary = []
        
        # Progression section
        summary.append("=== PROGRESSION ===")
        summary.append(f"Deepest Level: {self.level_reached}/21")
        summary.append(f"Treasure: {self.treasure_collected}")
        summary.append(f"Victory: {'YES' if self.victory else 'No'}")
        summary.append("")
        
        # Combat section
        summary.append("=== COMBAT ===")
        summary.append(f"Enemies Defeated: {self.enemies_defeated}")
        summary.append(f"Attacks Made: {self.attacks_made}")
        summary.append(f"Hits Taken: {self.hits_taken}")
        summary.append(f"Damage Dealt: {self.damage_dealt}")
        summary.append(f"Damage Received: {self.damage_received}")
        
        # Combat efficiency
        if self.attacks_made > 0:
            hit_rate = (self.damage_dealt / self.attacks_made) * HIT_EFFICIENCY_PERCENT
            summary.append(f"Hit Efficiency: {hit_rate:.1f}%")
        summary.append("")
        
        # Items section
        summary.append("=== ITEMS ===")
        summary.append(f"Items Collected: {self.items_collected}")
        summary.append(f"Food Consumed: {self.food_consumed}")
        summary.append(f"Elixirs Used: {self.elixirs_used}")
        summary.append(f"Scrolls Read: {self.scrolls_read}")
        summary.append(f"Weapons Equipped: {self.weapons_equipped}")
        summary.append("")
        
        # Exploration section
        summary.append("=== EXPLORATION ===")
        summary.append(f"Tiles Traversed: {self.tiles_moved}")
        
        # Efficiency metrics
        if self.tiles_moved > 0:
            items_per_tile = self.items_collected / self.tiles_moved
            summary.append(f"Items per Tile: {items_per_tile:.3f}")
        
        return summary
    
    def to_dict(self):
        """
        Convert statistics to dictionary for JSON serialization.
        
        Returns:
            dict: All statistics as key-value pairs
        """
        return {
            'treasure_collected': self.treasure_collected,
            'level_reached': self.level_reached,
            'enemies_defeated': self.enemies_defeated,
            'food_consumed': self.food_consumed,
            'elixirs_used': self.elixirs_used,
            'scrolls_read': self.scrolls_read,
            'weapons_equipped': self.weapons_equipped,
            'attacks_made': self.attacks_made,
            'hits_taken': self.hits_taken,
            'damage_dealt': self.damage_dealt,
            'damage_received': self.damage_received,
            'tiles_moved': self.tiles_moved,
            'items_collected': self.items_collected,
            'deaths': self.deaths,
            'victory': self.victory,
            'final_health': self.final_health,
            'final_strength': self.final_strength,
            'final_dexterity': self.final_dexterity,
            'timestamp': self.timestamp
        }
    
    @staticmethod
    def from_dict(data):
        """
        Create Statistics instance from dictionary.
        
        Args:
            data (dict): Statistics data from JSON
        
        Returns:
            Statistics: Reconstructed statistics instance
        """
        stats = Statistics()
        for key, value in data.items():
            if hasattr(stats, key):
                setattr(stats, key, value)
        return stats


class StatisticsManager:
    """
    Manages leaderboard persistence and aggregate statistics.
    
    Saves completed runs to leaderboard file, provides leaderboard queries,
    and calculates aggregate statistics across all runs.
    
    Attributes:
        save_dir (str): Directory for save files
        leaderboard_file (str): Full path to leaderboard JSON
    """
    
    def __init__(self, save_dir=DEFAULT_SAVE_DIR):
        """
        Initialize statistics manager and ensure save directory exists.
        
        Args:
            save_dir (str): Directory for save files
        """
        self.save_dir = save_dir
        self.leaderboard_file = os.path.join(save_dir, LEADERBOARD_FILENAME)
        os.makedirs(save_dir, exist_ok=True)
    
    def save_run(self, statistics):
        """
        Save completed run to leaderboard.
        
        Appends run to leaderboard and sorts by treasure collected.
        
        Args:
            statistics: Statistics instance to save
        """
        leaderboard = self.load_leaderboard()
        leaderboard.append(statistics.to_dict())
        
        # Sort by treasure (highest first)
        leaderboard.sort(key=lambda x: x['treasure_collected'], reverse=True)
        
        try:
            with open(self.leaderboard_file, 'w') as f:
                json.dump(leaderboard, f, indent=2)
        except Exception as e:
            _logger.exception("Failed to save leaderboard to '%s': %s", self.leaderboard_file, e)
    
    def load_leaderboard(self):
        """
        Load complete leaderboard from file.
        
        Returns:
            list: List of run dictionaries, sorted by treasure
        """
        if not os.path.exists(self.leaderboard_file):
            return []
        
        try:
            with open(self.leaderboard_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            _logger.exception("Failed to load leaderboard from '%s': %s", self.leaderboard_file, e)
            return []
    
    def get_top_runs(self, count=DEFAULT_TOP_RUNS_COUNT):
        """
        Get top N runs by treasure.
        
        Args:
            count (int): Number of runs to return
        
        Returns:
            list: Top run dictionaries
        """
        leaderboard = self.load_leaderboard()
        return leaderboard[:count]
    
    def get_total_stats(self):
        """
        Calculate aggregate statistics across all runs.
        
        Provides totals and averages for all tracked metrics.
        
        Returns:
            dict: Aggregate statistics or None if no runs
        """
        leaderboard = self.load_leaderboard()
        
        if not leaderboard:
            return None
        
        totals = {
            'total_runs': len(leaderboard),
            'total_victories': sum(
                1 for run in leaderboard if run.get('victory', False)
            ),
            'total_deaths': sum(run.get('deaths', 0) for run in leaderboard),
            'total_enemies_defeated': sum(
                run.get('enemies_defeated', 0) for run in leaderboard
            ),
            'total_treasure': sum(
                run.get('treasure_collected', 0) for run in leaderboard
            ),
            'deepest_level': max(
                run.get('level_reached', 1) for run in leaderboard
            ),
            'most_treasure': max(
                run.get('treasure_collected', 0) for run in leaderboard
            ),
            'total_tiles_moved': sum(
                run.get('tiles_moved', 0) for run in leaderboard
            ),
            'total_attacks': sum(
                run.get('attacks_made', 0) for run in leaderboard
            ),
            'total_damage_dealt': sum(
                run.get('damage_dealt', 0) for run in leaderboard
            ),
            'total_damage_received': sum(
                run.get('damage_received', 0) for run in leaderboard
            ),
            'total_food_consumed': sum(
                run.get('food_consumed', 0) for run in leaderboard
            ),
            'total_items_collected': sum(
                run.get('items_collected', 0) for run in leaderboard
            ),
        }
        
        # Calculate averages
        if totals['total_runs'] > 0:
            totals['avg_treasure_per_run'] = (
                totals['total_treasure'] / totals['total_runs']
            )
            totals['avg_level_reached'] = (
                sum(run.get('level_reached', 1) for run in leaderboard) /
                totals['total_runs']
            )
            totals['avg_enemies_per_run'] = (
                totals['total_enemies_defeated'] / totals['total_runs']
            )
        
        return totals
    
    def get_player_rank(self, treasure_value):
        """
        Calculate rank for specific treasure value.
        
        Args:
            treasure_value (int): Treasure amount to rank
        
        Returns:
            int: Rank (1-based, 1 is best)
        """
        leaderboard = self.load_leaderboard()
        rank = sum(
            1 for run in leaderboard 
            if run.get('treasure_collected', 0) > treasure_value
        ) + 1
        return rank
    
    def get_statistics_by_level(self):
        """
        Group statistics by deepest level reached.
        
        Useful for analyzing difficulty curve and progression.
        
        Returns:
            dict: Mapping of level numbers to aggregated stats
        """
        leaderboard = self.load_leaderboard()
        level_stats = {}
        
        for run in leaderboard:
            level = run.get('level_reached', 1)
            
            if level not in level_stats:
                level_stats[level] = {
                    'runs': 0,
                    'victories': 0,
                    'avg_treasure': 0,
                    'total_treasure': 0
                }
            
            level_stats[level]['runs'] += 1
            if run.get('victory', False):
                level_stats[level]['victories'] += 1
            level_stats[level]['total_treasure'] += run.get('treasure_collected', 0)
        
        # Calculate averages
        for level, stats in level_stats.items():
            if stats['runs'] > 0:
                stats['avg_treasure'] = stats['total_treasure'] / stats['runs']
        
        return level_stats
    
    def clear_leaderboard(self):
        """
        Clear all statistics.
        
        Used for testing or complete reset. Deletes leaderboard file.
        """
        if os.path.exists(self.leaderboard_file):
            os.remove(self.leaderboard_file)
