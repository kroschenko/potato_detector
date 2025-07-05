import time

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
    def __init__(
            self,
            frame_size,
            count_of_scanning_zones: int,
            potato_timing_top_queue: Queue,
            potato_timing_bottom_queue: Queue
    ) -> None:
        self.potato_detector = YOLO(MainConfigs.POTATO_DETECTOR_PATH)
        self.defected_potato_classifier = torch_models.mobilenet_v3_small(pretrained=False)
        self.defected_potato_classifier.classifier[3] = torch.nn.Linear(self.defected_potato_classifier.classifier[3].in_features, MainConfigs.NUM_CLASSES)

        device = torch.device("cuda" if torch.cuda.is_available() else MainConfigs.DEFAULT_DEVICE)
        self.potato_detector.to(device)
        self.defected_potato_classifier.load_state_dict(torch.load(MainConfigs.DEFECTS_CLASSIFIER_PATH, map_location=device))
        self.defected_potato_classifier.eval()
        self.tracker = Tracker(distance_function="euclidean", distance_threshold=150)
        self.active_potato_objects = {}
        self.count_of_scanning_zones = count_of_scanning_zones
        self.delta = frame_size[1] / float(count_of_scanning_zones + 1)
        self.potato_timing_top_queue = potato_timing_top_queue
        self.potato_timing_bottom_queue = potato_timing_bottom_queue

        if MainConfigs.SAVE_FRAMES:
            self.frame_path = init_frames()
        logger.info("-------------------PotatoTracker initialized")
        logger.debug(f"Frame size: {frame_size}")
        self.total_defects_detected = 0
        self.camera_split_line = frame_size[0] // 2

    def cleanup(self):
        """Clean up resources and reset state"""
        # Clear active objects
        self.active_potato_objects.clear()
        # Reset defect counter
        self.total_defects_detected = 0
        # Clear queues
        self.potato_timing_top_queue.close()
        self.potato_timing_bottom_queue.close()
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
            detections, centers, bounds, camera_ids = [], [], [], []
            detected_count = 0
            for frame_result in results:
                for box in frame_result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    score = box.conf[0].cpu().numpy()
                    if score > MainConfigs.POTATO_DETECTION_CONFIDENCE_THRESHOLD:
                        center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
                        bounds.append((x1, y1, x2, y2))
                        centers.append(center)
                        detections.append(Detection(center))
                        frame = cv2.rectangle(
                            frame,
                            (int(x1), int(y1)), (int(x2), int(y2)),
                            Color.RED,
                            3
                        )
                        camera_id = 1 if center[1] > self.camera_split_line else 0
                        camera_ids.append(camera_id)
                        detected_count += 1
                        logger.debug(f"Detected potato with confidence {score:.2f} at position {center}")
            
            logger.debug(f"Detected {detected_count} potatoes in current frame")
            logger.debug(f"Total objects before tracking: {len(detections)}")

            tracked_objects = self.tracker.update(detections)
            logger.debug(f"Total objects after tracking: {len(tracked_objects)}")
            
            tmp_active = {}
            for tracked_object, camera_id in zip(tracked_objects, camera_ids):
                last_detection = tracked_object.last_detection
                if last_detection in detections:
                    _id = tracked_object.id
                    det_index = detections.index(tracked_object.last_detection)
                    if _id in self.active_potato_objects:
                        tmp_active[_id] = self.active_potato_objects[_id]
                        logger.debug(f"Updating existing potato object {_id}")
                    else:
                        tmp_active[_id] = PotatoObject(_id)
                        tmp_active[_id].camera_id = camera_id
                        logger.debug(f"Created new potato object {_id}")
                    tmp_active[_id].bounds = bounds[det_index]
                    tmp_active[_id].center = centers[det_index]
            self.active_potato_objects = tmp_active

            scanning_objects = [[] for _ in range(self.count_of_scanning_zones)]

            for _id, potato_obj in self.active_potato_objects.items():
                for stage in range(0, self.count_of_scanning_zones):
                    if (
                        stage not in potato_obj.sections_scanned
                        and abs(potato_obj.center[0] - (stage + 1) * self.delta) < MainConfigs.SCANNING_WINDOW
                    ):
                        scanning_objects[stage].append(_id)
                        logger.debug(f"Potato {_id} entered stage {stage + 1}")

            for stage in range(0, self.count_of_scanning_zones):
                for _id in scanning_objects[stage]:
                    potato_obj = self.active_potato_objects[_id]
                    x0, y0, x1, y1 = potato_obj.bounds
                    sub_img = frame[int(y0):int(y1), int(x0):int(x1)]
                    logger.debug(f"Scanning potato {_id} for defects in stage {stage + 1}")
                    sub_img = Image.fromarray(sub_img).convert("RGB")
                    sub_img = data_transform(sub_img)
                    potato_obj.img_patches.append(sub_img)
                    potato_obj.sections_scanned.append(stage)
                    logger.debug(f"Potato {_id} completed stage {stage + 1} scanning")

            for _id, potato_obj in self.active_potato_objects.items():
                if (
                        (self.count_of_scanning_zones - 1) in potato_obj.sections_scanned and
                        not potato_obj.final_evaluation_complete
                ):
                    timing_queue = self.potato_timing_top_queue if potato_obj.camera_id == 0 else self.potato_timing_bottom_queue
                    sub_imgs = torch.stack(potato_obj.img_patches, dim=0)
                    with torch.no_grad():
                        eval_res = self.defected_potato_classifier(sub_imgs).sum(dim=0)
                    pred_class = eval_res.argmax(dim=0).item()
                    if pred_class == 0: #and abs(eval_res[0][1]-eval_res[0][0]) > 15:
                        text_browser.append(f"{_id} {Messages.APPEND_DAMAGED_POTATOES}")
                        timing_queue.put(time.time())
                    potato_obj.final_evaluation_complete = True

            draw_points(
                frame,
                tracked_objects,
                text_size=8,
                text_color=Color.RED,
                color=Color.RED
            )
        return frame
