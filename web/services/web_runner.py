import os
import sys
import threading
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from logger_config import logger
from services.camera_service import CameraService
from services.tracking_service import TrackingService
from services.annotation_service import AnnotationService
from services.frame_store import FrameStore
from services.statistics_service import StatisticsService
from services.processing_loop import ProcessingLoop


class WebRunner:
    def __init__(self):
        self.camera_activated = False
        self.camera_service = CameraService()
        self.tracking_service = TrackingService()
        self.annotation_service = AnnotationService()
        self.frame_store = FrameStore()
        self.statistics_service = StatisticsService()
        self.processing_loop = ProcessingLoop(
            self.camera_service,
            self.tracking_service,
            self.annotation_service,
            self.frame_store,
            self.statistics_service,
            logger,
        )
        self.processing_thread = None

    def activate_camera(self) -> bool:
        logger.info("Attempting to activate camera")
        if self.camera_activated:
            logger.warning("Camera already activated")
            return False
        try:
            self.camera_service.activate_stream()
            self.camera_activated = True
            self.processing_loop.start()
            self.processing_thread = threading.Thread(target=self.processing_loop.run_forever, daemon=True)
            self.processing_thread.start()
            logger.info("Camera activated and processing started")
            return True
        except Exception as e:
            logger.error(f"Failed to activate camera: {e}")
            return False

    def deactivate_camera(self) -> None:
        if self.camera_activated:
            self.processing_loop.stop()
            if self.processing_thread:
                self.processing_thread.join()
            self.camera_activated = False
            try:
                self.camera_service.deactivate_stream()
            except Exception as e:
                logger.error(f"Error while stopping stream: {e}")

    def get_current_frame_jpeg(self) -> Optional[bytes]:
        jpeg = self.frame_store.get_current_frame_jpeg()
        if jpeg is not None:
            return jpeg
        return self.frame_store.get_placeholder_jpeg()

    def get_statistics(self) -> dict:
        defects = self.tracking_service.get_total_defects_detected()
        return self.statistics_service.build_statistics(defects)


