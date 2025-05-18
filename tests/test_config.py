"""
Configuration for integration tests
"""

import time

class TestConfig:
    """Configuration for test cases"""
    def __init__(self, video_path, expected_potatoes, expected_defects, max_frames=1000, test_type="all"):
        self.video_path = video_path
        self.expected_potatoes = expected_potatoes
        self.expected_defects = expected_defects
        self.max_frames = max_frames
        self.test_type = test_type  # "all", "total", or "defects"

    def tearDown(self):
        if hasattr(self, 'camera'):
            self.camera.stop_stream()
            del self.camera
        if hasattr(self, 'tracker'):
            del self.tracker
        import gc
        gc.collect()
        time.sleep(0.2)

# Test cases configuration
TEST_CASES = [

    TestConfig(
        video_path="video/14-31.avi",
        expected_potatoes=3,
        expected_defects=3,
        max_frames=1000,
        test_type="all"
    ),

    TestConfig(
        video_path="video/Trim.avi",
        expected_potatoes=10,
        expected_defects= None ,
        max_frames=1000,
        test_type="defects"
    ),

] 