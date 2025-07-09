import os
import time
import logging
import unittest
import sys
import re
import cv2
import numpy as np

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs import MainConfigs
from main_types import CameraType
from camera import AVICamera
from tracker import PotatoTracker
from logger_config import logger
from tests.test_config import TestConfig, TEST_CASES


class MockTextBrowser:
    """Mock class to handle tracker's text browser operations"""

    def __init__(self):
        self.messages = []

    def append(self, message):
        self.messages.append(message)
        logger.info(f"Tracker message: {message}")


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure test settings
        MainConfigs.PREFERRED_CAMERA_DEVICE = CameraType.AVI_CAMERA
        MainConfigs.CAMERA_AUTOSTART = True
        MainConfigs.AVI_CAMERA_LOOP = False
        MainConfigs.LOG_LEVEL = "INFO"

        # Create test log file
        cls.test_log_file = "test_integration.log"
        file_handler = logging.FileHandler(cls.test_log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def setUp(self):
        # Clear log file before each test
        with open(self.test_log_file, "w") as f:
            f.write("")

        # Initialize empty queues for potato tracking
        self.potato_defects_queue = []
        self.potato_timing_queue = []

        # Create mock text browser
        self.text_browser = MockTextBrowser()

    def run_test_case(self, test_config):
        """Run a single test case with the given configuration"""
        # Convert video path to absolute path
        video_path = os.path.abspath(test_config.video_path)

        # Verify video file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        # Verify model files exist
        if not os.path.exists(MainConfigs.POTATO_DETECTOR_PATH):
            raise FileNotFoundError(
                f"Potato detector model not found at: {MainConfigs.POTATO_DETECTOR_PATH}"
            )
        if not os.path.exists(MainConfigs.DEFECTS_DETECTOR_PATH):
            raise FileNotFoundError(
                f"Defects detector model not found at: {MainConfigs.DEFECTS_DETECTOR_PATH}"
            )

        # Set video path for this test
        MainConfigs.AVI_CAMERA_PATH = video_path

        logger.info(f"Running test case with video: {video_path}")
        logger.info(f"Test type: {test_config.test_type}")
        logger.info(f"Expected potatoes: {test_config.expected_potatoes}")
        logger.info(f"Expected defects: {test_config.expected_defects}")

        # Initialize camera and tracker with the current video path
        self.camera = AVICamera(avi_path=video_path)
        self.tracker = PotatoTracker(
            MainConfigs.CAMERA_FRAME_SHAPE,
            self.potato_defects_queue,
            self.potato_timing_queue,
        )

        # Start camera stream
        if self.camera.device_is_activated():
            self.camera.start_stream()
            logger.info("Camera stream started")
            # Log camera info
            logger.info(f"Camera initialized with path: {self.camera.cam_descriptor}")
            logger.info(f"Frame count: {self.camera.frame_count}")
            logger.info(f"FPS: {self.camera.fps}")
        else:
            raise RuntimeError("Failed to initialize camera")

        frame_count = 0

        while frame_count < test_config.max_frames:
            frame = self.camera.get_next_frame()
            if frame is None:
                logger.info("End of video reached")
                break

            # Process frame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed_frame = self.tracker.update(frame, self.text_browser)
            frame_count += 1

            # Log progress every 50 frames
            if frame_count % 50 == 0:
                logger.info(f"Processed {frame_count} frames")
                # Log frame shape and type
                logger.info(f"Frame shape: {frame.shape}, type: {frame.dtype}")
                # Log detection results
                logger.info(
                    f"Current unique potatoes: {self.tracker.get_total_objects_count()}"
                )
                logger.info(
                    f"Current total defects: {self.tracker.total_defects_detected}"
                )

        # Stop camera stream
        self.camera.stop_stream()
        logger.info(f"Processing complete. Total frames processed: {frame_count}")

        # Get final statistics from tracker
        total_potatoes = self.tracker.get_total_objects_count()
        total_defects = self.tracker.total_defects_detected
        total_frames = frame_count

        # Log the results
        logger.info(f"Test Results:")
        logger.info(f"Total frames processed: {total_frames}")
        logger.info(f"Total unique potatoes detected: {total_potatoes}")
        logger.info(f"Total defects detected: {total_defects}")

        # Verify results based on test type
        self.assertGreater(frame_count, 0, "No frames were read from video")

        if (
            test_config.test_type in ["total", "all"]
            and test_config.expected_potatoes is not None
        ):
            self.assertEqual(
                total_potatoes,
                test_config.expected_potatoes,
                f"Expected {test_config.expected_potatoes} potatoes, got {total_potatoes}",
            )

        if (
            test_config.test_type in ["defects", "all"]
            and test_config.expected_defects is not None
        ):
            self.assertEqual(
                total_defects,
                test_config.expected_defects,
                f"Expected {test_config.expected_defects} defects, got {total_defects}",
            )

        # Calculate and verify defect rate only if we're checking both counts
        if (
            total_potatoes > 0
            and test_config.expected_potatoes is not None
            and test_config.expected_defects is not None
        ):
            defect_rate = (total_defects / total_potatoes) * 100
            logger.info(f"Defect rate: {defect_rate:.2f}%")
            self.assertGreaterEqual(defect_rate, 0, "Invalid defect rate")
            self.assertLessEqual(defect_rate, 100, "Invalid defect rate")

    def test_potato_detection(self):
        """Run all test cases"""
        for test_config in TEST_CASES:
            with self.subTest(
                video=test_config.video_path, test_type=test_config.test_type
            ):
                self.run_test_case(test_config)

    def tearDown(self):
        # Clean up
        if hasattr(self, "camera"):
            self.camera.stop_stream()
            del self.camera
            self.camera = None
        if hasattr(self, "tracker"):
            self.tracker.cleanup()  # Call cleanup before deletion
            del self.tracker
            self.tracker = None
        import gc

        gc.collect()
        try:
            import cv2

            cv2.destroyAllWindows()
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        # Remove test log file
        if os.path.exists(cls.test_log_file):
            os.remove(cls.test_log_file)


if __name__ == "__main__":
    unittest.main()
