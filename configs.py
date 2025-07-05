from dataclasses import dataclass, field
import os
from typing import Any, Dict, Tuple

from main_types import CameraType


@dataclass
class MainConfigs:
    MAIN_FORM_NAME: str = "mainForm.ui"
    DEFAULT_DEVICE: str = "cpu"
    SAVE_FRAMES: bool = False
    SAVE_PATH: str = os.path.join(os.path.expanduser("~"), "frames")


@dataclass
class LoggerConfigs:
    LOG_FILE_MAX_SIZE: int = 1 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    LOG_LEVEL: str = "INFO"  # ,DEBUG , WARNING, ERROR


@dataclass
class ModelsConfigs:
    POTATO_DETECTOR_PATH: str = "models/potato_det.pt"
    DEFECTS_CLASSIFIER_PATH: str = "models/defects_classifier_v3.pth"
    NUM_CLASSES: int = 2
    POTATO_DETECTION_CONFIDENCE_THRESHOLD: float = 0.85
    DEFECTS_DETECTION_CONFIDENCE_THRESHOLD: float = 0.75


@dataclass
class TrackerConfigs:
    FRAME_SIZE: Tuple = (1200, 1920)
    SCANNING_WINDOW: int = 50
    SCAN_ZONES_COUNT: int = 9
    USE_AIR: bool = True
    NOZZLE_ACTIVATION_DELAY = 1.9  # controller po53 =  75 = 130 potat min
    # 5.5 2000 rpm motor


# @dataclass
class CameraConfigs:
    CAMERA_STATUS_STYLE_ON: str = """ 
                    QLabel { 
                        color: green; 
                        font-weight: bold; 
                    }
                """
    CAMERA_STATUS_STYLE_OFF: str = """ 
                    QLabel { 
                        color: red; 
                        font-weight: bold; 
                    }
                """
    CAMERA_AUTOSTART: bool = True
    # DO3THINK_CAMERA_DEVICE: Dict[str, Any] = {
    #     "descriptor": "DO3THINK-04B400000199-",
    #     "frame_shape": (1080, 1920, 3),
    #     "type": CameraType.DO3THINK_CAMERA,
    # }
    # OPENCV_CAMERA_DEVICE: Dict[str, Any] = {
    #     "descriptor": 0,
    #     "frame_shape": (720, 1280, 3),
    #     "type": CameraType.OPENCV_CAMERA,
    # }
    # AVI_DEVICE: Dict[str, Any] = field(default_factory=get_avi_device_params)


@dataclass
class CameraConfig:
    descriptor: str
    frame_shape: Tuple
    type: CameraType
    #     "frame_shape": (1080, 1920, 3)
    #     "type": CameraType.DO3THINK_CAMERA


@dataclass
class Do3ThinkCameraConfig(CameraConfig):
    descriptor: str = "DO3THINK-04B400000199-"
    frame_shape: Tuple = (1200, 1920, 3)
    type: CameraType = CameraType.DO3THINK_CAMERA


@dataclass
class OpenCVCameraConfig(CameraConfig):
    descriptor: int = 0
    frame_shape: Tuple = (720, 1280, 3)
    type: CameraType = CameraType.OPENCV_CAMERA


@dataclass
class AVICameraConfig(CameraConfig):
    descriptor: str = os.path.join(os.path.expanduser("./video/"), "14-31.avi")
    frame_shape: Tuple = (1200, 1920, 3)
    type: CameraType = CameraType.AVI_CAMERA
    fps: int = 130
    loop: bool = False
    start_frame: int = 0

#
# class AVICameraConfig:
#     "descriptor": os.path.join(os.path.expanduser("./video/"), "14-31.avi")
#     "frame_shape": (1080, 1920, 3)
#     "type": CameraType.AVI_CAMERA
#     "fps": 130
#     "loop": False
#     "start_frame": 320