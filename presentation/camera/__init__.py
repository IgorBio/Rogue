"""
Camera package for 3D mode.

Contains Camera class, CameraController, and synchronization utilities.
"""

from presentation.camera.camera import Camera, RayHit
from presentation.camera.controller import CameraController
from presentation.camera.sync import CameraSync, create_synced_pair, camera_sync

__all__ = [
    'Camera',
    'RayHit',
    'CameraController',
    'CameraSync',
    'create_synced_pair',
    'camera_sync',
]
