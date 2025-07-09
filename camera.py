import gi
import logging

gi.require_version("Aravis", "0.8")
import ctypes
from abc import abstractmethod
from typing import Any, Optional

import cv2
import numpy as np
from gi.repository import Aravis

from configs import CameraConfigs, MainConfigs
from logger_config import logger


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
            cam_descriptor = CameraConfigs.DO3THINK_CAMERA_NAME
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
        self.device.release()


class AVICamera(Camera):
    def __init__(
        self,
        avi_path: str = None,
        fps: int = None,
        loop: bool = None,
        start_frame: int = None,
    ):
        if avi_path is None:
            avi_path = CameraConfigs.AVI_CAMERA_PATH

        if fps is None:
            fps = CameraConfigs.AVI_CAMERA_FPS
        if loop is None:
            loop = CameraConfigs.AVI_CAMERA_LOOP
        if start_frame is None:
            start_frame = CameraConfigs.AVI_CAMERA_START_FRAME

        super().__init__(avi_path)
        logger.info("Initializing AVI camera")
        logger.info(f"Video path: {avi_path}")
        logger.debug(f"Target FPS: {fps}")
        logger.debug(f"Loop enabled: {loop}")
        logger.debug(f"Start frame: {start_frame}")

        self.device = cv2.VideoCapture(avi_path)
        if not self.device.isOpened():
            logger.error(f"Could not open video file: {avi_path}")
        else:
            logger.info("Video opened successfully")
            # Log detailed camera information
            from utils import log_camera_info

            log_camera_info(self)

            # Set the starting frame if specified
            success = self.device.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            if success:
                logger.info(f"Successfully set start frame to: {start_frame}")
            else:
                logger.warning(f"Failed to set start frame to {start_frame}")

        self.fps = fps
        self.loop = loop
        self.frame_count = int(self.device.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = start_frame if start_frame > 0 else 0
        self.last_frame_time = 0
        self.frame_delay = 1000 / fps  # Convert FPS to milliseconds delay
        logger.debug(f"Frame delay set to: {self.frame_delay:.2f}ms")

    def device_is_activated(self) -> bool:
        is_activated = self.device is not None and self.device.isOpened()
        if not is_activated:
            logger.error("Device is not activated")
        return is_activated

    def start_stream(self):
        self.last_frame_time = 0
        logger.info(f"Stream started at frame {self.current_frame}")
        # Log camera info when stream starts
        from utils import log_camera_info

        log_camera_info(self)

    def get_next_frame(self):
        frame = None
        if self.device.isOpened():
            current_time = (
                cv2.getTickCount() / cv2.getTickFrequency() * 1000
            )  # Current time in milliseconds

            # Check if enough time has passed since last frame based on FPS
            if current_time - self.last_frame_time >= self.frame_delay:
                ret, frame = self.device.read()
                if not ret:
                    logger.debug(f"End of video reached at frame {self.current_frame}")
                    if self.loop:
                        logger.info("Looping back to start of video")
                        self.device.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.device.read()
                        if ret:
                            logger.info("Successfully looped to start")
                        else:
                            logger.error("Failed to read frame after loop")
                if ret:
                    self.last_frame_time = current_time
                    self.current_frame = (self.current_frame + 1) % self.frame_count
                    if self.current_frame % 100 == 0:  # Log every 100 frames
                        # Log detailed camera info every 1000 frames
                        if self.current_frame % 1000 == 0:
                            from utils import log_camera_info

                            log_camera_info(self)
        return frame

    def stop_stream(self):
        if self.device is not None:
            self.device.release()
            logger.info("Stream stopped and resources released")
