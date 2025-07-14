from typing import Any

from camera import Camera, DO3ThinkCamera, OpenCVCamera, AVICamera
from main_types import CameraType


class CameraFactory:
    @staticmethod
    def get_camera_device(cam_type: CameraType, desc: Any = None) -> Camera:
        cam_switch = {
            CameraType.OPENCV_CAMERA: OpenCVCamera,
            CameraType.DO3THINK_CAMERA: DO3ThinkCamera,
            CameraType.AVI_CAMERA: AVICamera,
        }
        return cam_switch[cam_type](desc)
