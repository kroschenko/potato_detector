from configs import CameraConfig, TrackerConfigs
from camera import Camera, DO3ThinkCamera, OpenCVCamera, AVICamera
import cv2
from tracker import PotatoTracker
from multiprocessing import Process, Queue
from dataclasses import asdict
from main_types import CameraType

potato_timing_top_queue = Queue()
potato_timing_bottom_queue = Queue()


class CameraFactory:
    @staticmethod
    def get_camera_device(
        cam_config: CameraConfig
    ) -> Camera:
        cam_config_dict = asdict(cam_config)
        cam_switch = {
            CameraType.OPENCV_CAMERA: OpenCVCamera,
            CameraType.DO3THINK_CAMERA: DO3ThinkCamera,
            CameraType.AVI_CAMERA: AVICamera,
        }
        return cam_switch[cam_config_dict["type"]](cam_config_dict)


class CameraManager:
    def __init__(self):
        self.cameras = []
        self.current_camera = -1
        self.tracker = PotatoTracker(
            potato_timing_top_queue,
            potato_timing_bottom_queue,
        )

    def add_camera(self, camera_config: CameraConfig):
        camera = CameraFactory.get_camera_device(camera_config)
        self.cameras.append(camera)
        self.current_camera = len(self.cameras) - 1

    def set_current_camera(self, index: int):
        self.current_camera = index

    def circular_switch_current_camera(self):
        ind = self.current_camera
        self.set_current_camera((ind + 1) % len(self.cameras))

    def get_current_camera_index(self):
        return self.current_camera

    def activate_camera(self, index: int):
        if not self.cameras[index].camera_activated:
            self.cameras[index].start_stream()

    def deactivate_camera(self, index: int):
        if self.cameras[index].camera_activated:
            self.cameras[index].stop_stream()

    def activate_all_cameras(self) -> bool:
        for camera in self.cameras:
            if not camera.camera_activated:
                camera.start_stream()
                if not camera.camera_activated:
                    return False
        return True

    def deactivate_all_cameras(self) -> None:
        for camera in self.cameras:
            if camera.camera_activated:
                camera.stop_stream()

    def get_next_frame(self):
        frames = []
        for camera in self.cameras:
            if camera.camera_activated:
                frame = camera.get_next_frame()
                if frame is not None:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, dsize=TrackerConfigs.FRAME_SIZE, interpolation=cv2.INTER_CUBIC)
                    frames.append(frame)
        if len(frames) > 0:
            frames = self.tracker.update(frames, 0)
        return frames[self.current_camera] if len(frames) > 0 else None
