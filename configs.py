from dataclasses import dataclass
from typing import Any, Tuple

from main_types import CameraType


@dataclass
class MainConfigs:
    DO3THINK_CAMERA_NAME: str = "DO3THINK-04B400000199-"
    OPENCV_CAMERA_DESC: Any = 0
    POTATO_DETECTOR_PATH: str = "models/potato_detector.pt"
    DEFECTS_DETECTOR_PATH: str = "models/mechdamage_detector.pt"
    MAIN_FORM_NAME: str = "mainForm.ui"
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
    PREFERRED_CAMERA_DEVICE: CameraType = CameraType.OPENCV_CAMERA
    POTATO_DETECTION_CONFIDENCE_THRESHOLD: float = 0.75
    DEFECTS_DETECTION_CONFIDENCE_THRESHOLD: float = 0.75
    SCANNING_WINDOW: int = 50
    FIRST_STAGE_MIDDLE_POINT: float = 0.165
    SECOND_STAGE_MIDDLE_POINT: float = 0.495
    THIRD_STAGE_MIDDLE_POINT: float = 0.825
    CAMERA_FRAME_SHAPE: Tuple = (1080, 1920, 3)
    FIRST_STAGE_TIME_DELAY: int = 3
    SECOND_STAGE_TIME_DELAY: int = 2
    THIRD_STAGE_TIME_DELAY: int = 1
    ARDUINO_PATH: str = "/dev/cu.usbserial-120"
    USE_AIR: bool = False
