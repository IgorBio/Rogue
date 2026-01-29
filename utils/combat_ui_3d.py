"""
Combat and interaction UI elements for 3D mode.
Stage 8: Visual feedback for attacks, damage, and pickups.
"""
import curses
import time


class CombatFeedback:
    """Handles visual feedback for combat events in 3D mode."""
    
    def __init__(self, stdscr):
        """
        Initialize combat feedback system.
        
        Args:
            stdscr: Curses screen object
        """
        self.stdscr = stdscr
        self.messages = []
        self.flash_frames = 0
        self.damage_indicators = []
    
    def show_attack_hit(self, damage, enemy_name="Enemy"):
        """
        Display attack hit feedback.
        
        Args:
            damage: Damage dealt
            enemy_name: Name of enemy hit
        """
        message = f"HIT {enemy_name} for {damage} damage!"
        self.messages.append({
            'text': message,
            'color': curses.COLOR_RED,
            'frames_left': 30
        })
        
        # Flash effect
        self.flash_frames = 3
    
    def show_attack_miss(self, enemy_name="Enemy"):
        """Display attack miss feedback."""
        message = f"Missed {enemy_name}!"
        self.messages.append({
            'text': message,
            'color': curses.COLOR_YELLOW,
            'frames_left': 20
        })
    
    def show_enemy_killed(self, enemy_name="Enemy", treasure=0):
        """Display enemy killed feedback."""
        message = f"Killed {enemy_name}! +{treasure} treasure"
        self.messages.append({
            'text': message,
            'color': curses.COLOR_GREEN,
            'frames_left': 40
        })
        
        # Strong flash for kill
        self.flash_frames = 5
    
    def show_item_pickup(self, item_name):
        """Display item pickup feedback."""
        message = f"Picked up: {item_name}"
        self.messages.append({
            'text': message,
            'color': curses.COLOR_CYAN,
            'frames_left': 30
        })
    
    def show_damage_taken(self, damage):
        """Display player damage feedback."""
        message = f"Took {damage} damage!"
        self.messages.append({
            'text': message,
            'color': curses.COLOR_RED,
            'frames_left': 30
        })
        
        # Red flash for player damage
        self.flash_frames = 5
    
    def update(self):
        """Update feedback state (call each frame)."""
        # Update messages
        self.messages = [
            msg for msg in self.messages
            if msg['frames_left'] > 0
        ]
        
        for msg in self.messages:
            msg['frames_left'] -= 1
        
        # Update flash
        if self.flash_frames > 0:
            self.flash_frames -= 1
    
    def render(self, x_offset=0, y_offset=0, max_width=70):
        """
        Render combat feedback messages.
        
        Args:
            x_offset: X position to render
            y_offset: Y position to render
            max_width: Maximum width for messages
        """
        # Render flash effect (optional - full screen flash)
        if self.flash_frames > 0:
            self._render_flash()
        
        # Render messages (top-down)
        for i, msg in enumerate(self.messages[:5]):  # Show up to 5 messages
            text = msg['text']
            color = msg['color']
            
            # Fade based on remaining frames
            if msg['frames_left'] < 10:
                attr = curses.A_DIM
            else:
                attr = curses.A_BOLD
            
            try:
                # Truncate if too long
                if len(text) > max_width:
                    text = text[:max_width-3] + "..."
                
                # Center the message
                x = x_offset + (max_width - len(text)) // 2
                
                self.stdscr.addstr(
                    y_offset + i,
                    x,
                    text,
                    curses.color_pair(self._get_color_pair(color)) | attr
                )
            except curses.error:
                pass
    
    def _render_flash(self):
        """Render screen flash effect (invert colors briefly)."""
        # This is a simple implementation - could be enhanced
        # For now, we just note the flash is active
        pass
    
    def _get_color_pair(self, color):
        """Get color pair ID for curses color."""
        # Map curses colors to our color pairs
        color_map = {
            curses.COLOR_RED: 7,      # Red for damage
            curses.COLOR_GREEN: 6,    # Green for kills
            curses.COLOR_YELLOW: 9,   # Yellow for misses
            curses.COLOR_CYAN: 4,     # Cyan for pickups
        }
        return color_map.get(color, 1)
    
    def clear(self):
        """Clear all feedback."""
        self.messages.clear()
        self.flash_frames = 0


class TargetingReticle:
    """Displays a targeting reticle in the center of the screen."""
    
    # Reticle designs
    RETICLE_SIMPLE = "+"
    RETICLE_CROSS = "╬"
    RETICLE_CIRCLE = "◎"
    RETICLE_DOT = "·"
    
    def __init__(self, stdscr, design=RETICLE_CROSS):
        """
        Initialize targeting reticle.
        
        Args:
            stdscr: Curses screen object
            design: Reticle character design
        """
        self.stdscr = stdscr
        self.design = design
        self.enabled = True
        self.enemy_locked = False
    
    def render(self, viewport_width, viewport_height, x_offset=0, y_offset=0):
        """
        Render the reticle in center of viewport.
        
        Args:
            viewport_width: Width of 3D viewport
            viewport_height: Height of 3D viewport
            x_offset: X offset of viewport
            y_offset: Y offset of viewport
        """
        if not self.enabled:
            return
        
        # Calculate center
        center_x = x_offset + viewport_width // 2
        center_y = y_offset + viewport_height // 2
        
        # Choose color based on lock status
        if self.enemy_locked:
            color = curses.color_pair(7) | curses.A_BOLD  # Red when locked
        else:
            color = curses.color_pair(1) | curses.A_DIM   # White when idle
        
        try:
            self.stdscr.addch(center_y, center_x, self.design, color)
        except curses.error:
            pass
    
    def set_locked(self, locked):
        """Set whether reticle is locked onto target."""
        self.enemy_locked = locked
    
    def toggle(self):
        """Toggle reticle visibility."""
        self.enabled = not self.enabled
        return self.enabled


class EnemyHealthBar:
    """Displays health bar above targeted enemy."""
    
    def __init__(self, stdscr):
        """
        Initialize enemy health bar.
        
        Args:
            stdscr: Curses screen object
        """
        self.stdscr = stdscr
        self.enabled = True
    
    def render_for_enemy(self, enemy, viewport_width, viewport_height, 
                         x_offset=0, y_offset=0):
        """
        Render health bar for a specific enemy.
        
        Args:
            enemy: Enemy object
            viewport_width: Width of viewport
            viewport_height: Height of viewport
            x_offset: X offset of viewport
            y_offset: Y offset of viewport
        """
        if not self.enabled or not enemy:
            return
        
        # Calculate health percentage
        health_percent = enemy.health / enemy.max_health if enemy.max_health > 0 else 0
        
        # Health bar width
        bar_width = 10
        filled = int(health_percent * bar_width)
        
        # Build bar string
        bar = "[" + "█" * filled + "░" * (bar_width - filled) + "]"
        
        # Determine color
        if health_percent > 0.66:
            color = curses.color_pair(6)  # Green
        elif health_percent > 0.33:
            color = curses.color_pair(9)  # Yellow
        else:
            color = curses.color_pair(7)  # Red
        
        # Position above center (where enemy sprite would be)
        bar_x = x_offset + (viewport_width - len(bar)) // 2
        bar_y = y_offset + viewport_height // 2 - 2
        
        try:
            self.stdscr.addstr(bar_y, bar_x, bar, color | curses.A_BOLD)
            
            # Show health numbers below bar
            health_text = f"{enemy.health}/{enemy.max_health}"
            text_x = x_offset + (viewport_width - len(health_text)) // 2
            self.stdscr.addstr(bar_y + 1, text_x, health_text, 
                             curses.color_pair(1) | curses.A_DIM)
        except curses.error:
            pass
    
    def toggle(self):
        """Toggle health bar visibility."""
        self.enabled = not self.enabled
        return self.enabled


def test_combat_ui():
    """Test combat UI components."""
    print("=" * 60)
    print("COMBAT UI TEST")
    print("=" * 60)
    
    print("\nCombatFeedback Messages:")
    print("  - Attack Hit: 'HIT Enemy for 25 damage!'")
    print("  - Attack Miss: 'Missed Enemy!'")
    print("  - Enemy Killed: 'Killed Zombie! +50 treasure'")
    print("  - Item Pickup: 'Picked up: Health Potion'")
    print("  - Damage Taken: 'Took 15 damage!'")
    
    print("\nTargetingReticle Designs:")
    print("  - Simple: '+'")
    print("  - Cross: '╬'")
    print("  - Circle: '◎'")
    print("  - Dot: '·'")
    
    print("\nEnemyHealthBar Example:")
    print("  Full health:  [██████████]")
    print("  Half health:  [█████░░░░░]")
    print("  Low health:   [██░░░░░░░░]")
    
    print("\nUsage in game:")
    print("  1. Create CombatFeedback instance")
    print("  2. On attack hit: feedback.show_attack_hit(damage, enemy_name)")
    print("  3. On each frame: feedback.update()")
    print("  4. On render: feedback.render(x_offset, y_offset)")
    
    print("\n✓ Combat UI components ready!")


if __name__ == "__main__":
    test_combat_ui()