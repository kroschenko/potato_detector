import os
import sys
import cv2
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from configs import TrackerConfigs


class AnnotationService:
    def __init__(self):
        self.cached_shape = None
        self.static_overlay = None
        self.static_overlay_mask = None
        self.enabled = True

    def build_static_overlay(self, height, width):
        overlay = np.zeros((height, width, 3), dtype=np.uint8)
        zone_lines = []
        for stage in range(TrackerConfigs.SCAN_ZONES_COUNT):
            x = int((stage + 1) * (width / (TrackerConfigs.SCAN_ZONES_COUNT + 1)))
            zone_lines.append(np.array([[x, 0], [x, height]], dtype=np.int32).reshape((-1, 1, 2)))
            cv2.putText(overlay, f"Zone {stage + 1}", (x - 30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        if zone_lines:
            cv2.polylines(overlay, zone_lines, False, (0, 255, 0), 3)

        camera_split_line = height // 2
        split_polyline = [np.array([[0, camera_split_line], [width, camera_split_line]], dtype=np.int32).reshape((-1, 1, 2))]
        cv2.polylines(overlay, split_polyline, False, (0, 0, 255), 3)
        cv2.putText(overlay, "Camera Split", (10, camera_split_line - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        gray = cv2.cvtColor(overlay, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
        self.static_overlay = overlay
        self.static_overlay_mask = mask

    def ensure_overlay(self, height, width):
        shape = (height, width)
        if self.cached_shape != shape or self.static_overlay is None or self.static_overlay_mask is None:
            self.build_static_overlay(height, width)
            self.cached_shape = shape

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)

    def is_enabled(self) -> bool:
        return self.enabled

    def annotate_frame(self, frame_rgb, active_objects):
        if not self.enabled:
            return frame_rgb
        height, width = frame_rgb.shape[:2]
        cm_per_px_x = TrackerConfigs.VISIBLE_AREA_WIDTH_CENTIMETERS / TrackerConfigs.FRAME_SIZE[1]
        cm_per_px_y = TrackerConfigs.VISIBLE_AREA_HEIGHT_CENTIMETERS / TrackerConfigs.FRAME_SIZE[0]

        self.ensure_overlay(height, width)
        frame_rgb = cv2.copyTo(self.static_overlay, self.static_overlay_mask, frame_rgb)

        rects_reject = []
        rects_ok = []
        labels = []
        for potato_id, potato_obj in active_objects.items():
            x0, y0, x1, y1 = [int(coord) for coord in potato_obj.bounds]
            rect_pts = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.int32).reshape((-1, 1, 2))
            is_reject = bool(getattr(potato_obj, 'added_to_queue', False))
            if is_reject:
                rects_reject.append(rect_pts)
            else:
                rects_ok.append(rect_pts)
            width_pixels = x1 - x0
            height_pixels = y1 - y0
            width_cm = width_pixels * cm_per_px_x
            height_cm = height_pixels * cm_per_px_y
            decision_text = "REJECT" if is_reject else "OK"
            label_text = f"ID:{potato_id} {width_cm:.1f}x{height_cm:.1f}cm {decision_text}"
            labels.append((label_text, (x0, y0 - 10)))

        if rects_ok:
            cv2.polylines(frame_rgb, rects_ok, True, (255, 255, 0), 3)
        if rects_reject:
            cv2.polylines(frame_rgb, rects_reject, True, (255, 0, 0), 3)

        for text, org in labels:
            cv2.putText(frame_rgb, text, org, cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

        return frame_rgb


