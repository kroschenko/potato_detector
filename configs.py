from dataclasses import dataclass
import os
from typing import Tuple

from main_types import CameraType


@dataclass
class MainConfigs:
    DEFAULT_DEVICE: str = "cpu"
    CUDA_DEVICE: str = "cuda"
    SAVE_FRAMES: bool = False
    SAVE_PATH: str = os.path.join(os.path.expanduser("~"), "frames")


@dataclass
class SorterConfigs:
    SORT_BY_OUTER_DEFECTS: bool = True
    SORT_BY_POTATO_SIZE: bool = True
    SORT_BY_ROTTEN: bool = True
    SORT_BY_GREEN: bool = True
    SORT_BY_DAMAGED: bool = True
    POTATO_SIZE_LIMIT_CENTIMETERS: float = 35


@dataclass
class LoggerConfigs:
    LOG_FILE_MAX_SIZE: int = 1 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    LOG_LEVEL: str = "INFO"  # ,DEBUG , WARNING, ERROR


@dataclass
class ModelsConfigs:
    POTATO_DETECTOR_PATH: str = "models/potato_det.pt"
    DEFECTS_CLASSIFIER_PATH: str = "models/4_classes_classifier_67.pth"
    NUM_CLASSES: int = 4
    POTATO_DETECTION_CONFIDENCE_THRESHOLD: float = 0.6
    DEFECTS_DETECTION_CONFIDENCE_THRESHOLD: float = 0.75


@dataclass
class TrackerConfigs:
    FRAME_SIZE: Tuple = (1200, 1920)
    SCANNING_WINDOW: int = 50
    SCAN_ZONES_COUNT: int = 9
    VISIBLE_AREA_WIDTH_CENTIMETERS: float = 43.0
    VISIBLE_AREA_HEIGHT_CENTIMETERS: float = 25.0


@dataclass
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
    CAMERA_FRAME_SHAPE: Tuple = (1080, 1920, 3)
    PREFERRED_CAMERA_DEVICE: CameraType = CameraType.DO3THINK_CAMERA
    AVI_CAMERA_LOOP: bool = False
    AVI_CAMERA_FPS: int = 130
    AVI_CAMERA_START_FRAME: int = 0
    AVI_CAMERA_PATH: str = os.path.join(
        os.path.expanduser("./video/"), "BAD_2.wmv"
    )
    DO3THINK_CAMERA_NAME: str = "DO3THINK-04B400000199-"


@dataclass
class ArduinoConfigs:
    USE_AIR: bool = True
    ARDUINO_ONLINE: bool = True
    FIRST_NOZZLE_MNEMONIC = "R1"
    SECOND_NOZZLE_MNEMONIC = "R2"
    LED_MNEMONIC = "P"
    PIN_HIGH = "1"
    PIN_LOW = "0"
    ARDUINO_BAUD_RATE = 115200
    ARDUINO_PORT = "/dev/ttyUSB0"
    NOZZLE_DELAY_BEFORE_OPEN_TOP: int = 420
    NOZZLE_DELAY_BEFORE_OPEN_BOTTOM: int = 600
