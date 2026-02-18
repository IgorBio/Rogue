"""
Texture system for 3D wall rendering.

Provides 16x16 character-based textures with distance shading,
room/corridor variations, and special entrance textures.
"""


class WallTexture:
    """A 2D character pattern used as a wall texture."""

    def __init__(self, name, pattern, width=None, height=None):
        """
        Args:
            name: Identifier string.
            pattern: List of equal-length strings, or 2-D list of characters.
            width: Override detected width (optional).
            height: Override detected height (optional).
        """
        self.name = name

        if not pattern:
            self.pattern = [['█'] * 16 for _ in range(16)]
            self.width = 16
            self.height = 16
            return

        if isinstance(pattern[0], str):
            self.pattern = [list(row) for row in pattern]
        else:
            self.pattern = pattern

        self.height = height or len(self.pattern)
        self.width = width or (len(self.pattern[0]) if self.pattern else 0)

        if self.height <= 0 or self.width <= 0:
            self.pattern = [['█'] * 16 for _ in range(16)]
            self.width = 16
            self.height = 16
            return

        # Normalise all rows to the same length
        max_w = max(len(row) for row in self.pattern)
        for i, row in enumerate(self.pattern):
            if len(row) < max_w:
                self.pattern[i] = row + [' '] * (max_w - len(row))
        self.width = max_w

    def sample(self, texture_x: float, texture_y: float) -> str:
        """
        Return the character at normalised texture coordinates.

        Args:
            texture_x: Horizontal position in [0.0, 1.0].
            texture_y: Vertical position in [0.0, 1.0].

        Returns:
            Single character string.
        """
        texture_x = max(0.0, min(0.9999, texture_x))
        texture_y = max(0.0, min(0.9999, texture_y))

        tex_x = max(0, min(int(texture_x * self.width), self.width - 1))
        tex_y = max(0, min(int(texture_y * self.height), len(self.pattern) - 1))

        if not self.pattern:
            return '█'

        row = self.pattern[tex_y]
        if not row:
            return '█'

        return row[max(0, min(tex_x, len(row) - 1))]


class TextureManager:
    """Registry and factory for wall textures."""

    def __init__(self):
        self.textures: dict = {}
        self._build_textures()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_texture(self, name: str):
        """Return a WallTexture by name, or None."""
        return self.textures.get(name)

    def get_room_wall_texture(self, room_id: int):
        """Return a room-wall texture varied by room index (4 variants)."""
        return self.get_texture(f'room_wall_{room_id % 4}')

    def get_corridor_wall_texture(self, corridor_id: int):
        """Return a corridor-wall texture varied by corridor index (3 variants)."""
        return self.get_texture(f'corridor_wall_{corridor_id % 3}')

    def add_texture(self, texture: WallTexture) -> None:
        """Register a custom texture."""
        self.textures[texture.name] = texture

    def sample_texture(self, name: str, texture_x: float,
                       texture_y: float) -> str:
        """
        Sample a texture by name with a safe fallback.

        Returns '█' if the texture does not exist or sampling fails.
        """
        texture = self.get_texture(name)
        if texture:
            try:
                return texture.sample(texture_x, texture_y)
            except Exception:
                return '█'
        return '█'

    # ------------------------------------------------------------------
    # Texture definitions
    # ------------------------------------------------------------------

    def _build_textures(self) -> None:
        # ── Room wall variants ────────────────────────────────────────

        brick = [
            "████▓▓▓▓▒▒▒▒░░░░",
            "███▓▓▓▓▒▒▒▒░░░░ ",
            "▓▓▓▓▒▒▒▒░░░░    ",
            "▓▓▓▒▒▒▒░░░░  ░░░",
            "████▓▓▓▓▒▒▒▒░░░░",
            "███▓▓▓▓▒▒▒▒░░░░ ",
            "▓▓▓▓▒▒▒▒░░░░    ",
            "▓▓▓▒▒▒▒░░░░  ░░░",
            "████▓▓▓▓▒▒▒▒░░░░",
            "███▓▓▓▓▒▒▒▒░░░░ ",
            "▓▓▓▓▒▒▒▒░░░░    ",
            "▓▓▓▒▒▒▒░░░░  ░░░",
            "████▓▓▓▓▒▒▒▒░░░░",
            "███▓▓▓▓▒▒▒▒░░░░ ",
            "▓▓▓▓▒▒▒▒░░░░    ",
            "▓▓▓▒▒▒▒░░░░  ░░░",
        ]
        self.textures['room_wall'] = WallTexture('room_wall', brick)
        self.textures['room_wall_0'] = WallTexture('room_wall_0', brick)

        rough_stone = [
            "▓▓▓▓▓▓▒▒▒▒▒▒░░░░",
            "▓▓▓▓▒▒▒▒▒▒░░░░  ",
            "▓▓▒▒▒▒▒░░░░░    ",
            "▒▒▒▒▒░░░░░  ░░░░",
            "▓▓▓▓▓▒▒▒▒▒▒░░░░ ",
            "▓▓▓▒▒▒▒▒░░░░░   ",
            "▓▒▒▒▒▒░░░░   ░░░",
            "▒▒▒▒░░░░░  ░░░░░",
            "▓▓▓▓▓▒▒▒▒▒▒░░░░ ",
            "▓▓▓▒▒▒▒▒░░░░░   ",
            "▓▒▒▒▒▒░░░░   ░░░",
            "▒▒▒▒░░░░░  ░░░░░",
            "▓▓▓▓▒▒▒▒▒░░░░░  ",
            "▓▓▒▒▒▒░░░░░     ",
            "▒▒▒▒░░░░   ░░░░ ",
            "▒▒░░░░   ░░░░░░ ",
        ]
        self.textures['room_wall_1'] = WallTexture('room_wall_1', rough_stone)

        carved = [
            "║║║║║║║║║║║║║║║║",
            "════════════════",
            "║║║║║║║║║║║║║║║║",
            "║║░░░░░░░░░░║║║║",
            "║║░░░░░░░░░░║║║║",
            "════════════════",
            "║║║║║║║║║║║║║║║║",
            "║║░░░░░░░░░░║║║║",
            "║║░░░░░░░░░░║║║║",
            "════════════════",
            "║║║║║║║║║║║║║║║║",
            "║║░░░░░░░░░░║║║║",
            "║║░░░░░░░░░░║║║║",
            "════════════════",
            "║║║║║║║║║║║║║║║║",
            "║║║║║║║║║║║║║║║║",
        ]
        self.textures['room_wall_2'] = WallTexture('room_wall_2', carved)

        mossy = [
            "████▓▓▓▓▒▒▒▒░░░░",
            "██:▓▓::▒▒::░░:  ",
            "▓:▓▓▒:▒▒░:░░    ",
            "▓▓::▒▒::░░:  ░░:",
            "████▓▓▓▓▒▒▒▒░░░░",
            "██:▓▓::▒▒::░░:  ",
            "▓:▓▓▒:▒▒░:░░    ",
            "▓▓::▒▒::░░:  ░░:",
            "████▓▓▓▓▒▒▒▒░░░░",
            "██:▓▓::▒▒::░░:  ",
            "▓:▓▓▒:▒▒░:░░    ",
            "▓▓::▒▒::░░:  ░░:",
            "████▓▓▓▓▒▒▒▒░░░░",
            "██:▓▓::▒▒::░░:  ",
            "▓:▓▓▒:▒▒░:░░    ",
            "▓▓::▒▒::░░:  ░░:",
        ]
        self.textures['room_wall_3'] = WallTexture('room_wall_3', mossy)

        # ── Corridor wall variants ────────────────────────────────────

        corr0 = [
            "▓▓▓▓▓▓▓▒▒▒▒▒░░░░",
            "▓▓▓▓▓▒▒▒▒▒░░░░  ",
            "▓▓▓▒▒▒▒▒░░░░    ",
            "▓▒▒▒▒▒░░░░  ░░  ",
            "▒▒▒▒░░░░    ░░░ ",
            "▒▒░░░░  ░░  ░░░░",
            "░░░░    ░░░░░░░░",
            "░░  ░░  ░░░░░░░ ",
            "▓▓▓▓▓▓▒▒▒▒▒░░░░ ",
            "▓▓▓▓▒▒▒▒▒░░░░   ",
            "▓▓▒▒▒▒▒░░░░     ",
            "▒▒▒▒▒░░░░   ░░  ",
            "▒▒▒░░░░  ░  ░░░ ",
            "▒░░░░    ░░░░░░ ",
            "░░░  ░░  ░░░░░░░",
            "░  ░░░░░░░░░░░░ ",
        ]
        self.textures['corridor_wall'] = WallTexture('corridor_wall', corr0)
        self.textures['corridor_wall_0'] = WallTexture('corridor_wall_0', corr0)

        corr1 = [
            "▓▓▓▓▓▓▓▒▒▒▒▒░░░░",
            "▓▓~▓▓▒▒~▒▒░~░░  ",
            "▓~▓▒▒~▒░░~░     ",
            "~▒▒▒~░░░~  ░~   ",
            "▒▒~░░░~    ~░░  ",
            "▒~░░~  ░~  ~░░░ ",
            "~░░    ~░░~░░░░ ",
            "░  ~░  ~░░~░░░  ",
            "▓▓▓▓▓▒▒▒▒▒~░░░  ",
            "▓▓~▓▒▒~▒░░~░    ",
            "▓~▒▒~▒░~░       ",
            "~▒▒~░░~    ~    ",
            "▒~░░~    ~  ~░  ",
            "~░░  ~░  ~░~░░  ",
            "░    ~░~░~░░░░  ",
            "  ~░~░░~░░░░    ",
        ]
        self.textures['corridor_wall_1'] = WallTexture('corridor_wall_1', corr1)

        corr2 = [
            "▓▓▓▓/▓▓▒▒/▒▒░░\\░",
            "▓▓/▓▒▒/▒░░/░    ",
            "▓/▒▒/░░/        ",
            "/▒▒/░░/    \\    ",
            "▒/░░/    \\  \\   ",
            "/░░/  \\  \\  \\░  ",
            "░/    \\  \\░\\░░  ",
            "/  \\  \\░\\░\\░░   ",
            "▓▓▓▓/▓▒▒/▒░░/░  ",
            "▓▓/▒▒/░░/░      ",
            "▓/▒/░░/         ",
            "/▒/░░/    \\     ",
            "/░░/  \\    \\    ",
            "░/  \\  \\  \\  \\  ",
            "/    \\  \\  \\░\\  ",
            "  \\  \\  \\░\\░\\   ",
        ]
        self.textures['corridor_wall_2'] = WallTexture('corridor_wall_2', corr2)

        # ── Corner textures ───────────────────────────────────────────

        self.textures['corner_nw'] = WallTexture('corner_nw', [
            "████████████████",
            "████████████████",
            "████████▓▓▓▓▓▓▓▓",
            "████████▓▓▓▓▓▓▒▒",
            "██████▓▓▓▓▓▓▒▒▒▒",
            "██████▓▓▓▓▒▒▒▒▒░",
            "████▓▓▓▓▓▒▒▒▒░░░",
            "████▓▓▓▓▒▒▒▒░░░░",
            "██▓▓▓▓▓▒▒▒░░░░░ ",
            "██▓▓▓▓▒▒▒░░░░   ",
            "▓▓▓▓▓▒▒▒░░░░    ",
            "▓▓▓▓▒▒▒░░░░     ",
            "▓▓▓▒▒▒░░░       ",
            "▓▓▒▒▒░░░        ",
            "▓▒▒░░░          ",
            "▒▒░░            ",
        ])

        self.textures['corner_ne'] = WallTexture('corner_ne', [
            "████████████████",
            "████████████████",
            "▓▓▓▓▓▓▓▓████████",
            "▒▒▓▓▓▓▓▓████████",
            "▒▒▒▒▓▓▓▓▓▓██████",
            "░▒▒▒▒▒▓▓▓▓██████",
            "░░░▒▒▒▒▒▓▓▓▓████",
            "░░░░▒▒▒▒▓▓▓▓████",
            " ░░░░░▒▒▒▓▓▓▓██ ",
            "   ░░░░▒▒▒▓▓▓▓██",
            "    ░░░░▒▒▒▓▓▓▓▓",
            "     ░░░░▒▒▒▓▓▓▓",
            "       ░░░▒▒▒▓▓▓",
            "        ░░░▒▒▒▓▓",
            "          ░░░▒▒▓",
            "            ░░▒▒",
        ])

        self.textures['corner_sw'] = WallTexture('corner_sw', [
            "▒▒░░            ",
            "▓▒▒░░░          ",
            "▓▓▒▒▒░░░        ",
            "▓▓▓▒▒▒░░░       ",
            "▓▓▓▓▒▒▒░░░░     ",
            "▓▓▓▓▓▒▒▒░░░░    ",
            "██▓▓▓▓▒▒▒░░░░   ",
            "██▓▓▓▓▓▒▒▒░░░░░ ",
            "████▓▓▓▓▒▒▒▒░░░░",
            "████▓▓▓▓▓▒▒▒▒░░░",
            "██████▓▓▓▓▒▒▒▒▒░",
            "██████▓▓▓▓▓▓▒▒▒▒",
            "████████▓▓▓▓▓▓▒▒",
            "████████▓▓▓▓▓▓▓▓",
            "████████████████",
            "████████████████",
        ])

        self.textures['corner_se'] = WallTexture('corner_se', [
            "            ░░▒▒",
            "          ░░░▒▒▓",
            "        ░░░▒▒▒▓▓",
            "       ░░░▒▒▒▓▓▓",
            "     ░░░░▒▒▒▓▓▓▓",
            "    ░░░░▒▒▒▓▓▓▓▓",
            "   ░░░░▒▒▒▓▓▓▓██",
            " ░░░░░▒▒▒▓▓▓▓▓██",
            "░░░░▒▒▒▒▓▓▓▓████",
            "░░░▒▒▒▒▓▓▓▓▓████",
            "░▒▒▒▒▒▓▓▓▓██████",
            "▒▒▒▒▓▓▓▓▓▓██████",
            "▒▒▓▓▓▓▓▓████████",
            "▓▓▓▓▓▓▓▓████████",
            "████████████████",
            "████████████████",
        ])

        # ── Entrance textures ─────────────────────────────────────────

        # The real corridor opening: arrows point into the passage.
        self.textures['room_wall_entrance'] = WallTexture('room_wall_entrance', [
            "╔═══════════════╗",
            "║███████████████║",
            "║███         ███║",
            "║███         ███║",
            "║███    ↓    ███║",
            "║███         ███║",
            "║███         ███║",
            "║███         ███║",
            "║███    ↓    ███║",
            "║███         ███║",
            "║███         ███║",
            "║███         ███║",
            "║███    ↓    ███║",
            "║███████████████║",
            "╚═══════════════╝",
            "                ",
        ])

        # The lateral face of the entrance tile: solid pillar, no gap, no arrow.
        self.textures['room_wall_beside_entrance'] = WallTexture(
            'room_wall_beside_entrance', [
            "████████████████",
            "█░░░░░░░░░░░░░░█",
            "█░┌──────────┐░█",
            "█░│  ██████  │░█",
            "█░│  ██  ██  │░█",
            "█░│  ██  ██  │░█",
            "█░│  ██  ██  │░█",
            "█░│  ██  ██  │░█",
            "█░│  ██  ██  │░█",
            "█░│  ██  ██  │░█",
            "█░│  ██████  │░█",
            "█░│          │░█",
            "█░└──────────┘░█",
            "█░░░░░░░░░░░░░░█",
            "████████████████",
            "                ",
        ])

        # ── Door textures ─────────────────────────────────────────────

        door = [
            "╔═══════════════╗",
            "║███████████████║",
            "║███████████████║",
            "║███████████████║",
            "║████       ████║",
            "║████   ●   ████║",
            "║████       ████║",
            "║███████████████║",
            "║███████████████║",
            "║████       ████║",
            "║████   ●   ████║",
            "║████       ████║",
            "║███████████████║",
            "║███████████████║",
            "╚═══════════════╝",
            "                ",
        ]
        self.textures['door'] = WallTexture('door', door)
        self.textures['door_open'] = self.textures['door']

        locked_door = [
            "╔═══════════════╗",
            "║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║",
            "║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║",
            "║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║",
            "║▓▓▓▓       ▓▓▓▓║",
            "║▓▓▓▓   k   ▓▓▓▓║",
            "║▓▓▓▓       ▓▓▓▓║",
            "║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║",
            "║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║",
            "║▓▓▓▓       ▓▓▓▓║",
            "║▓▓▓▓   k   ▓▓▓▓║",
            "║▓▓▓▓       ▓▓▓▓║",
            "║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║",
            "║▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║",
            "╚═══════════════╝",
            "                ",
        ]
        self.textures['locked_door'] = WallTexture('locked_door', locked_door)
        self.textures['door_locked'] = self.textures['locked_door']


class TexturedRenderer:
    """Applies textures and distance-based shading to wall columns."""

    SHADE_CHARS = ['█', '▓', '▓', '▒', '▒', '▒', '░', '░', '░', '·', '·', ' ']
    SHADE_DISTANCES = [1.5, 2.5, 3.5, 5.0, 6.5, 8.0, 10.0, 12.0, 14.5, 17.0, 19.5, 22.0]

    _DIM_LEVELS = [
        {},  # level 0: no change
        {'█': '▓', '▓': '▒', '▒': '░', '░': '·',
         '║': '│', '═': '─', '╔': '┌', '╗': '┐', '╚': '└', '╝': '┘'},
        {'█': '▒', '▓': '░', '▒': '·', '░': ' ',
         '║': '│', '═': '─', '↓': '|', ':': ':'},
        {'█': '░', '▓': '·', '▒': '·', '░': ' ',
         '║': '|', '═': '-', '↓': '|', ':': '.'},
        {'█': '·', '▓': ' ', '▒': ' ', '░': ' ',
         '║': ' ', '═': ' ', '↓': '·', ':': ' '},
        {},  # level 5: everything -> ' '
    ]

    def __init__(self, texture_manager: TextureManager):
        self.texture_manager = texture_manager
        self._shade_cache: dict = {}

    def get_wall_char(self, wall_type: str, texture_x: float,
                      texture_y: float, distance: float) -> str:
        """
        Return the shaded texture character for a single wall pixel.

        Args:
            wall_type: One of the wall type strings from raycasting.
            texture_x: Horizontal texture coordinate [0, 1].
            texture_y: Vertical texture coordinate [0, 1].
            distance: Perpendicular distance to the wall.

        Returns:
            Single character string.
        """
        name_map = {
            'door_open': 'door',
            'door_locked': 'locked_door',
        }
        texture_name = name_map.get(wall_type, wall_type)
        char = self.texture_manager.sample_texture(texture_name, texture_x, texture_y)
        return self._shade(char, distance)

    def _shade(self, char: str, distance: float) -> str:
        key = (char, int(distance * 10))
        if key in self._shade_cache:
            return self._shade_cache[key]

        level = len(self.SHADE_DISTANCES)
        for i, threshold in enumerate(self.SHADE_DISTANCES):
            if distance < threshold:
                level = i
                break

        if level == 0:
            result = char
        elif level >= len(self._DIM_LEVELS) - 1:
            result = ' ' if char != '·' else '·'
        else:
            result = self._DIM_LEVELS[level].get(char, char)

        self._shade_cache[key] = result
        return result


# Module-level singleton
_texture_manager: TextureManager = None


def get_texture_manager() -> TextureManager:
    """Return the shared TextureManager instance, creating it on first call."""
    global _texture_manager
    if _texture_manager is None:
        _texture_manager = TextureManager()
    return _texture_manager
