from dataclasses import dataclass
import os
from typing import Any, Tuple

from main_types import CameraType


@dataclass
class MainConfigs:
    DO3THINK_CAMERA_NAME: str = "DO3THINK-04B400000199-"
    OPENCV_CAMERA_DESC: Any = 0
    POTATO_DETECTOR_PATH: str = "models/potato_det.pt"
    DEFECTS_CLASSIFIER_PATH: str = "models/defects_classifier.pth"
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
    NUM_CLASSES: int = 2
    PREFERRED_CAMERA_DEVICE: CameraType = CameraType.OPENCV_CAMERA
    POTATO_DETECTION_CONFIDENCE_THRESHOLD: float = 0.85
    DEFECTS_DETECTION_CONFIDENCE_THRESHOLD: float = 0.75
    SCANNING_WINDOW: int = 50
    FIRST_STAGE_MIDDLE_POINT: float = 0.165
    SECOND_STAGE_MIDDLE_POINT: float = 0.495
    THIRD_STAGE_MIDDLE_POINT: float = 0.825
    CAMERA_FRAME_SHAPE: Tuple = (1080, 1920, 3)
    FIRST_STAGE_TIME_DELAY: int = 3
    SECOND_STAGE_TIME_DELAY: int = 2
    THIRD_STAGE_TIME_DELAY: int = 1
    ARDUINO_PATH: str = "/dev/ttyUSB0" #"/dev/cu.usbserial-120"

    SAVE_PATH: str = os.path.join(os.path.expanduser("~"), "frames")
    # AVI file camera emulation settings
    # not used USE_AVI_CAMERA: bool = False


    AVI_CAMERA_START_FRAME: int = 0 # Frame number to start playback from (0-based)

    # Logging configuration
    LOG_FILE_MAX_SIZE: int = 1 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    #LOG_CONSOLE_LEVEL: str = "DEBUG"  # Console log level
    #LOG_FILE_LEVEL: str = "DEBUG"  # File log level
#most common fast change for debug
    #!!!!!!!!
    PREFERRED_CAMERA_DEVICE: CameraType =CameraType.AVI_CAMERA   #CameraType.DO3THINK_CAMERA # # CameraType.OPENCV_CAMERA##
    AVI_CAMERA_LOOP: bool = False#True
    USE_AIR: bool = False  # True #
    SAVE_FRAMES: bool = True  # False
    LOG_LEVEL: str = "INFO"  # ,DEBUG , WARNING, ERROR
    AVI_CAMERA_PATH: str = os.path.join(os.path.expanduser("./video/"),
                                        "14-31.avi"
                                        )#"16-51 09-38.avi")
    AVI_CAMERA_LOOP: bool = False#True
    AVI_CAMERA_FPS: int = 130
    CAMERA_AUTOSTART: bool = True  #False Whether to start camera automatically when application starts