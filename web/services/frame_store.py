import threading
import cv2
import numpy as np
import os
import sys
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from configs import CameraConfigs


class FrameStore:
    def __init__(self):
        self.current_frame_rgb = None
        self.frame_lock = threading.Lock()
        self.current_frame_id = 0
        self.cached_frame_id = -1
        self.cached_jpeg = None
        height, width, _ = CameraConfigs.CAMERA_FRAME_SHAPE
        placeholder = np.zeros((height, width, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', placeholder)
        self.placeholder_jpeg = buffer.tobytes()

    def set_current_frame(self, frame_rgb) -> None:
        with self.frame_lock:
            self.current_frame_rgb = frame_rgb
            self.current_frame_id += 1

    def get_current_frame_jpeg(self) -> Optional[bytes]:
        with self.frame_lock:
            local_frame = self.current_frame_rgb
            local_frame_id = self.current_frame_id
            if local_frame is None:
                return None
            if self.cached_jpeg is not None and self.cached_frame_id == local_frame_id:
                return self.cached_jpeg
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(local_frame, cv2.COLOR_RGB2BGR))
        jpeg = buffer.tobytes()
        with self.frame_lock:
            if self.current_frame_id == local_frame_id:
                self.cached_frame_id = local_frame_id
                self.cached_jpeg = jpeg
        return jpeg

    def get_placeholder_jpeg(self) -> bytes:
        return self.placeholder_jpeg


