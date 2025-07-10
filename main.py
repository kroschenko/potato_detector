import time

import cv2
import utils

from configs import CameraConfigs, TrackerConfigs
from constants import Messages
from factories import CameraFactory
from tracker import PotatoTracker
from multiprocessing import Process, Queue
from logger_config import logger
from control_from_another_prog.simple_impulse import send_impulse_raspberry

global top_impulse, bottom_impulse
potato_defects_queue = []
potato_timing_top_queue = Queue()
potato_timing_bottom_queue = Queue()


def send_impulse(input_queue: Queue, cam_id: int):
    delay = (
        TrackerConfigs.TOP_NOZZLE_ACTIVATION_DELAY
        if cam_id == 0
        else TrackerConfigs.BOTTOM_NOZZLE_ACTIVATION_DELAY
    )
    while True:
        sample = input_queue.get()
        time.sleep(delay - (time.time() - sample))
        # send_impulse_raspberry(cam_id)
        logger.info(f"Send impulse {cam_id} to raspberry board")


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
        # Auto-start camera if configured
        if CameraConfigs.CAMERA_AUTOSTART:
            utils.logger.info("Auto-starting camera as per configuration")
            self.activate_camera()

    def calibrate(self):
        pass

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
                    self.update()
            else:
                logger.error(Messages.ERROR_CAMERA_IS_NOT_FOUNDED)

    def deactivate_camera(self):
        if self.camera_activated:
            self.camera_activated = False
            self.camera.stop_stream()
            self.timer = None
            self.camera = None

    def update(self):
        frame = self.camera.get_next_frame()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.tracker.update(frame)

            current_objects_total_count = self.tracker.get_total_objects_count()
            if current_objects_total_count > self.prev_total_objects_count:
                self.counter += 1
                logger.info(f"{Messages.OBJECTS_COUNT} {self.counter}")
                self.prev_total_objects_count = current_objects_total_count
        else:
            pass

    def closeEvent(self, event):
        """Override closeEvent to log statistics before closing"""
        utils.logger.info("Application is closing...")
        self.tracker.log_final_statistics(self.counter)
        if self.camera:
            self.camera.stop_stream()
        if TrackerConfigs.USE_AIR and hasattr(self, "serial_interface_thread"):
            self.serial_interface_thread.quit()
            self.serial_interface_thread.wait()
        event.accept()
        if top_impulse:
            top_impulse.terminate()
        if bottom_impulse:
            bottom_impulse.terminate()


if __name__ == "__main__":
    if TrackerConfigs.USE_AIR:
        top_impulse = Process(
            target=send_impulse, args=(potato_timing_top_queue, 0), daemon=True
        )
        bottom_impulse = Process(
            target=send_impulse, args=(potato_timing_bottom_queue, 1), daemon=True
        )
        top_impulse.start()
        bottom_impulse.start()

    runner = Runner()
    runner.activate_camera()
