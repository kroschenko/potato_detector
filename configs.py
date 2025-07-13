from dataclasses import dataclass
import os
from typing import Tuple

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
    PREFERRED_CAMERA_DEVICE: CameraType = CameraType.AVI_CAMERA
    AVI_CAMERA_LOOP: bool = False
    AVI_CAMERA_FPS: int = 130
    AVI_CAMERA_START_FRAME: int = 0
    AVI_CAMERA_PATH: str = os.path.join(os.path.expanduser("./video/"), "13-29.avi")
    DO3THINK_CAMERA_NAME: str = "DO3THINK-04B400000199-"


@dataclass
class ArduinoConfigs:
    USE_AIR: bool = True
    TOP_NOZZLE_ACTIVATION_DELAY = 1.9
    BOTTOM_NOZZLE_ACTIVATION_DELAY = 1.9
    NOZZLE_ACTIVE_PERIOD = 0.5  # in sec
    TOP_NOZZLE_MNEMONIC = "T"
    BOTTOM_NOZZLE_MNEMONIC = "B"
    LED_MNEMONIC = "P"
    PIN_HIGH = "1"
    PIN_LOW = "0"
    ARDUINO_BAUD_RATE = 115200
    ARDUINO_PORT = "/dev/cu.usbserial-120"
