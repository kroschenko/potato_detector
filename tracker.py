import time
from collections import OrderedDict
from typing import List

import cv2
import numpy as np
from norfair import Detection, Tracker, draw_points
from ultralytics import YOLO

from configs import MainConfigs
from constants import Color, Messages
from potato_object import PotatoObject


class PotatoTracker:
    def __init__(self, frame_size, potato_defects_queue: List, potato_timing_queue: List):
        self.potato_detector = YOLO(MainConfigs.POTATO_DETECTOR_PATH)
        self.defects_detector = YOLO(MainConfigs.DEFECTS_DETECTOR_PATH)
        self.tracker = Tracker(distance_function="euclidean", distance_threshold=100)
        self.active_potato_objects = {}
        frame_width = frame_size[1]
        self.first_section_middle = int(MainConfigs.FIRST_STAGE_MIDDLE_POINT * frame_width)
        self.second_section_middle = int(MainConfigs.SECOND_STAGE_MIDDLE_POINT * frame_width)
        self.third_section_middle = int(MainConfigs.THIRD_STAGE_MIDDLE_POINT * frame_width)
        self.potato_defects_queue = potato_defects_queue
        self.potato_timing_queue = potato_timing_queue

    def get_total_objects_count(self):
        return self.tracker.total_object_count

    def update(self, frame, text_browser):
        if frame is not None:
            results = self.potato_detector(frame, verbose=False)
            detections = []
            centers = []
            bounds = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    score = box.conf[0].cpu().numpy()
                    if score > MainConfigs.POTATO_DETECTION_CONFIDENCE_THRESHOLD:
                        center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
                        bounds.append((x1, y1, x2, y2))
                        centers.append(center)
                        detections.append(Detection(center))
                        frame = cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), Color.RED, 3)

            tracked_objects = self.tracker.update(detections)
            tmp_active = {}
            for tracked_object in tracked_objects:
                last_detection = tracked_object.last_detection
                if last_detection in detections:
                    _id = tracked_object.id
                    det_index = detections.index(tracked_object.last_detection)
                    if _id in self.active_potato_objects:
                        tmp_active[_id] = self.active_potato_objects[_id]
                    else:
                        tmp_active[_id] = PotatoObject(_id)
                    tmp_active[_id].bounds = bounds[det_index]
                    tmp_active[_id].center = centers[det_index]
            self.active_potato_objects = tmp_active

            first_stage_scanning_objects, second_stage_scanning_objects, third_stage_scanning_objects = [], [], []

            stage_switch = {
                0: [
                    "first_section_scanned",
                    "first_section_middle",
                    first_stage_scanning_objects,
                    Messages.FIRST_STAGE_ADDED,
                ],
                1: [
                    "second_section_scanned",
                    "second_section_middle",
                    second_stage_scanning_objects,
                    Messages.SECOND_STAGE_ADDED,
                ],
                2: [
                    "third_section_scanned",
                    "third_section_middle",
                    third_stage_scanning_objects,
                    Messages.THIRD_STAGE_ADDED,
                ],
            }

            for _id, potato_obj in self.active_potato_objects.items():
                for stage in range(0, 3):
                    if (
                        not potato_obj.__getattribute__(stage_switch[stage][0])
                        and abs(potato_obj.center[0] - self.__getattribute__(stage_switch[stage][1]))
                        < MainConfigs.SCANNING_WINDOW
                        and _id not in self.potato_defects_queue
                    ):
                        stage_switch[stage][2].append(_id)
                        text_browser.append(f"{_id} {stage_switch[stage][3]}")
                        break

            stage_switch = {
                0: [first_stage_scanning_objects, Messages.FIRST_STAGE_SCANNED, "first_section_scanned"],
                1: [second_stage_scanning_objects, Messages.SECOND_STAGE_SCANNED, "second_section_scanned"],
                2: [third_stage_scanning_objects, Messages.THIRD_STAGE_SCANNED, "third_section_scanned"],
            }

            for stage in range(0, 3):
                for _id in stage_switch[stage][0]:
                    potato_obj = self.active_potato_objects[_id]
                    x0, y0, x1, y1 = potato_obj.bounds
                    sub_img = frame[int(y0) : int(y1), int(x0) : int(x1)]
                    res = self.defects_detector(sub_img, verbose=False)
                    for damage_box in res[0].boxes.data:
                        if damage_box[-2] > MainConfigs.DEFECTS_DETECTION_CONFIDENCE_THRESHOLD:
                            self.potato_defects_queue.append(_id)  # [_id] = (time.time(), stage)
                            self.potato_timing_queue.append((time.time(), stage))
                            text_browser.append(f"{_id} {Messages.APPEND_DAMAGED_POTATOES}")
                            break
                    potato_obj.__setattr__(stage_switch[stage][2], True)
                    text_browser.append(f"{_id} {stage_switch[stage][1]}")

            draw_points(frame, tracked_objects, text_size=8, text_color=Color.RED, color=Color.RED)
        return frame
