from presentation.camera.camera import Camera
from presentation.rendering.sprite_renderer_3d import Sprite, SpriteRenderer


def test_sprite_projection_uses_forward_distance_not_euclidean():
    renderer = SpriteRenderer(viewport_width=80, viewport_height=24, fov=60.0)
    camera = Camera(0.0, 0.0, angle=0.0, fov=60.0)

    # Euclidean distance is > max, but forward depth is still inside max.
    sprite = Sprite(19.0, 10.0, "E", color=1, sprite_type="enemy")
    visible = renderer.calculate_sprite_positions([sprite], camera)

    assert len(visible) == 1
    assert visible[0].distance == 19.0


def test_sprite_far_shading_keeps_faint_marker_until_max_distance():
    renderer = SpriteRenderer(viewport_width=80, viewport_height=24, fov=60.0)

    very_far = renderer.max_sprite_distance * 0.95
    assert renderer._shade_char("E", very_far) == "·"
