import os
import sys
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from factories import CameraFactory
from configs import CameraConfigs


class CameraService:
    def __init__(self):
        self.camera_device = None

    def ensure_device_created(self) -> None:
        if self.camera_device is None:
            self.camera_device = CameraFactory.get_camera_device(
                CameraConfigs.PREFERRED_CAMERA_DEVICE
            )

    def activate_stream(self) -> None:
        self.ensure_device_created()
        if not self.camera_device.device_is_activated():
            self.camera_device.restart_stream()
        self.camera_device.start_stream()

    def deactivate_stream(self) -> None:
        if self.camera_device is not None:
            self.camera_device.stop_stream()

    def get_next_frame(self) -> Optional[object]:
        if self.camera_device is None:
            return None
        return self.camera_device.get_next_frame()

    def restart_stream(self) -> None:
        if self.camera_device is not None:
            self.camera_device.restart_stream()

    def device_is_activated(self) -> bool:
        if self.camera_device is None:
            return False
        return self.camera_device.device_is_activated()


