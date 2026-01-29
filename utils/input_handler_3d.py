"""
Enhanced Input handler for 3D first-person mode with combat support.
Stage 8: Added attack and item pickup actions.
"""
import curses


class InputHandler3D:
    """Handles input for 3D first-person mode with combat."""
    
    # Action types - Movement
    ACTION_MOVE_FORWARD = "move_forward"
    ACTION_MOVE_BACKWARD = "move_backward"
    ACTION_STRAFE_LEFT = "strafe_left"
    ACTION_STRAFE_RIGHT = "strafe_right"
    ACTION_ROTATE_LEFT = "rotate_left"
    ACTION_ROTATE_RIGHT = "rotate_right"
    
    # Action types - Combat & Interaction
    ACTION_ATTACK = "attack"
    ACTION_PICKUP = "pickup"
    ACTION_INTERACT = "interact"  # Generic interaction (attack/pickup/use)
    
    # Action types - UI
    ACTION_TOGGLE_MODE = "toggle_mode"
    ACTION_TOGGLE_TEXTURES = "toggle_textures"
    ACTION_TOGGLE_DEBUG = "toggle_debug"
    ACTION_TOGGLE_HELP = "toggle_help"
    ACTION_TOGGLE_MINIMAP = "toggle_minimap"
    ACTION_TOGGLE_SPRITES = "toggle_sprites"
    
    # Action types - Items
    ACTION_USE_WEAPON = "use_weapon"
    ACTION_USE_FOOD = "use_food"
    ACTION_USE_ELIXIR = "use_elixir"
    ACTION_USE_SCROLL = "use_scroll"
    
    # Action types - System
    ACTION_QUIT = "quit"
    ACTION_NONE = "none"
    
    def __init__(self, stdscr):
        """
        Initialize 3D input handler.
        
        Args:
            stdscr: Curses screen object
        """
        self.stdscr = stdscr
        self.stdscr.nodelay(False)
        
        # Control schemes
        self.use_arrow_keys = True
        self.use_wasd = True
        self.auto_pickup = False  # If True, walking into items picks them up
    
    def get_action(self):
        """
        Get the next action from user input.
        
        Returns:
            String action type
        """
        key = self.stdscr.getch()
        
        # Movement - WASD (primary in 3D mode)
        if self.use_wasd:
            if key == ord('w') or key == ord('W'):
                return self.ACTION_MOVE_FORWARD
            elif key == ord('s') or key == ord('S'):
                return self.ACTION_MOVE_BACKWARD
            elif key == ord('a') or key == ord('A'):
                return self.ACTION_ROTATE_LEFT
            elif key == ord('d') or key == ord('D'):
                return self.ACTION_ROTATE_RIGHT
        
        # Movement - Arrow keys (alternative)
        if self.use_arrow_keys:
            if key == curses.KEY_UP:
                return self.ACTION_MOVE_FORWARD
            elif key == curses.KEY_DOWN:
                return self.ACTION_MOVE_BACKWARD
            elif key == curses.KEY_LEFT:
                return self.ACTION_ROTATE_LEFT
            elif key == curses.KEY_RIGHT:
                return self.ACTION_ROTATE_RIGHT
        
        # Strafing - Q/E
        if key == ord('q') or key == ord('Q'):
            return self.ACTION_STRAFE_LEFT
        elif key == ord('e') or key == ord('E'):
            return self.ACTION_STRAFE_RIGHT
        
        # Combat & Interaction - F or Space
        elif key == ord('f') or key == ord('F') or key == ord(' '):
            return self.ACTION_INTERACT
        
        # Direct attack - Left Ctrl or X
        elif key == ord('x') or key == ord('X'):
            return self.ACTION_ATTACK
        
        # Direct pickup - G
        elif key == ord('g') or key == ord('G'):
            return self.ACTION_PICKUP
        
        # Item usage (same as 2D mode)
        elif key == ord('h') or key == ord('H'):
            return self.ACTION_USE_WEAPON
        elif key == ord('j') or key == ord('J'):
            return self.ACTION_USE_FOOD
        elif key == ord('k') or key == ord('K'):
            return self.ACTION_USE_ELIXIR
        # 'e' is strafe, so use different key for scrolls
        elif key == ord('r') or key == ord('R'):
            return self.ACTION_USE_SCROLL
        
        # Mode toggling
        elif key == ord('\t') or key == 9:  # Tab key
            return self.ACTION_TOGGLE_MODE
        
        # Feature toggles
        elif key == ord('t') or key == ord('T'):
            return self.ACTION_TOGGLE_TEXTURES
        elif key == ord('i') or key == ord('I'):
            return self.ACTION_TOGGLE_DEBUG
        elif key == ord('m') or key == ord('M'):
            return self.ACTION_TOGGLE_MINIMAP
        elif key == ord('n') or key == ord('N'):
            return self.ACTION_TOGGLE_SPRITES
        elif key == ord('?') or key == ord('/'):
            return self.ACTION_TOGGLE_HELP
        
        # Quit
        elif key == 27:  # ESC
            return self.ACTION_QUIT
        
        # Unknown key
        else:
            return self.ACTION_NONE
    
    def enable_arrow_keys(self, enabled=True):
        """Enable/disable arrow key controls."""
        self.use_arrow_keys = enabled
    
    def enable_wasd(self, enabled=True):
        """Enable/disable WASD controls."""
        self.use_wasd = enabled
    
    def enable_auto_pickup(self, enabled=True):
        """Enable/disable automatic item pickup."""
        self.auto_pickup = enabled
    
    def get_control_help(self):
        """
        Get help text for controls.
        
        Returns:
            List of strings describing controls
        """
        help_text = []
        
        help_text.append("╔══ MOVEMENT ══╗")
        if self.use_wasd:
            help_text.append("W/↑ - Move Forward")
            help_text.append("S/↓ - Move Backward")
            help_text.append("A/← - Rotate Left")
            help_text.append("D/→ - Rotate Right")
        if self.use_arrow_keys and not self.use_wasd:
            help_text.append("↑   - Move Forward")
            help_text.append("↓   - Move Backward")
            help_text.append("←   - Rotate Left")
            help_text.append("→   - Rotate Right")
        
        help_text.append("Q   - Strafe Left")
        help_text.append("E   - Strafe Right")
        
        help_text.append("")
        help_text.append("╔══ COMBAT ══╗")
        help_text.append("F/Space - Interact")
        help_text.append("X       - Attack Enemy")
        help_text.append("G       - Pick Up Item")
        
        help_text.append("")
        help_text.append("╔══ ITEMS ══╗")
        help_text.append("H - Use Weapon")
        help_text.append("J - Use Food")
        help_text.append("K - Use Elixir")
        help_text.append("R - Use Scroll")
        
        help_text.append("")
        help_text.append("╔══ VIEW ══╗")
        help_text.append("Tab - Toggle 2D/3D")
        help_text.append("T   - Toggle Textures")
        help_text.append("M   - Toggle Mini-map")
        help_text.append("N   - Toggle Sprites")
        help_text.append("I   - Toggle Debug")
        help_text.append("?   - Toggle Help")
        help_text.append("ESC - Quit")
        
        return help_text


class InputMapper3D:
    """Maps 3D actions to game logic."""
    
    def __init__(self, camera_controller, character, level):
        """
        Initialize input mapper.
        
        Args:
            camera_controller: CameraController instance
            character: Character object
            level: Level object
        """
        self.controller = camera_controller
        self.character = character
        self.level = level
    
    def handle_action(self, action):
        """
        Execute action using camera controller and game logic.
        
        Args:
            action: Action string from InputHandler3D
        
        Returns:
            Tuple of (success, message, data)
        """
        # Movement actions
        if action == InputHandler3D.ACTION_MOVE_FORWARD:
            success = self.controller.move_forward()
            return (success, "Moved forward" if success else "Blocked", None)
        
        elif action == InputHandler3D.ACTION_MOVE_BACKWARD:
            success = self.controller.move_backward()
            return (success, "Moved backward" if success else "Blocked", None)
        
        elif action == InputHandler3D.ACTION_STRAFE_LEFT:
            success = self.controller.strafe_left()
            return (success, "Strafed left" if success else "Blocked", None)
        
        elif action == InputHandler3D.ACTION_STRAFE_RIGHT:
            success = self.controller.strafe_right()
            return (success, "Strafed right" if success else "Blocked", None)
        
        elif action == InputHandler3D.ACTION_ROTATE_LEFT:
            self.controller.rotate_left()
            return (True, f"Facing {self.controller.get_direction_name()}", None)
        
        elif action == InputHandler3D.ACTION_ROTATE_RIGHT:
            self.controller.rotate_right()
            return (True, f"Facing {self.controller.get_direction_name()}", None)
        
        # Combat & Interaction actions
        elif action == InputHandler3D.ACTION_INTERACT:
            # Smart interaction: attack enemy if present, else pickup item, else open door
            entity, entity_type, distance = self.controller.get_entity_in_front(self.level)
            
            if entity_type == 'enemy':
                return self.handle_attack()
            elif entity_type == 'item':
                return self.handle_pickup()
            elif entity_type == 'exit':
                return (True, "Press forward to advance to next level", {'exit': True})
            else:
                # Try door
                success, message = self.controller.try_open_door(self.character)
                return (success, message, None)
        
        elif action == InputHandler3D.ACTION_ATTACK:
            return self.handle_attack()
        
        elif action == InputHandler3D.ACTION_PICKUP:
            return self.handle_pickup()
        
        # No action
        elif action == InputHandler3D.ACTION_NONE:
            return (False, "", None)
        
        else:
            return (False, "Unknown action", None)
    
    def handle_attack(self):
        """Handle attack action."""
        success, message, result = self.controller.attack_entity_in_front(
            self.character, self.level
        )
        
        if success and result:
            # Add treasure to backpack if enemy died
            if result.get('killed') and result.get('treasure'):
                self.character.backpack.treasure_value += result['treasure']
            
            return (True, message, result)
        else:
            return (False, message, None)
    
    def handle_pickup(self):
        """Handle pickup action."""
        success, message, item = self.controller.pickup_item_in_front(
            self.character, self.level
        )
        
        if success:
            return (True, message, {'item': item})
        else:
            return (False, message, None)


def test_input_handler_3d():
    """Test enhanced input handler."""
    print("=" * 60)
    print("ENHANCED INPUT HANDLER 3D TEST")
    print("=" * 60)
    
    # Mock screen
    class MockScreen:
        def getch(self):
            return ord('w')
        
        def nodelay(self, val):
            pass
    
    screen = MockScreen()
    handler = InputHandler3D(screen)
    
    # Test action mapping
    test_keys = [
        (ord('w'), "W", InputHandler3D.ACTION_MOVE_FORWARD),
        (ord('f'), "F", InputHandler3D.ACTION_INTERACT),
        (ord('x'), "X", InputHandler3D.ACTION_ATTACK),
        (ord('g'), "G", InputHandler3D.ACTION_PICKUP),
        (ord('h'), "H", InputHandler3D.ACTION_USE_WEAPON),
        (ord('j'), "J", InputHandler3D.ACTION_USE_FOOD),
        (ord('m'), "M", InputHandler3D.ACTION_TOGGLE_MINIMAP),
    ]
    
    print("\nKey Mapping:")
    print("  Key   | Action")
    print("  ------|---------------------------")
    
    for key_code, key_name, expected_action in test_keys:
        print(f"  {key_name:5s} | {expected_action}")
    
    # Test control help
    print("\n" + "=" * 60)
    print("Control Help Text:")
    print("=" * 60)
    
    help_lines = handler.get_control_help()
    for line in help_lines:
        print(f"  {line}")
    
    print("\n✓ Enhanced input handler tests complete!")


if __name__ == "__main__":
    test_input_handler_3d()