import cv2
import utils

from configs import CameraConfigs, TrackerConfigs, ArduinoConfigs
from constants import Messages
from factories import CameraFactory
from tracker import PotatoTracker
from multiprocessing import Process, Queue
from logger_config import logger
from arduino import activate_nozzle, led_on
from main_types import CameraType

global top_impulse, bottom_impulse
potato_defects_queue = []
potato_timing_top_queue = Queue()
potato_timing_bottom_queue = Queue()


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
            potato_timing_top_queue,
            potato_timing_bottom_queue,
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
                        if CameraConfigs.PREFERRED_CAMERA_DEVICE in [CameraType.OPENCV_CAMERA, CameraType.AVI_CAMERA]:
                            break

            else:
                logger.error(Messages.ERROR_CAMERA_IS_NOT_FOUNDED)

    def update(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.tracker.update(frame)

        current_objects_total_count = self.tracker.get_total_objects_count()
        if current_objects_total_count > self.prev_total_objects_count:
            self.counter += 1
            logger.info(f"{Messages.OBJECTS_COUNT} {self.counter}")
            self.prev_total_objects_count = current_objects_total_count

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Override closeEvent to log statistics before closing"""
        utils.logger.info("Thread is finishing...")
        self.tracker.log_final_statistics(self.counter)
        if self.camera_activated:
            self.camera_activated = False
            self.camera.stop_stream()
            self.timer = None
            self.camera = None
        if ArduinoConfigs.USE_AIR:
            potato_timing_top_queue.put(-1)
            potato_timing_bottom_queue.put(-1)
            top_impulse.join()
            bottom_impulse.join()


if __name__ == "__main__":
    led_on()
    if ArduinoConfigs.USE_AIR:
        top_impulse = Process(
            target=activate_nozzle, args=(potato_timing_top_queue, 0), daemon=True
        )
        bottom_impulse = Process(
            target=activate_nozzle, args=(potato_timing_bottom_queue, 1), daemon=True
        )
        top_impulse.start()
        bottom_impulse.start()

    with Runner() as runner:
        pass
