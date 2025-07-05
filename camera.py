import gi

gi.require_version("Aravis", "0.8")
import ctypes
from abc import abstractmethod
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from gi.repository import Aravis

from configs import CameraConfigs
from logger_config import logger


def log_camera_info(camera):
    """Log detailed camera information"""
    if camera is None:
        logger.error("Cannot log camera info: camera is None")
        return

    logger.debug("Camera Information:")
    logger.debug(f"Camera Type: {camera.__class__.__name__}")

    if isinstance(camera, AVICamera):
        logger.debug("AVI Camera Properties:")
        logger.debug(f"  - Video Path: {camera.descriptor}")

        if camera.device is not None and camera.device.isOpened():
            logger.debug("Video Properties:")
            logger.debug(
                f"  - Frame Width: {camera.device.get(cv2.CAP_PROP_FRAME_WIDTH)}"
            )
            logger.debug(
                f"  - Frame Height: {camera.device.get(cv2.CAP_PROP_FRAME_HEIGHT)}"
            )
            logger.debug(f"  - Original FPS: {camera.device.get(cv2.CAP_PROP_FPS)}")
            logger.debug(f"  - FourCC Codec: {camera.device.get(cv2.CAP_PROP_FOURCC)}")
            logger.debug(
                f"  - Current Position: {camera.device.get(cv2.CAP_PROP_POS_FRAMES)}"
            )
            logger.debug(
                f"  - Brightness: {camera.device.get(cv2.CAP_PROP_BRIGHTNESS)}"
            )
            logger.debug(f"  - Contrast: {camera.device.get(cv2.CAP_PROP_CONTRAST)}")
            logger.debug(
                f"  - Saturation: {camera.device.get(cv2.CAP_PROP_SATURATION)}"
            )
            logger.debug(f"  - Hue: {camera.device.get(cv2.CAP_PROP_HUE)}")
            logger.debug(f"  - Gain: {camera.device.get(cv2.CAP_PROP_GAIN)}")
            logger.debug(f"  - Exposure: {camera.device.get(cv2.CAP_PROP_EXPOSURE)}")
    elif isinstance(camera, DO3ThinkCamera):
        logger.debug("DO3Think Camera Properties:")
        logger.debug(f"  - Camera Name: {camera.descriptor}")
        logger.debug(f"  - Device Activated: {camera.device_is_activated()}")
    elif isinstance(camera, OpenCVCamera):
        logger.debug("OpenCV Camera Properties:")
        logger.debug(f"  - Camera Index: {camera.descriptor}")
        logger.debug(f"  - Device Activated: {camera.device_is_activated()}")


class Camera:
    def __init__(self, params: Dict[str, Any]) -> None:
        self.descriptor = params["descriptor"]
        self.frame_shape = params["frame_shape"]
        self.camera_activated = False

    @abstractmethod
    def start_stream(self) -> None:
        pass

    @abstractmethod
    def stop_stream(self) -> None:
        pass

    @abstractmethod
    def get_next_frame(self) -> Optional[np.ndarray]:
        pass

    def get_shape(self) -> Tuple[int]:
        return self.frame_shape
    # def device_is_activated(self) -> bool:
    #     return self.camera_activated


class DO3ThinkCamera(Camera):
    def __init__(self, params: Dict[str, Any] = None) -> None:
        super().__init__(params)
        self.device = None
        self.stream = None

    def start_stream(self) -> None:
        try:
            self.device = Aravis.Camera.new(self.descriptor)
            payload = self.device.get_payload()
            self.stream = self.device.create_stream(None, None)
            self.stream.push_buffer(Aravis.Buffer.new_allocate(payload))
            self.device.start_acquisition()
            self.camera_activated = True
        except gi.repository.GLib.Error:
            self.device = None
            self.stream = None

    def get_next_frame(self) -> Optional[np.ndarray]:
        frame = None
        if self.camera_activated:
            buffer = self.stream.try_pop_buffer()
            if buffer:
                frame = DO3ThinkCamera._convert(buffer)
                self.stream.push_buffer(buffer)  # push buffer back into stream
        return frame

    def stop_stream(self) -> None:
        if self.camera_activated:
            self.device.stop_acquisition()
            self.stream, self.device = None, None
            self.camera_activated = False

    @staticmethod
    def _convert(buf) -> Optional[np.ndarray]:
        if not buf:
            return None
        intp = ctypes.POINTER(ctypes.c_uint8)
        addr = buf.get_data()
        ptr = ctypes.cast(addr, intp)
        im = np.ctypeslib.as_array(ptr, (buf.get_image_height(), buf.get_image_width()))
        im = im.copy()
        return cv2.cvtColor(im, cv2.COLOR_BAYER_GB2RGB)


class OpenCVCamera(Camera):
    def __init__(self, params: Dict[str, Any] = None) -> None:
        super().__init__(params)
        self.device = None

    def start_stream(self):
        self.device = cv2.VideoCapture(self.descriptor)
        self.camera_activated = self.device is not None and self.device.isOpened()

    def get_next_frame(self):
        frame = None
        if self.camera_activated:
            ret, frame = self.device.read()
        return frame

    def stop_stream(self):
        if self.camera_activated:
            self.device.release()
            self.camera_activated = False


class AVICamera(Camera):
    def __init__(self, params: Dict[str, Any] = None) -> None:
        super().__init__(params)

        self.fps = params["fps"]
        self.loop = params["loop"]
        self.start_frame = params["start_frame"]
        self.current_frame = self.start_frame if self.start_frame > 0 else 0
        self.last_frame_time = 0
        self.frame_delay = 1000 / self.fps  # Convert FPS to milliseconds delay
        self.frame_count = 0
        self.device = None

        logger.info("Initializing AVI camera")
        logger.info(f"Video path: {self.descriptor}")
        logger.debug(f"Target FPS: {self.fps}")
        logger.debug(f"Loop enabled: {self.loop}")
        logger.debug(f"Start frame: {self.start_frame}")
        logger.debug(f"Frame delay set to: {self.frame_delay:.2f}ms")

    def start_stream(self):
        self.device = cv2.VideoCapture(self.descriptor)
        if not self.device.isOpened():
            logger.error(f"Could not open video file: {self.descriptor}")
        else:
            logger.info("Video opened successfully")
            # Log detailed camera information
            # log_camera_info(self)

            # Set the starting frame if specified
            success = self.device.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
            if success:
                logger.info(f"Successfully set start frame to: {self.start_frame}")
            else:
                logger.warning(f"Failed to set start frame to {self.start_frame}")

            self.frame_count = int(self.device.get(cv2.CAP_PROP_FRAME_COUNT))
            self.last_frame_time = 0
            logger.info(f"Stream started at frame {self.current_frame}")
            # Log camera info when stream starts
            log_camera_info(self)
            self.camera_activated = self.device is not None and self.device.isOpened()

    def get_next_frame(self):
        frame = None
        if self.camera_activated:
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
                            log_camera_info(self)
        return frame

    def stop_stream(self):
        if self.camera_activated:
            self.device.release()
            logger.info("Stream stopped and resources released")
            self.camera_activated = False
