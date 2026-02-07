from presentation.rendering.texture_system import get_texture_manager, TexturedRenderer


def test_textured_renderer_maps_open_door_to_door_texture():
    manager = get_texture_manager()
    renderer = TexturedRenderer(manager)

    texture_char = manager.sample_texture("door", 0.2, 0.3)
    wall_char = renderer.get_wall_char("door_open", 0.2, 0.3, 0.0)

    assert wall_char == texture_char


def test_textured_renderer_maps_locked_door_to_locked_door_texture():
    manager = get_texture_manager()
    renderer = TexturedRenderer(manager)

    texture_char = manager.sample_texture("locked_door", 0.6, 0.1)
    wall_char = renderer.get_wall_char("door_locked", 0.6, 0.1, 0.0)

    assert wall_char == texture_char
