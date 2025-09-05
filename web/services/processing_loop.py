import time
import cv2
from typing import Callable

from configs import CameraConfigs
from main_types import CameraType


class ProcessingLoop:
    def __init__(self, camera_service, tracking_service, annotation_service, frame_store, statistics_service, logger):
        self.camera_service = camera_service
        self.tracking_service = tracking_service
        self.annotation_service = annotation_service
        self.frame_store = frame_store
        self.statistics_service = statistics_service
        self.logger = logger
        self.running = False

    def start(self) -> None:
        if self.running:
            return
        self.running = True

    def stop(self) -> None:
        self.running = False

    def run_forever(self) -> None:
        self.logger.info("Frame processing started")
        frame_count = 0
        while self.running:
            try:
                frame = self.camera_service.get_next_frame()
                if frame is not None:
                    frame_count += 1
                    if frame_count % 30 == 0:
                        self.logger.debug(f"Processed {frame_count} frames")

                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.tracking_service.update_with_rgb_frame(frame_rgb)
                    annotated_frame = self.annotation_service.annotate_frame(frame_rgb.copy(), self.tracking_service.get_active_objects())
                    self.frame_store.set_current_frame(annotated_frame)

                    total_objects = self.tracking_service.get_total_objects_count()
                    self.statistics_service.update_counts(total_objects)

                    time.sleep(1.0 / CameraConfigs.TARGET_STREAM_FPS)
                else:
                    self.logger.warning("No frame received from camera")
                    if CameraConfigs.PREFERRED_CAMERA_DEVICE in [
                        CameraType.OPENCV_CAMERA,
                        CameraType.AVI_CAMERA,
                    ]:
                        if CameraConfigs.AVI_CAMERA_LOOP:
                            self.logger.info("Restarting AVI camera stream")
                            try:
                                self.camera_service.restart_stream()
                                continue
                            except Exception as e:
                                self.logger.error(f"Failed to restart camera stream: {e}")
                                break
                        else:
                            self.logger.info("AVI file finished, stopping processing")
                            break
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in frame processing: {e}")
                time.sleep(0.1)

        self.logger.info("Frame processing stopped")


