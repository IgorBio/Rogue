"""
2D rendering and UI components for roguelike.
"""
import curses
from collections import deque
from config.game_config import GameConfig, ItemType, EnemyType
from presentation.colors import (
    init_colors,
    COLOR_WALL,
    COLOR_FLOOR,
    COLOR_CORRIDOR,
    COLOR_PLAYER,
    COLOR_EXIT,
    get_enemy_color,
    get_item_color,
    get_key_door_color,
    COLOR_UI_TEXT,
    COLOR_UI_HIGHLIGHT,
)

class Renderer:
    """
    Curses-based renderer for displaying the game in 2D.
    
    Manages the terminal display, color initialization, and provides
    methods for rendering the complete game state including map,
    entities, and user interface.
    
    Attributes:
        stdscr: Curses standard screen object
        map_height (int): Height of game map
        map_width (int): Width of game map
        message_log (MessageLog): Scrolling message display
    """
    
    def __init__(self, stdscr):
        """
        Initialize the renderer.
        
        Args:
            stdscr: Curses standard screen object
        """
        self.stdscr = stdscr
        self.map_height = GameConfig.MAP_HEIGHT
        self.map_width = GameConfig.MAP_WIDTH
        self.message_log = MessageLog(max_messages=5)
        
        # Configure curses for game display
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        curses.raw()
        self.stdscr.keypad(True)
        self.stdscr.nodelay(False)
        
        # Initialize color system
        if curses.has_colors():
            curses.start_color()
            init_colors()
        
        self.stdscr.clear()
        self.stdscr.refresh()
    
    def cleanup(self):
        """Restore terminal to normal state."""
        curses.noraw()
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()
    
    def render_level(self, level, character, fog_of_war=None, game_stats=None):
        """
        Render the complete game state.
        
        Displays the level map, entities, character, and UI based on
        fog of war settings and game statistics.
        
        Args:
            level: Level object to render
            character: Player character object
            fog_of_war (FogOfWar): Optional fog of war system
            game_stats: Optional statistics object for UI display
        """
        self.stdscr.clear()
        
        if fog_of_war is None:
            self._render_without_fog(level, character)
        else:
            self._render_with_fog(level, character, fog_of_war)
        
        self._render_character(character)
        
        if game_stats:
            render_status_panel(self.stdscr, character, level, game_stats, y_offset=self.map_height)
            render_message_log(self.stdscr, self.message_log, y_offset=self.map_height + 5, max_messages=3)
        else:
            self._render_ui(character, level)
        
        self.stdscr.refresh()
    
    def _render_without_fog(self, level, character):
        """
        Render everything without fog of war.
        
        Shows all rooms, corridors, items, and enemies regardless
        of player position. Used for debugging or test mode.
        
        Args:
            level: Level object
            character: Character object (unused but kept for consistency)
        """
        for room in level.rooms:
            self._render_room(room, show_contents=True)
        
        for corridor in level.corridors:
            self._render_corridor(corridor)
        
        if level.exit_position:
            self._render_exit(level.exit_position)
        
        for room in level.rooms:
            for item in room.items:
                if item.position:
                    self._render_item(item)
        
        for room in level.rooms:
            for enemy in room.enemies:
                self._render_enemy(enemy)
        
        for door in level.doors:
            self._render_door(door)
    
    def _render_with_fog(self, level, character, fog_of_war):
        """
        Render with fog of war enabled.
        
        Only shows discovered areas and currently visible entities.
        Adapts rendering based on whether player is in a room or corridor.
        
        Args:
            level: Level object
            character: Character object
            fog_of_war: FogOfWar object with visibility state
        """
        in_corridor = fog_of_war.get_current_corridor() is not None
        
        if in_corridor:
            self._render_corridor_line_of_sight(level, character, fog_of_war)
        else:
            self._render_room_based_fog(level, character, fog_of_war)
    
    def _render_room_based_fog(self, level, character, fog_of_war):
        """
        Render with room-based fog of war (player in room).
        
        Shows all discovered room walls, current room contents, and
        entities visible from current position.
        
        Args:
            level: Level object
            character: Character object
            fog_of_war: FogOfWar object
        """
        # First pass: render all discovered room walls
        for room_idx, room in enumerate(level.rooms):
            if fog_of_war.should_render_room_walls(room_idx):
                self._render_room_walls(room)
        
        # Second pass: render discovered corridors
        for corridor_idx, corridor in enumerate(level.corridors):
            if fog_of_war.should_render_corridor(corridor_idx):
                self._render_corridor(corridor)
        
        # Third pass: render floor ONLY for current room
        if fog_of_war.current_room_index is not None:
            current_room = level.rooms[fog_of_war.current_room_index]
            self._render_room_floor(current_room)
            
            # Render exit if in current room
            if fog_of_war.current_room_index == level.exit_room_index and level.exit_position:
                ex, ey = level.exit_position
                if fog_of_war.is_position_visible(ex, ey):
                    self._render_exit(level.exit_position)
        
        # Render items with individual visibility checks
        for room in level.rooms:
            for item in room.items:
                if item.position:
                    ix, iy = item.position
                    if fog_of_war.is_position_visible(ix, iy):
                        self._render_item(item)
        
        # Render enemies with individual visibility checks
        for room in level.rooms:
            for enemy in room.enemies:
                if enemy.is_alive():
                    ex, ey = enemy.position
                    if fog_of_war.is_position_visible(ex, ey):
                        self._render_enemy(enemy)
        
        # Render doors near current room
        if fog_of_war.current_room_index is not None:
            current_room = level.rooms[fog_of_war.current_room_index]
            for door in level.doors:
                if self._is_door_near_room(door, current_room):
                    self._render_door(door)
    
    def _render_corridor_line_of_sight(self, level, character, fog_of_war):
        """
        Render with line-of-sight in corridors.
        
        Uses ray casting to determine visible tiles when player
        is in a corridor, providing limited visibility.
        
        Args:
            level: Level object
            character: Character object
            fog_of_war: FogOfWar object
        """
        # First pass: render discovered room walls
        for room_idx, room in enumerate(level.rooms):
            if fog_of_war.should_render_room_walls(room_idx):
                self._render_room_walls(room)
        
        # Second pass: render discovered corridors
        for corridor_idx, corridor in enumerate(level.corridors):
            if fog_of_war.should_render_corridor(corridor_idx):
                self._render_corridor(corridor)
        
        # Third pass: render visible floor tiles in rooms
        for x, y in fog_of_war.visible_tiles:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                for room_idx, room in enumerate(level.rooms):
                    if room.contains_point(x, y):
                        self._draw_char(y, x, '.', COLOR_FLOOR)
                        break
        
        # Fourth pass: render doors in visible tiles
        for door in level.doors:
            if door.position in fog_of_war.visible_tiles:
                self._render_door(door)
        
        # Fifth pass: render exit if visible
        if level.exit_position:
            ex, ey = level.exit_position
            if fog_of_war.is_position_visible(ex, ey):
                self._render_exit(level.exit_position)
        
        # Render items with individual visibility checks
        for room in level.rooms:
            for item in room.items:
                if item.position:
                    ix, iy = item.position
                    if fog_of_war.is_position_visible(ix, iy):
                        self._render_item(item)
        
        # Render enemies with individual visibility checks
        for room in level.rooms:
            for enemy in room.enemies:
                if enemy.is_alive():
                    ex, ey = enemy.position
                    if fog_of_war.is_position_visible(ex, ey):
                        self._render_enemy(enemy)
    
    def _render_room(self, room, show_contents=True):
        """
        Render a single room with walls and optionally floor/contents.
        
        Args:
            room: Room object
            show_contents (bool): Whether to show floor tiles
        """
        self._render_room_walls(room)
        
        if show_contents:
            self._render_room_floor(room)
    
    def _render_room_walls(self, room):
        """
        Render only the walls of a room.
        
        Args:
            room: Room object
        """
        for x in range(room.x, room.x + room.width):
            if 0 <= x < self.map_width:
                if 0 <= room.y < self.map_height:
                    self._draw_char(room.y, x, '#', COLOR_WALL)
                if 0 <= room.y + room.height - 1 < self.map_height:
                    self._draw_char(room.y + room.height - 1, x, '#', COLOR_WALL)
        
        for y in range(room.y, room.y + room.height):
            if 0 <= y < self.map_height:
                if 0 <= room.x < self.map_width:
                    self._draw_char(y, room.x, '#', COLOR_WALL)
                if 0 <= room.x + room.width - 1 < self.map_width:
                    self._draw_char(y, room.x + room.width - 1, '#', COLOR_WALL)
    
    def _render_room_floor(self, room):
        """
        Render only the floor of a room.
        
        Args:
            room: Room object
        """
        for y in range(room.y + 1, room.y + room.height - 1):
            for x in range(room.x + 1, room.x + room.width - 1):
                if 0 <= x < self.map_width and 0 <= y < self.map_height:
                    self._draw_char(y, x, '.', COLOR_FLOOR)
    
    def _render_corridor(self, corridor):
        """
        Render a corridor.
        
        Args:
            corridor: Corridor object
        """
        for x, y in corridor.tiles:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                self._draw_char(y, x, '+', COLOR_CORRIDOR)
    
    def _render_exit(self, exit_position):
        """
        Render the exit marker.
        
        Args:
            exit_position (tuple): (x, y) coordinates
        """
        x, y = exit_position
        if 0 <= x < self.map_width and 0 <= y < self.map_height:
            self._draw_char(y, x, '>', COLOR_EXIT)
    
    def _render_item(self, item):
        """
        Render an item.
        
        Handles special rendering for keys with color-coded display.
        
        Args:
            item: Item object with position
        """
        if not item.position:
            return
        
        x, y = item.position
        if 0 <= x < self.map_width and 0 <= y < self.map_height:
            char = self._get_item_char(item)

            # Special handling for keys - use door color matching
            if item.item_type == ItemType.KEY:
                color = get_key_door_color(item.color)
            else:
                color = get_item_color(char)
            
            self._draw_char(y, x, char, color)
    
    def _render_enemy(self, enemy):
        """
        Render an enemy.
        
        Handles special rendering for mimics when disguised.
        
        Args:
            enemy: Enemy object
        """
        # Don't render if invisible (ghosts)
        if hasattr(enemy, 'is_invisible') and enemy.is_invisible:
            return
        
        x, y = enemy.position
        if 0 <= x < self.map_width and 0 <= y < self.map_height:
            # Check if this is a disguised mimic
            if (enemy.enemy_type == EnemyType.MIMIC and 
                hasattr(enemy, 'is_disguised') and 
                enemy.is_disguised):
                # Render as the disguise item
                disguise_char = getattr(enemy, 'disguise_char', '%')
                color = get_item_color(disguise_char)
                self._draw_char(y, x, disguise_char, color)
            else:
                # Render as normal enemy
                color = get_enemy_color(enemy.char)
                self._draw_char(y, x, enemy.char, color)
    
    def _render_character(self, character):
        """
        Render the player character.
        
        Args:
            character: Character object
        """
        x, y = character.position
        if 0 <= x < self.map_width and 0 <= y < self.map_height:
            self._draw_char(y, x, '@', COLOR_PLAYER)
    
    def _render_door(self, door):
        """
        Render a door with appropriate color.
        
        Args:
            door: Door object with color and lock state
        """
        x, y = door.position
        if 0 <= x < self.map_width and 0 <= y < self.map_height:
            char = '+' if door.is_locked else '/'
            color = get_key_door_color(door.color)
            self._draw_char(y, x, char, color)
    
    def _is_door_near_room(self, door, room):
        """
        Check if a door is adjacent to a room.
        
        Args:
            door: Door object
            room: Room object
        
        Returns:
            bool: True if door is near room
        """
        dx, dy = door.position
        
        for x in range(room.x - 2, room.x + room.width + 2):
            for y in range(room.y - 2, room.y + room.height + 2):
                if (x, y) == door.position:
                    return True
        return False

    
    def _render_ui(self, character, level):
        """
        Render the UI elements (stats, etc.).
        
        Simple fallback version when detailed stats are not available.
        
        Args:
            character: Character object
            level: Level object
        """
        ui_y = self.map_height
        
        health_str = f"HP: {character.health}/{character.max_health}"
        self._draw_string(ui_y, 0, health_str, COLOR_UI_TEXT)
        
        stats_str = f"STR: {character.strength} DEX: {character.dexterity}"
        self._draw_string(ui_y, 20, stats_str, COLOR_UI_TEXT)
        
        weapon_name = character.current_weapon.name if character.current_weapon else "None"
        weapon_str = f"Weapon: {weapon_name}"
        self._draw_string(ui_y, 40, weapon_str, COLOR_UI_TEXT)
        
        treasure_str = f"Treasure: {character.backpack.treasure_value}"
        self._draw_string(ui_y, 60, treasure_str, COLOR_UI_HIGHLIGHT)
        
        level_str = f"Level: {level.level_number}"
        self._draw_string(ui_y + 1, 0, level_str, COLOR_UI_TEXT)
        
        if character.active_elixirs:
            elixir_count = len(character.active_elixirs)
            min_turns = min(e['remaining_turns'] for e in character.active_elixirs)
            elixir_str = f"Buffs: {elixir_count} active ({min_turns}t)"
            self._draw_string(ui_y + 1, 20, elixir_str, COLOR_UI_HIGHLIGHT)
        
        food_count = character.backpack.get_item_count(ItemType.FOOD)
        weapon_count = character.backpack.get_item_count(ItemType.WEAPON)
        elixir_count = character.backpack.get_item_count(ItemType.ELIXIR)
        scroll_count = character.backpack.get_item_count(ItemType.SCROLL)
        key_count = character.backpack.get_item_count(ItemType.KEY)
        
        inv_str = f"Items: F:{food_count} W:{weapon_count} E:{elixir_count} S:{scroll_count} K:{key_count}"
        self._draw_string(ui_y + 1, 45, inv_str, COLOR_UI_TEXT)
    
    def _get_item_char(self, item):
        """
        Get the character representation for an item.
        
        Args:
            item: Item object
        
        Returns:
            str: Single character to display
        """
        item_chars = {
            ItemType.FOOD: '%',
            ItemType.TREASURE: '$',
            ItemType.WEAPON: '(',
            ItemType.ELIXIR: '!',
            ItemType.SCROLL: '?',
            ItemType.KEY: 'k'
        }
        return item_chars.get(item.item_type, '?')
    
    def _draw_char(self, y, x, char, color_pair):
        """
        Safely draw a character at the given position.
        
        Args:
            y (int): Row coordinate
            x (int): Column coordinate
            char (str): Character to draw
            color_pair (int): Color pair ID
        """
        try:
            self.stdscr.addch(y, x, char, curses.color_pair(color_pair))
        except curses.error:
            pass
    
    def _draw_string(self, y, x, string, color_pair):
        """
        Safely draw a string at the given position.
        
        Args:
            y (int): Row coordinate
            x (int): Column coordinate
            string (str): String to draw
            color_pair (int): Color pair ID
        """
        try:
            self.stdscr.addstr(y, x, string, curses.color_pair(color_pair))
        except curses.error:
            pass
    
    def display_message(self, message, y=None):
        """
        Display a message and add it to the message log.
        
        Args:
            message (str): Message to display
            y (int): Optional y coordinate (unused, kept for compatibility)
        """
        if message:
            self.message_log.add_message(message)
    
    def wait_for_key(self):
        """Wait for any key press."""
        self.stdscr.getch()

# === UI components (merged) ===
# UI configuration constants
MAX_MESSAGE_LOG_ENTRIES = 5
MAX_STATUS_MESSAGES = 3
ITEM_SELECTION_MENU_WIDTH = 60
ITEM_SELECTION_MENU_HEIGHT = 20


class MessageLog:
    """
    Manages a scrolling message log for game events.
    
    Stores recent messages in a fixed-size buffer and provides
    access to retrieve them for display.
    
    Attributes:
        messages (deque): Fixed-size deque of message strings
        max_messages (int): Maximum number of messages to store
    """
    
    def __init__(self, max_messages=MAX_MESSAGE_LOG_ENTRIES):
        """
        Initialize message log.
        
        Args:
            max_messages (int): Maximum messages to retain
        """
        self.messages = deque(maxlen=max_messages)
        self.max_messages = max_messages
    
    def add_message(self, message):
        """
        Add a new message to the log.
        
        Args:
            message (str): Message to add
        """
        if message:
            self.messages.append(message)
    
    def get_messages(self):
        """
        Get all messages in the log.
        
        Returns:
            list: All stored messages
        """
        return list(self.messages)
    
    def clear(self):
        """Clear all messages."""
        self.messages.clear()


def show_main_menu(stdscr, save_manager):
    """
    Display main menu with game options.
    
    Shows options for new game, continue, statistics, test mode, and quit.
    
    Args:
        stdscr: Curses screen object
        save_manager: SaveManager instance for checking save availability
    
    Returns:
        str: Selected option ('new', 'continue', 'stats', 'test', 'quit')
    """
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    title = "ROGUELIKE DUNGEON"
    subtitle = "A Classic Adventure"
    title_y = max_y // 2 - 6
    
    try:
        stdscr.addstr(title_y, (max_x - len(title)) // 2, title, curses.A_BOLD)
        stdscr.addstr(title_y + 1, (max_x - len(subtitle)) // 2, subtitle)
    except:
        pass
    
    menu_y = title_y + 4
    has_save = save_manager.save_exists()
    
    options = [
        "1. New Game",
        "2. Continue" if has_save else "2. Continue (No save found)",
        "3. View Statistics",
        "4. Test Mode",
        "Q. Quit"
    ]
    
    for i, option in enumerate(options):
        try:
            x = (max_x - len(option)) // 2
            if i == 1 and not has_save:
                stdscr.addstr(menu_y + i, x, option, curses.A_DIM)
            else:
                stdscr.addstr(menu_y + i, x, option)
        except:
            pass
    
    instruction = "Press the corresponding key to select"
    try:
        stdscr.addstr(menu_y + len(options) + 2, (max_x - len(instruction)) // 2, instruction, curses.A_DIM)
    except:
        pass
    
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        if key == ord('1'):
            return 'new'
        elif key == ord('2') and has_save:
            return 'continue'
        elif key == ord('3'):
            return 'stats'
        elif key == ord('4'):
            return 'test'
        elif key == ord('q') or key == ord('Q'):
            return 'quit'


def show_test_mode_menu(stdscr):
    """
    Display test mode configuration menu.
    
    Allows user to configure starting level and fog of war settings
    for testing purposes.
    
    Args:
        stdscr: Curses screen object
    
    Returns:
        dict: Configuration with 'level' and 'fog_of_war' keys, or None if cancelled
    """
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    title = "TEST MODE CONFIGURATION"
    subtitle = "Configure test parameters"
    title_y = max_y // 2 - 8
    
    try:
        stdscr.addstr(title_y, (max_x - len(title)) // 2, title, curses.A_BOLD | curses.A_REVERSE)
        stdscr.addstr(title_y + 1, (max_x - len(subtitle)) // 2, subtitle, curses.A_DIM)
    except:
        pass
    
    config_y = title_y + 4
    selected_level = 1
    fog_of_war_enabled = False
    current_option = 0
    
    while True:
        # Clear option area
        for y in range(config_y, config_y + 10):
            try:
                stdscr.addstr(y, 0, " " * max_x)
            except:
                pass
        
        # Level selection
        level_text = f"Level: {selected_level}/21"
        level_x = (max_x - len(level_text)) // 2
        
        if current_option == 0:
            try:
                stdscr.addstr(config_y, level_x - 5, ">", curses.A_BOLD)
                stdscr.addstr(config_y, level_x, level_text, curses.A_REVERSE)
            except:
                pass
        else:
            try:
                stdscr.addstr(config_y, level_x, level_text)
            except:
                pass
        
        level_hint = "(Use LEFT/RIGHT arrows or -/+ to change)"
        try:
            stdscr.addstr(config_y + 1, (max_x - len(level_hint)) // 2, level_hint, curses.A_DIM)
        except:
            pass
        
        # Fog of war toggle
        fog_text = f"Fog of War: {'ENABLED' if fog_of_war_enabled else 'DISABLED'}"
        fog_x = (max_x - len(fog_text)) // 2
        
        if current_option == 1:
            try:
                stdscr.addstr(config_y + 3, fog_x - 5, ">", curses.A_BOLD)
                stdscr.addstr(config_y + 3, fog_x, fog_text, curses.A_REVERSE)
            except:
                pass
        else:
            try:
                stdscr.addstr(config_y + 3, fog_x, fog_text)
            except:
                pass
        
        fog_hint = "(Press SPACE to toggle)"
        try:
            stdscr.addstr(config_y + 4, (max_x - len(fog_hint)) // 2, fog_hint, curses.A_DIM)
        except:
            pass
        
        # Action buttons
        start_text = "[ START TEST ]"
        cancel_text = "[ CANCEL ]"
        button_y = config_y + 7
        
        if current_option == 2:
            try:
                stdscr.addstr(button_y, (max_x - len(start_text)) // 2 - 10, start_text, curses.A_REVERSE | curses.A_BOLD)
                stdscr.addstr(button_y, (max_x - len(cancel_text)) // 2 + 10, cancel_text)
            except:
                pass
        elif current_option == 3:
            try:
                stdscr.addstr(button_y, (max_x - len(start_text)) // 2 - 10, start_text)
                stdscr.addstr(button_y, (max_x - len(cancel_text)) // 2 + 10, cancel_text, curses.A_REVERSE | curses.A_BOLD)
            except:
                pass
        else:
            try:
                stdscr.addstr(button_y, (max_x - len(start_text)) // 2 - 10, start_text)
                stdscr.addstr(button_y, (max_x - len(cancel_text)) // 2 + 10, cancel_text)
            except:
                pass
        
        nav_hint = "Use UP/DOWN to navigate, ENTER to select"
        try:
            stdscr.addstr(button_y + 2, (max_x - len(nav_hint)) // 2, nav_hint, curses.A_DIM)
        except:
            pass
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            current_option = max(0, current_option - 1)
        elif key == curses.KEY_DOWN:
            current_option = min(3, current_option + 1)
        elif key == curses.KEY_LEFT or key == ord('-'):
            if current_option == 0:
                selected_level = max(1, selected_level - 1)
        elif key == curses.KEY_RIGHT or key == ord('+') or key == ord('='):
            if current_option == 0:
                selected_level = min(21, selected_level + 1)
        elif key == ord(' '):
            if current_option == 1:
                fog_of_war_enabled = not fog_of_war_enabled
        elif key == ord('\n') or key == curses.KEY_ENTER or key == 10 or key == 13:
            if current_option == 2:
                return {'level': selected_level, 'fog_of_war': fog_of_war_enabled}
            elif current_option == 3:
                return None
        elif key == 27 or key == ord('q') or key == ord('Q'):
            return None


def show_statistics_screen(stdscr, stats_manager):
    """
    Display statistics and leaderboard.
    
    Shows top 10 runs by treasure and aggregate statistics
    across all playthroughs.
    
    Args:
        stdscr: Curses screen object
        stats_manager: StatisticsManager instance
    """
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    title = "LEADERBOARD - Top 10 Runs"
    try:
        stdscr.addstr(2, (max_x - len(title)) // 2, title, curses.A_BOLD)
        stdscr.addstr(3, 0, "=" * max_x)
    except:
        pass
    
    top_runs = stats_manager.get_top_runs(10)
    
    if not top_runs:
        try:
            msg = "No runs recorded yet. Play the game to see your stats here!"
            stdscr.addstr(max_y // 2, (max_x - len(msg)) // 2, msg)
        except:
            pass
    else:
        header = f"{'#':<4} {'Treasure':<10} {'Level':<7} {'Enemies':<9} {'Victory':<8} {'Date':<19}"
        try:
            stdscr.addstr(5, 2, header, curses.A_BOLD)
            stdscr.addstr(6, 0, "-" * max_x)
        except:
            pass
        
        y = 7
        for i, run in enumerate(top_runs, 1):
            if y >= max_y - 11:
                break
            
            rank = f"{i}."
            treasure = f"{run.get('treasure_collected', 0)}"
            level = f"{run.get('level_reached', 1)}/21"
            enemies = f"{run.get('enemies_defeated', 0)}"
            victory = "YES" if run.get('victory', False) else "No"
            
            timestamp_raw = run.get('timestamp', 'Unknown')
            if timestamp_raw and timestamp_raw != 'Unknown':
                timestamp = str(timestamp_raw)[:19]
            else:
                timestamp = 'Unknown'
            
            line = f"{rank:<4} {treasure:<10} {level:<7} {enemies:<9} {victory:<8} {timestamp:<19}"
            
            try:
                if i == 1:
                    stdscr.addstr(y, 2, line, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, 2, line)
            except:
                pass
            
            y += 1
        
        totals = stats_manager.get_total_stats()
        if totals:
            try:
                stdscr.addstr(y + 1, 0, "=" * max_x)
                stdscr.addstr(y + 2, 2, "ALL-TIME STATISTICS", curses.A_BOLD)
                stdscr.addstr(y + 3, 2, f"Total Runs:           {totals['total_runs']}")
                stdscr.addstr(y + 4, 2, f"Victories:            {totals['total_victories']}")
                stdscr.addstr(y + 5, 2, f"Deaths:               {totals['total_deaths']}")
                stdscr.addstr(y + 6, 2, f"Total Enemies:        {totals['total_enemies_defeated']}")
                
                col2_x = max_x // 2
                stdscr.addstr(y + 3, col2_x, f"Total Treasure:       {totals['total_treasure']}")
                stdscr.addstr(y + 4, col2_x, f"Most Treasure:        {totals['most_treasure']}")
                stdscr.addstr(y + 5, col2_x, f"Deepest Level:        {totals['deepest_level']}/21")
                stdscr.addstr(y + 6, col2_x, f"Total Tiles Moved:    {totals['total_tiles_moved']}")
                
                win_rate = (totals['total_victories'] / totals['total_runs'] * 100) if totals['total_runs'] > 0 else 0
                stdscr.addstr(y + 7, 2, f"Win Rate:             {win_rate:.1f}%", curses.A_BOLD)
            except:
                pass
    
    try:
        stdscr.addstr(max_y - 2, 0, "=" * max_x)
        footer = "Press any key to return to main menu"
        stdscr.addstr(max_y - 1, (max_x - len(footer)) // 2, footer, curses.A_DIM)
    except:
        pass
    
    stdscr.refresh()
    stdscr.getch()


def render_status_panel(stdscr, character, level, stats, y_offset=24):
    """
    Render comprehensive status panel.
    
    Displays character stats, inventory counts, combat statistics,
    and active effects.
    
    Args:
        stdscr: Curses screen object
        character: Character object
        level: Level object
        stats: Statistics object
        y_offset (int): Starting Y position for panel
    """
    try:
        max_y, max_x = stdscr.getmaxyx()
        for y in range(y_offset, min(y_offset + 6, max_y)):
            stdscr.addstr(y, 0, " " * max_x)
        
        health_str = f"HP: {character.health}/{character.max_health}"
        health_percent = character.health / character.max_health if character.max_health > 0 else 0
        
        if health_percent > 0.5:
            health_color = COLOR_UI_TEXT
        elif health_percent > 0.25:
            health_color = COLOR_UI_HIGHLIGHT
        else:
            health_color = curses.color_pair(6)
        
        stdscr.addstr(y_offset, 0, health_str, curses.color_pair(health_color))
        
        stats_str = f"STR: {character.strength}  DEX: {character.dexterity}"
        stdscr.addstr(y_offset, 20, stats_str, curses.color_pair(COLOR_UI_TEXT))
        
        weapon_name = character.current_weapon.name if character.current_weapon else "Unarmed"
        weapon_str = f"Weapon: {weapon_name}"
        stdscr.addstr(y_offset, 45, weapon_str, curses.color_pair(COLOR_UI_TEXT))
        
        level_str = f"Level: {level.level_number}/21"
        stdscr.addstr(y_offset + 1, 0, level_str, curses.color_pair(COLOR_UI_TEXT))
        
        treasure_str = f"Treasure: {character.backpack.treasure_value}"
        stdscr.addstr(y_offset + 1, 20, treasure_str, curses.color_pair(COLOR_UI_HIGHLIGHT))
        
        if character.active_elixirs:
            elixir_strs = []
            for elixir in character.active_elixirs:
                stat = elixir['stat_type'].split('_')[-1][:3].upper()
                bonus = elixir['bonus']
                turns = elixir['remaining_turns']
                elixir_strs.append(f"{stat}+{bonus}({turns}t)")
            
            buffs_str = f"Buffs: {', '.join(elixir_strs)}"
            stdscr.addstr(y_offset + 1, 45, buffs_str[:35], curses.color_pair(COLOR_UI_HIGHLIGHT))
        
        food_count = character.backpack.get_item_count(ItemType.FOOD)
        weapon_count = character.backpack.get_item_count(ItemType.WEAPON)
        elixir_count = character.backpack.get_item_count(ItemType.ELIXIR)
        scroll_count = character.backpack.get_item_count(ItemType.SCROLL)
        
        inv_str = f"Inventory: [J]Food:{food_count}/9  [H]Weapon:{weapon_count}/9  [K]Elixir:{elixir_count}/9  [E]Scroll:{scroll_count}/9"
        stdscr.addstr(y_offset + 2, 0, inv_str[:max_x-1], curses.color_pair(COLOR_UI_TEXT))
        
        stats_line = f"Kills: {stats.enemies_defeated}  Attacks: {stats.attacks_made}  Hits Taken: {stats.hits_taken}  Damage: {stats.damage_dealt}/{stats.damage_received}"
        stdscr.addstr(y_offset + 3, 0, stats_line[:max_x-1], curses.color_pair(COLOR_UI_TEXT))
        
        items_line = f"Moved: {stats.tiles_moved} tiles  Items: {stats.items_collected} collected  Food: {stats.food_consumed} eaten"
        stdscr.addstr(y_offset + 4, 0, items_line[:max_x-1], curses.color_pair(COLOR_UI_TEXT))
        
    except curses.error:
        pass


def render_message_log(stdscr, message_log, y_offset=30, max_messages=MAX_STATUS_MESSAGES):
    """
    Render scrolling message log.
    
    Displays recent game messages in a fixed area.
    
    Args:
        stdscr: Curses screen object
        message_log: MessageLog instance
        y_offset (int): Starting Y position
        max_messages (int): Maximum messages to display
    """
    try:
        max_y, max_x = stdscr.getmaxyx()
        
        for i in range(max_messages):
            if y_offset + i < max_y:
                stdscr.addstr(y_offset + i, 0, " " * max_x)
        
        messages = message_log.get_messages()
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        for i, message in enumerate(recent_messages):
            if y_offset + i < max_y:
                display_msg = message[:max_x-1] if len(message) >= max_x else message
                stdscr.addstr(y_offset + i, 0, display_msg, curses.color_pair(COLOR_UI_HIGHLIGHT))
        
    except curses.error:
        pass


def show_item_selection(stdscr, items, title, allow_zero=False):
    """
    Show item selection menu.
    
    Displays a menu for selecting items from a list, with optional
    zero index for special actions (like unequipping).
    
    Args:
        stdscr: Curses screen object
        items (list): List of item objects
        title (str): Menu title
        allow_zero (bool): Whether to allow selecting option 0
    
    Returns:
        int: Selected index (0-9), -1 for option 0, or None if cancelled
    """
    if not items and not allow_zero:
        return None
    
    max_y, max_x = stdscr.getmaxyx()
    menu_height = min(len(items) + 6 + (1 if allow_zero else 0), ITEM_SELECTION_MENU_HEIGHT)
    menu_width = min(ITEM_SELECTION_MENU_WIDTH, max_x - 4)
    menu_y = (max_y - menu_height) // 2
    menu_x = (max_x - menu_width) // 2
    
    # Clear menu area
    for y in range(menu_y, menu_y + menu_height):
        if y < max_y:
            stdscr.addstr(y, menu_x, " " * menu_width)
    
    # Draw border
    try:
        stdscr.addstr(menu_y, menu_x, "â”Œ" + "â”€" * (menu_width - 2) + "â”")
        for y in range(menu_y + 1, menu_y + menu_height - 1):
            stdscr.addstr(y, menu_x, "â”‚")
            stdscr.addstr(y, menu_x + menu_width - 1, "â”‚")
        stdscr.addstr(menu_y + menu_height - 1, menu_x, "â””" + "â”€" * (menu_width - 2) + "â”˜")
    except:
        pass
    
    # Draw title
    try:
        title_x = menu_x + (menu_width - len(title)) // 2
        stdscr.addstr(menu_y + 1, title_x, title, curses.A_BOLD | curses.A_REVERSE)
    except:
        pass
    
    line = menu_y + 3
    
    if allow_zero:
        try:
            stdscr.addstr(line, menu_x + 2, "0. Empty hands (unequip)", curses.A_DIM)
        except:
            pass
        line += 1
    
    for i, item in enumerate(items, 1):
        if line >= menu_y + menu_height - 3:
            break
        
        desc = _get_item_description(item)
        display_text = f"{i}. {desc}"
        
        if len(display_text) > menu_width - 4:
            display_text = display_text[:menu_width - 7] + "..."
        
        try:
            stdscr.addstr(line, menu_x + 2, display_text)
        except:
            pass
        line += 1
    
    # Draw footer
    try:
        footer_y = menu_y + menu_height - 2
        cancel_text = "Press number to select, ESC/Q to cancel"
        footer_x = menu_x + (menu_width - len(cancel_text)) // 2
        stdscr.addstr(footer_y, footer_x, cancel_text, curses.A_DIM)
    except:
        pass
    
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        
        if key == 27 or key == ord('q') or key == ord('Q'):
            return None
        
        if ord('0') <= key <= ord('9'):
            selection = key - ord('0')
            
            if selection == 0 and allow_zero:
                return -1
            elif selection == 0 and not allow_zero:
                continue
            elif 1 <= selection <= len(items):
                return selection - 1
            else:
                continue


def _get_item_description(item):
    """
    Get detailed item description.
    
    Args:
        item: Item object
    
    Returns:
        str: Human-readable item description
    """
    if item.item_type == ItemType.FOOD:
        return f"Food - Restores {item.health_restoration} HP"
    elif item.item_type == ItemType.WEAPON:
        return f"{item.name} - Damage +{item.strength_bonus}"
    elif item.item_type == ItemType.ELIXIR:
        stat_name = item.stat_type.replace('_', ' ').title()
        return f"Elixir of {stat_name} - +{item.bonus} for {item.duration} turns"
    elif item.item_type == ItemType.SCROLL:
        stat_name = item.stat_type.replace('_', ' ').title()
        return f"Scroll of {stat_name} - Permanent +{item.bonus}"
    else:
        return "Unknown Item"


def show_game_over_screen(stdscr, stats, victory=False):
    """
    Display game over screen with final statistics.
    
    Shows comprehensive run statistics and provides options
    to restart, return to menu, or quit.
    
    Args:
        stdscr: Curses screen object
        stats (dict): Statistics dictionary
        victory (bool): Whether player won
    
    Returns:
        str: Selected option ('restart', 'menu', 'quit')
    """
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    title_y = 2
    if victory:
        title = "â˜… â˜… â˜…  V I C T O R Y  â˜… â˜… â˜… "
        subtitle = "You have conquered all 21 levels!"
    else:
        title = "â˜  â˜  â˜     G A M E   O V E R  â˜  â˜  â˜    "
        subtitle = stats.get('death_reason', 'You have fallen in battle!')
    
    try:
        title_x = (max_x - len(title)) // 2
        subtitle_x = (max_x - len(subtitle)) // 2
        stdscr.addstr(title_y, title_x, title, curses.A_BOLD | curses.A_REVERSE)
        stdscr.addstr(title_y + 1, subtitle_x, subtitle, curses.A_DIM)
    except:
        pass
    
    stats_y = title_y + 4
    col1_x = max_x // 4
    col2_x = max_x // 2 + 5
    
    try:
        stdscr.addstr(stats_y, col1_x, "â•”â•â•¡ CHARACTER â•žâ•â•—", curses.A_BOLD)
        stdscr.addstr(stats_y + 2, col1_x, f"Level Reached:  {stats['level_reached']}/21")
        stdscr.addstr(stats_y + 3, col1_x, f"Final Health:   {stats['final_health']}/{stats['max_health']}")
        stdscr.addstr(stats_y + 4, col1_x, f"Strength:       {stats['strength']}")
        stdscr.addstr(stats_y + 5, col1_x, f"Dexterity:      {stats['dexterity']}")
        stdscr.addstr(stats_y + 6, col1_x, f"Treasure:       {stats['treasure_collected']}", curses.A_BOLD)
    except:
        pass
    
    try:
        stdscr.addstr(stats_y, col2_x, "â•”â•â•¡ COMBAT â•žâ•â•—", curses.A_BOLD)
        stdscr.addstr(stats_y + 2, col2_x, f"Enemies Killed:   {stats.get('enemies_defeated', 0)}")
        stdscr.addstr(stats_y + 3, col2_x, f"Attacks Made:     {stats.get('attacks_made', 0)}")
        stdscr.addstr(stats_y + 4, col2_x, f"Hits Taken:       {stats.get('hits_taken', 0)}")
        stdscr.addstr(stats_y + 5, col2_x, f"Damage Dealt:     {stats.get('damage_dealt', 0)}")
        stdscr.addstr(stats_y + 6, col2_x, f"Damage Received:  {stats.get('damage_received', 0)}")
    except:
        pass
    
    stats_y2 = stats_y + 9
    try:
        stdscr.addstr(stats_y2, col1_x, "â•”â•â•¡ ITEMS â•žâ•â•—", curses.A_BOLD)
        stdscr.addstr(stats_y2 + 2, col1_x, f"Items Collected: {stats.get('items_collected', 0)}")
        stdscr.addstr(stats_y2 + 3, col1_x, f"Food Consumed:   {stats.get('food_consumed', 0)}")
        stdscr.addstr(stats_y2 + 4, col1_x, f"Elixirs Used:    {stats.get('elixirs_used', 0)}")
        stdscr.addstr(stats_y2 + 5, col1_x, f"Scrolls Read:    {stats.get('scrolls_read', 0)}")
    except:
        pass
    
    try:
        stdscr.addstr(stats_y2, col2_x, "â•”â•â•¡ EXPLORATION â•žâ•â•—", curses.A_BOLD)
        stdscr.addstr(stats_y2 + 2, col2_x, f"Tiles Traversed:  {stats.get('tiles_moved', 0)}")
    except:
        pass
    
    rank_y = stats_y2 + 8
    if stats.get('rank'):
        rank_msg = f"â—† This run ranked #{stats['rank']} on the leaderboard! â—† "
        try:
            rank_x = (max_x - len(rank_msg)) // 2
            stdscr.addstr(rank_y, rank_x, rank_msg, curses.A_BOLD | curses.A_REVERSE)
        except:
            pass
    
    options_y = max_y - 4
    try:
        separator = "â•" * max_x
        stdscr.addstr(options_y - 1, 0, separator[:max_x])
        
        options = "[R] Restart  â”‚  [M] Main Menu  â”‚  [Q] Quit "
        options_x = (max_x - len(options)) // 2
        stdscr.addstr(options_y, options_x, options, curses.A_BOLD | curses.A_REVERSE)
    except:
        pass
    
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        
        if key == ord('r') or key == ord('R'):
            return 'restart'
        elif key == ord('m') or key == ord('M'):
            return 'menu'
        elif key == ord('q') or key == ord('Q'):
            return 'quit'
