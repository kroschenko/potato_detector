from datetime import datetime
import os
import cv2
from configs import MainConfigs
from logger_config import logger


def init_frames():
    # Create nested folders: date/start_time (e.g., 2025-04-23/15-30)
    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    time_folder = now.strftime("%H-%M")
    folder_path = os.path.join(MainConfigs.SAVE_PATH, date_folder, time_folder)

    logger.info("Initializing frame storage")
    logger.debug(f"Base path: {MainConfigs.SAVE_PATH}")
    logger.debug(f"Date folder: {date_folder}")
    logger.debug(f"Time folder: {time_folder}")
    logger.debug(f"Full path: {folder_path}")

    os.makedirs(folder_path, exist_ok=True)
    logger.info("Storage directory created/verified")
    return folder_path


def save_frame(folder_path, frame):
    if frame is None:
        logger.error("Attempted to save None frame")
        return

    # Create a unique filename with full datetime (e.g., 2025-04-23_15-30-45-123456.jpg)
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    filename = f"{timestamp_str}.jpg"
    full_path = os.path.join(folder_path, filename)

    # Save the frame
    success = cv2.imwrite(full_path, frame)
    if success:
        logger.debug(f"Frame saved: {filename}")
    else:
        logger.error(f"Failed to save frame: {filename}")


class FrameSaver:
    def __init__(self):
        # Create nested folders: date/start_time (e.g., 2025-04-23/15-30)
        now = datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        time_folder = now.strftime("%H-%M")
        self.folder_path = os.path.join(MainConfigs.SAVE_PATH, date_folder, time_folder)

        logger.info("Initializing new frame saving session")
        logger.debug(f"Base path: {MainConfigs.SAVE_PATH}")
        logger.debug(f"Date folder: {date_folder}")
        logger.debug(f"Time folder: {time_folder}")
        logger.debug(f"Full path: {self.folder_path}")

        os.makedirs(self.folder_path, exist_ok=True)
        logger.info("Storage directory created/verified")
        self.frame_count = 0

    def save_frame(self, frame):
        if frame is None:
            logger.error("Attempted to save None frame")
            return

        # Create a unique filename with full datetime (e.g., 2025-04-23_15-30-45-123456.jpg)
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        filename = f"{timestamp_str}.jpg"
        full_path = os.path.join(self.folder_path, filename)

        # Save the frame
        success = cv2.imwrite(full_path, frame)
        if success:
            self.frame_count += 1
            if self.frame_count % 100 == 0:  # Log every 100 frames
                logger.info(f"Saved {self.frame_count} frames to {self.folder_path}")
        else:
            logger.error(f"Failed to save frame: {filename}")


def jpg_to_avi(input_dir: str, output_path: str, fps: int = 30) -> bool:
    """
    Convert a sequence of JPG images to an AVI video file.

    Args:
        input_dir (str): Directory containing JPG images
        output_path (str): Path where the AVI file will be saved
        fps (int): Frames per second for the output video (default: 30)

    Returns:
        bool: True if conversion was successful, False otherwise
    """
    try:
        # Get list of JPG files and sort them
        jpg_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".jpg")]
        if not jpg_files:
            logger.error(f"No JPG files found in directory: {input_dir}")
            return False

        jpg_files.sort()  # Sort files alphabetically

        # Read first image to get dimensions
        first_image = cv2.imread(os.path.join(input_dir, jpg_files[0]))
        if first_image is None:
            logger.error(f"Failed to read first image: {jpg_files[0]}")
            return False

        height, width = first_image.shape[:2]

        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            logger.error(f"Failed to create video writer for: {output_path}")
            return False

        logger.info(f"Converting {len(jpg_files)} images to AVI video")
        logger.debug(f"Output path: {output_path}")
        logger.debug(f"FPS: {fps}")
        logger.debug(f"Resolution: {width}x{height}")

        # Process each image
        for i, jpg_file in enumerate(jpg_files):
            img_path = os.path.join(input_dir, jpg_file)
            frame = cv2.imread(img_path)

            if frame is None:
                logger.error(f"Failed to read image: {jpg_file}")
                continue

            out.write(frame)

            if (i + 1) % 100 == 0:  # Log progress every 100 frames
                logger.info(f"Processed {i + 1}/{len(jpg_files)} images")

        # Release video writer
        out.release()
        logger.info(f"Successfully created AVI video: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error converting JPG to AVI: {str(e)}")
        return False
