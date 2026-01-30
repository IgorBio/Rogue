"""
Curses-based renderer for 2D game display.

This module handles all 2D rendering operations including:
- Room and corridor visualization
- Character, enemy, and item rendering
- Fog of war implementation
- UI panel display

The renderer provides both full-visibility and fog-of-war rendering modes,
adapting display based on player exploration progress.
"""
import curses
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
    COLOR_UI_HIGHLIGHT
)
from config.game_config import GameConfig, ItemType, EnemyType
from presentation.ui_components import MessageLog, render_status_panel, render_message_log


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