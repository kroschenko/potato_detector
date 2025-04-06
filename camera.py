import gi
gi.require_version('Aravis', '0.8')
import cv2
import numpy as np
import ctypes
from gi.repository import Aravis
from configs import MainConfigs
from abc import abstractmethod
from typing import Any, Optional


class Camera:
    def __init__(self, cam_descriptor: Any):
        self.cam_descriptor = cam_descriptor

    @abstractmethod
    def start_stream(self):
        pass

    @abstractmethod
    def stop_stream(self):
        pass

    @abstractmethod
    def get_next_frame(self) -> Optional[np.ndarray]:
        pass

    @abstractmethod
    def device_is_activated(self):
        pass


class DO3ThinkCamera(Camera):
    def __init__(self, cam_descriptor: str = None):
        if cam_descriptor is None:
            cam_descriptor = MainConfigs.DO3THINK_CAMERA_NAME
        super().__init__(cam_descriptor)
        try:
            self.device = Aravis.Camera.new(self.cam_descriptor)
        except gi.repository.GLib.Error:
            self.device = None
        self.stream = None

    def device_is_activated(self) -> bool:
        return self.device is not None

    def start_stream(self):
        payload = self.device.get_payload()
        self.stream = self.device.create_stream(None, None)
        self.stream.push_buffer(Aravis.Buffer.new_allocate(payload))
        self.device.start_acquisition()

    def get_next_frame(self):
        frame = None
        if self.stream:
            buffer = self.stream.try_pop_buffer()
            if buffer:
                frame = DO3ThinkCamera._convert(buffer)
                self.stream.push_buffer(buffer)  # push buffer back into stream
        return frame

    def stop_stream(self):
        self.device.stop_acquisition()
        self.stream = None

    @staticmethod
    def _convert(buf):
        if not buf:
            return None
        INTP = ctypes.POINTER(ctypes.c_uint8)
        addr = buf.get_data()
        ptr = ctypes.cast(addr, INTP)
        im = np.ctypeslib.as_array(ptr, (buf.get_image_height(), buf.get_image_width()))
        im = im.copy()
        return cv2.cvtColor(im, cv2.COLOR_BAYER_GB2RGB)


class OpenCVCamera(Camera):
    def __init__(self, cam_descriptor: Any = None):
        if cam_descriptor is None:
            cam_descriptor = 0
        super().__init__(cam_descriptor)
        self.device = cv2.VideoCapture(self.cam_descriptor)

    def device_is_activated(self):
        return self.device is not None

    def start_stream(self):
        pass

    def get_next_frame(self):
        frame = None
        if self.device.isOpened():
            ret, frame = self.device.read()
        return frame

    def stop_stream(self):
        if self.device.isOpened():
            self.device.release()
