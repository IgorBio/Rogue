from data.save_manager import SaveManager


class DummyCamera:
    def __init__(self):
        self.x = 1.5
        self.y = 2.5
        self.angle = 30.0
        self.fov = 60.0


def test_serialize_camera_none(tmp_path):
    sm = SaveManager(save_dir=str(tmp_path))
    assert sm._serialize_camera(None) is None


def test_serialize_camera_values(tmp_path):
    sm = SaveManager(save_dir=str(tmp_path))
    camera = DummyCamera()
    data = sm._serialize_camera(camera)
    assert data["x"] == camera.x
    assert data["y"] == camera.y
    assert data["angle"] == camera.angle
    assert data["fov"] == camera.fov
