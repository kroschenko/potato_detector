import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from configs import TrackerConfigs, CameraConfigs
from tracker import PotatoTracker


class TrackingService:
    def __init__(self):
        self.tracker = PotatoTracker(
            CameraConfigs.CAMERA_FRAME_SHAPE,
            TrackerConfigs.SCAN_ZONES_COUNT,
        )

    def update_with_rgb_frame(self, frame_rgb):
        self.tracker.update(frame_rgb)

    def get_total_objects_count(self) -> int:
        return self.tracker.get_total_objects_count()

    def get_active_objects(self):
        return self.tracker.active_potato_objects

    def get_total_defects_detected(self) -> int:
        return self.tracker.total_defects_detected


