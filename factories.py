from typing import Any

from camera import Camera, DO3ThinkCamera, OpenCVCamera
from main_types import CameraType


class CameraFactory:
    @staticmethod
    def get_camera_device(cam_type: CameraType, desc: Any = None) -> Camera:
        cam_switch = {CameraType.OPENCV_CAMERA: OpenCVCamera, CameraType.DO3THINK_CAMERA: DO3ThinkCamera}
        return cam_switch[cam_type](desc)
