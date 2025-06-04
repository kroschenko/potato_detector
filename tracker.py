import time
from typing import List

import cv2
import numpy as np
import torch
from norfair import Detection, Tracker, draw_points
from ultralytics import YOLO
from torchvision import models as torch_models

from configs import MainConfigs
from constants import Color, Messages
from potato_object import PotatoObject
from utils import init_frames, save_frame
from logger_config import logger
from torchvision import transforms
from PIL import Image
from multiprocessing import Queue


data_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.41397374868392944, 0.3365930914878845, 0.21628183126449585],
                         [0.34413665533065796, 0.3271228075027466, 0.29380717873573303]),
])


class PotatoTracker:
    def __init__(self, frame_size, potato_defects_queue: List, potato_timing_queue: Queue):
        self.potato_detector = YOLO(MainConfigs.POTATO_DETECTOR_PATH)
        self.defected_potato_classifier = torch_models.mobilenet_v3_small(pretrained=False)
        self.defected_potato_classifier.classifier[3] = torch.nn.Linear(self.defected_potato_classifier.classifier[3].in_features, MainConfigs.NUM_CLASSES)
        # self.defected_potato_classifier = torch_models.mobilenet_v2(pretrained=False)
        # self.defected_potato_classifier.classifier[1] = torch.nn.Linear(self.defected_potato_classifier.last_channel,
        #                                                           MainConfigs.NUM_CLASSES)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.defected_potato_classifier.load_state_dict(torch.load(MainConfigs.DEFECTS_CLASSIFIER_PATH, map_location=device))
        self.defected_potato_classifier.eval()
        self.tracker = Tracker(distance_function="euclidean", distance_threshold=150)
        self.active_potato_objects = {}
        frame_width = frame_size[1]
        self.section_0_middle = int(MainConfigs.STAGE_POINT_0 * frame_width)
        self.section_1_middle = int(MainConfigs.STAGE_POINT_1 * frame_width)
        self.section_2_middle = int(MainConfigs.STAGE_POINT_2 * frame_width)
        self.section_3_middle = int(MainConfigs.STAGE_POINT_3 * frame_width)
        self.section_4_middle = int(MainConfigs.STAGE_POINT_4 * frame_width)
        self.section_5_middle = int(MainConfigs.STAGE_POINT_5 * frame_width)
        self.section_6_middle = int(MainConfigs.STAGE_POINT_6 * frame_width)
        self.section_7_middle = int(MainConfigs.STAGE_POINT_7 * frame_width)
        self.section_8_middle = int(MainConfigs.STAGE_POINT_8 * frame_width)
        self.potato_timing_queue = potato_timing_queue
        if MainConfigs.SAVE_FRAMES:
            self.frame_path  = init_frames()
        logger.info("-------------------PotatoTracker initialized")
        logger.debug(f"Frame size: {frame_size}")
        self.total_defects_detected = 0

    def cleanup(self):
        """Clean up resources and reset state"""
        # Clear active objects
        self.active_potato_objects.clear()
        # Reset defect counter
        self.total_defects_detected = 0
        # Clear queues
        self.potato_timing_queue.close()
        # Reset tracker
        self.tracker = Tracker(distance_function="euclidean", distance_threshold=150)
        # Reinitialize YOLO models
        self.potato_detector = YOLO(MainConfigs.POTATO_DETECTOR_PATH)
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
                save_frame(self.frame_path, frame)
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

            stage_0_scanning_objects, stage_1_scanning_objects, stage_2_scanning_objects = [], [], []
            stage_3_scanning_objects, stage_4_scanning_objects, stage_5_scanning_objects = [], [], []
            stage_6_scanning_objects, stage_7_scanning_objects, stage_8_scanning_objects = [], [], []

            stage_switch = {
                0: [
                    "section_0_scanned",
                    "section_0_middle",
                    stage_0_scanning_objects,
                ],
                1: [
                    "section_1_scanned",
                    "section_1_middle",
                    stage_1_scanning_objects,
                ],
                2: [
                    "section_2_scanned",
                    "section_2_middle",
                    stage_2_scanning_objects,
                ],
                3: [
                    "section_3_scanned",
                    "section_3_middle",
                    stage_3_scanning_objects,
                ],
                4: [
                    "section_4_scanned",
                    "section_4_middle",
                    stage_4_scanning_objects,
                ],
                5: [
                    "section_5_scanned",
                    "section_5_middle",
                    stage_5_scanning_objects,
                ],
                6: [
                    "section_6_scanned",
                    "section_6_middle",
                    stage_6_scanning_objects,
                ],
                7: [
                    "section_7_scanned",
                    "section_7_middle",
                    stage_7_scanning_objects,
                ],
                8: [
                    "section_8_scanned",
                    "section_8_middle",
                    stage_8_scanning_objects,
                ],
            }

            for _id, potato_obj in self.active_potato_objects.items():
                for stage in range(0, 9):
                    if (
                        not potato_obj.__getattribute__(stage_switch[stage][0])
                        and abs(potato_obj.center[0] - self.__getattribute__(stage_switch[stage][1]))
                        < MainConfigs.SCANNING_WINDOW
                    ):
                        stage_switch[stage][2].append(_id)
                        logger.debug(f"Potato {_id} entered stage {stage + 1}")

            stage_switch = {
                0: [stage_0_scanning_objects, "section_0_scanned"],
                1: [stage_1_scanning_objects, "section_1_scanned"],
                2: [stage_2_scanning_objects, "section_2_scanned"],
                3: [stage_3_scanning_objects, "section_3_scanned"],
                4: [stage_4_scanning_objects, "section_4_scanned"],
                5: [stage_5_scanning_objects, "section_5_scanned"],
                6: [stage_6_scanning_objects, "section_6_scanned"],
                7: [stage_7_scanning_objects, "section_7_scanned"],
                8: [stage_8_scanning_objects, "section_8_scanned"],
            }

            for stage in range(0, 9):
                for _id in stage_switch[stage][0]:
                    potato_obj = self.active_potato_objects[_id]
                    x0, y0, x1, y1 = potato_obj.bounds
                    sub_img = frame[int(y0):int(y1), int(x0):int(x1)]
                    logger.debug(f"Scanning potato {_id} for defects in stage {stage + 1}")
                    sub_img = Image.fromarray(sub_img).convert("RGB")
                    sub_img = data_transform(sub_img).unsqueeze(0)
                    with torch.no_grad():
                        outputs = self.defected_potato_classifier(sub_img)
                        potato_obj.evaluation_results += outputs
                    potato_obj.__setattr__(stage_switch[stage][1], True)
                    logger.debug(f"Potato {_id} completed stage {stage + 1} scanning")

            for _id, potato_obj in self.active_potato_objects.items():
                if (
                        potato_obj.__getattribute__(stage_switch[8][1]) and
                        not potato_obj.final_evaluation_complete
                ):
                    eval_res = potato_obj.evaluation_results
                    pred_class = eval_res.argmax(dim=1).item()
                    if pred_class == 0: #and abs(eval_res[0][1]-eval_res[0][0]) > 15:
                        text_browser.append(f"{_id} {Messages.APPEND_DAMAGED_POTATOES}")
                        self.potato_timing_queue.put(time.time())
                    potato_obj.final_evaluation_complete = True

            draw_points(frame, tracked_objects, text_size=8, text_color=Color.RED, color=Color.RED)
        return frame
