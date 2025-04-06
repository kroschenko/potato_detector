from ultralytics import YOLO


class YOLODetector:
    def __init__(self, str_to_model):
        self.model = YOLO(str_to_model)

    def detect_objects(self, img):
        return self.model(img)
