"""
Rendering package for 3D visualization.

Contains raycasting, sprite rendering, textures, and mini-map rendering.
"""

from presentation.rendering.raycasting import (
    cast_ray,
    cast_fov_rays,
    calculate_wall_height,
)

from presentation.camera.camera import RayHit

from presentation.rendering.sprite_renderer_3d import (
    Sprite,
    SpriteRenderer,
)

from presentation.rendering.texture_system import (
    WallTexture,
    TextureManager,
    TexturedRenderer,
    get_texture_manager,
)

from presentation.rendering.minimap_renderer import (
    MiniMapRenderer,
)

__all__ = [
    # Raycasting
    'RayHit',
    'cast_ray',
    'cast_fov_rays',
    'calculate_wall_height',
    # Sprites
    'Sprite',
    'SpriteRenderer',
    # Textures
    'WallTexture',
    'TextureManager',
    'TexturedRenderer',
    'get_texture_manager',
    # Mini-map
    'MiniMapRenderer',
]
