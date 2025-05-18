import time
# from collections import OrderedDict
from typing import List

import cv2
import numpy as np
import torch
from norfair import Detection, Tracker, draw_points
from ultralytics import YOLO
from torchvision import models as torch_models
from torch import nn

from configs import MainConfigs
from constants import Color, Messages
from potato_object import PotatoObject
from utils import init_frames, save_frame
from logger_config import logger
from torchvision import transforms
from PIL import Image


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])


class PotatoTracker:
    def __init__(self, frame_size, potato_defects_queue: List, potato_timing_queue: List):
        self.potato_detector = YOLO(MainConfigs.POTATO_DETECTOR_PATH)
        self.defected_potato_classifier = torch_models.mobilenet_v2(pretrained=False)
        self.defected_potato_classifier.classifier[1] = nn.Linear(self.defected_potato_classifier.last_channel, MainConfigs.NUM_CLASSES)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.defected_potato_classifier.load_state_dict(torch.load(MainConfigs.DEFECTS_CLASSIFIER_PATH, map_location=device))
        self.defected_potato_classifier.eval()
        self.tracker = Tracker(distance_function="euclidean", distance_threshold=150)
        self.active_potato_objects = {}
        frame_width = frame_size[1]
        self.first_section_middle = int(MainConfigs.FIRST_STAGE_MIDDLE_POINT * frame_width)
        self.second_section_middle = int(MainConfigs.SECOND_STAGE_MIDDLE_POINT * frame_width)
        self.third_section_middle = int(MainConfigs.THIRD_STAGE_MIDDLE_POINT * frame_width)
        self.potato_defects_queue = potato_defects_queue
        self.potato_timing_queue = potato_timing_queue
        if MainConfigs.SAVE_FRAMES:
            self.frame_path  = init_frames()
        logger.info("-------------------PotatoTracker initialized")
        logger.debug(f"Frame size: {frame_size}")
        logger.debug(f"First section middle: {self.first_section_middle}")
        logger.debug(f"Second section middle: {self.second_section_middle}")
        logger.debug(f"Third section middle: {self.third_section_middle}")
        self.total_defects_detected = 0

    def cleanup(self):
        """Clean up resources and reset state"""
        # Clear active objects
        self.active_potato_objects.clear()
        # Reset defect counter
        self.total_defects_detected = 0
        # Clear queues
        self.potato_defects_queue.clear()
        self.potato_timing_queue.clear()
        # Reset tracker
        self.tracker = Tracker(distance_function="euclidean", distance_threshold=150)
        # Reinitialize YOLO models
        self.potato_detector = YOLO(MainConfigs.POTATO_DETECTOR_PATH)
        self.defects_detector = YOLO(MainConfigs.DEFECTS_DETECTOR_PATH)
        # Force garbage collection
        import gc
        gc.collect()
        logger.info("PotatoTracker resources cleaned up and models reinitialized")

    def get_total_objects_count(self):
        return self.tracker.total_object_count

    def log_final_statistics(self, total_counter):
        """Log final statistics about processed potatoes and detected defects"""
        logger.info("           Final Statistics")
        logger.info(f"Total potatoes processed: {total_counter}")
        logger.info(f"Total defects detected: {self.total_defects_detected}")
        logger.info(f"Defect rate: {(self.total_defects_detected/total_counter*100 if total_counter > 0 else 0):.2f}%")
        logger.info("       ")

    def update(self, frame, text_browser):
        if frame is not None:
            if MainConfigs.SAVE_FRAMES:
                save_frame(self.frame_path,frame)
            logger.debug("Starting object detection")
            results = self.potato_detector(frame, verbose=False)
            detections = []
            centers = []
            bounds = []
            detected_count = 0
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
                        detected_count += 1
                        logger.debug(f"Detected potato with confidence {score:.2f} at position {center}")
            
            logger.debug(f"Detected {detected_count} potatoes in current frame")
            logger.debug(f"Total objects before tracking: {len(detections)}")

            tracked_objects = self.tracker.update(detections)
            logger.debug(f"Total objects after tracking: {len(tracked_objects)}")
            
            tmp_active = {}
            for tracked_object in tracked_objects:
                last_detection = tracked_object.last_detection
                if last_detection in detections:
                    _id = tracked_object.id
                    det_index = detections.index(tracked_object.last_detection)
                    if _id in self.active_potato_objects:
                        tmp_active[_id] = self.active_potato_objects[_id]
                        logger.debug(f"Updating existing potato object {_id}")
                    else:
                        tmp_active[_id] = PotatoObject(_id)
                        logger.debug(f"Created new potato object {_id}")
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
                        logger.debug(f"Potato {_id} entered stage {stage + 1}")
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
                    logger.debug(f"Scanning potato {_id} for defects in stage {stage + 1}")
                    sub_img = Image.fromarray(sub_img).convert("RGB")
                    sub_img = transform(sub_img).unsqueeze(0)
                    with torch.no_grad():
                        outputs = self.defected_potato_classifier(sub_img)
                        pred_class = outputs.argmax(dim=1).item()
                    if pred_class == 0:
                        self.potato_defects_queue.append(_id)
                        self.potato_timing_queue.append((time.time(), stage))
                        text_browser.append(f"{_id} {Messages.APPEND_DAMAGED_POTATOES}")
                        logger.info(f"Defect detected in potato {_id} at stage {stage + 1}")
                        self.total_defects_detected += 1
                    potato_obj.__setattr__(stage_switch[stage][2], True)
                    text_browser.append(f"{_id} {stage_switch[stage][1]}")
                    logger.debug(f"Potato {_id} completed stage {stage + 1} scanning")

            draw_points(frame, tracked_objects, text_size=8, text_color=Color.RED, color=Color.RED)
        return frame
