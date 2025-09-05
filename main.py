import cv2
import utils
import argparse
import sys
import os

from configs import CameraConfigs, TrackerConfigs
from constants import Messages
from factories import CameraFactory
from tracker import PotatoTracker
from logger_config import logger
from arduino import led_on
from main_types import CameraType

potato_defects_queue = []


class Runner:
    def __init__(self):
        super().__init__()

        self.camera = None
        self.timer = None
        self.camera_activated = False
        self.counter = 0
        self.prev_total_objects_count = 0
        self.tracker = PotatoTracker(
            CameraConfigs.CAMERA_FRAME_SHAPE,
            TrackerConfigs.SCAN_ZONES_COUNT,
        )

    def __enter__(self):
        # Auto-start camera if configured
        if CameraConfigs.CAMERA_AUTOSTART:
            utils.logger.info("Auto-starting camera as per configuration")
            self.activate_camera()

    def null_objects_count(self):
        self.counter = 0
        logger.info(f"{Messages.OBJECTS_COUNT} {self.counter}")

    def activate_camera(self):
        # Запуск камеры
        if not self.camera_activated:
            if self.camera is None:
                self.camera = CameraFactory.get_camera_device(
                    CameraConfigs.PREFERRED_CAMERA_DEVICE
                )
            if self.camera.device_is_activated():
                self.camera_activated = True
                self.camera.start_stream()

                # Таймер для обновления кадров
                while True:
                    if (frame := self.camera.get_next_frame()) is not None:
                        self.update(frame)
                    else:
                        if CameraConfigs.PREFERRED_CAMERA_DEVICE in [
                            CameraType.OPENCV_CAMERA,
                            CameraType.AVI_CAMERA,
                        ]:
                            break
            else:
                logger.error(Messages.ERROR_CAMERA_IS_NOT_FOUNDED)

    def update(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.tracker.update(frame)

        self.counter = self.tracker.get_total_objects_count()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Override closeEvent to log statistics before closing"""
        utils.logger.info("Thread is finishing...")
        self.tracker.log_final_statistics(self.counter)
        if self.camera_activated:
            self.camera_activated = False
            self.camera.stop_stream()
            self.timer = None
            self.camera = None


def run_console_mode():
    led_on()
    with Runner() as runner:
        pass


def run_web_mode():
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'web'))
        from app import start_web_server
        
        logger.info("Starting Potato Detection System in Web Mode")
        start_web_server()
    except ImportError as e:
        logger.error(f"Failed to import web dependencies: {e}")
        logger.error("Make sure to install web dependencies: pip install Flask Flask-SocketIO")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Potato Detection System')
    parser.add_argument('--web', action='store_true', 
                       help='Run in web mode with browser interface')
    
    args = parser.parse_args()
    
    if args.web:
        run_web_mode()
    else:
        run_console_mode()


if __name__ == "__main__":
    main()
