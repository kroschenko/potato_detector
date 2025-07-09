import cv2
import os
import argparse
from tqdm import tqdm
import re
import logging
import json
from datetime import datetime
import numpy as np


# Configure logging
def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir, f"jpg_to_avi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


logger = setup_logging()


def natural_sort_key(s):
    """Helper function to sort filenames with timestamps naturally."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", s)
    ]


def get_video_codec(codec_name):
    """Get the appropriate fourcc code for the given codec name."""
    codec_map = {
        "xvid": cv2.VideoWriter_fourcc(*"XVID"),
        "mjpg": cv2.VideoWriter_fourcc(*"MJPG"),
        "mp4v": cv2.VideoWriter_fourcc(*"mp4v"),
        "avc1": cv2.VideoWriter_fourcc(*"avc1"),
        "h264": cv2.VideoWriter_fourcc(*"h264"),
    }
    return codec_map.get(codec_name.lower(), cv2.VideoWriter_fourcc(*"XVID"))


def preprocess_frame(frame, resize=None, brightness=0, contrast=1.0):
    """Apply preprocessing to the frame."""
    if resize is not None:
        frame = cv2.resize(frame, resize)

    if brightness != 0 or contrast != 1.0:
        frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)

    return frame


def save_progress(progress_file, current_frame, total_frames):
    """Save conversion progress to a file."""
    progress = {
        "current_frame": current_frame,
        "total_frames": total_frames,
        "timestamp": datetime.now().isoformat(),
    }
    with open(progress_file, "w") as f:
        json.dump(progress, f)


def load_progress(progress_file):
    """Load conversion progress from a file."""
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return json.load(f)
    return None


def verify_video_file(video_path, expected_frames):
    """Verify that the video file was saved correctly and can be read."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, "Failed to open video file for verification"

        # Get video properties
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Read first frame to verify content
        ret, frame = cap.read()
        if not ret or frame is None:
            cap.release()
            return False, "Failed to read first frame during verification"

        cap.release()

        # Check if frame count matches
        if frame_count != expected_frames:
            return (
                False,
                f"Frame count mismatch: expected {expected_frames}, got {frame_count}",
            )

        return (
            True,
            f"Video verified: {frame_count} frames, {width}x{height} resolution",
        )
    except Exception as e:
        return False, f"Verification error: {str(e)}"


def create_video_from_jpgs(
    input_dir,
    output_file,
    start_frame=0,
    num_frames=None,
    fps=30,
    codec="xvid",
    quality=100,
    resume=False,
    resize=None,
    brightness=0,
    contrast=1.0,
):
    """
    Create an AVI video from a sequence of JPG images.

    Args:
        input_dir (str): Directory containing JPG images
        output_file (str): Output AVI file path
        start_frame (int): Starting frame number
        num_frames (int): Number of frames to include (None for all frames)
        fps (int): Frames per second
        codec (str): Video codec to use (xvid, mjpg, mp4v, avc1, h264)
        quality (int): Video quality (0-100)
        resume (bool): Whether to resume from previous progress
        resize (tuple): Target resolution (width, height)
        brightness (int): Brightness adjustment (-255 to 255)
        contrast (float): Contrast adjustment (0.0 to 3.0)
    """
    try:
        # Get all jpg files and sort them by timestamp
        jpg_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".jpg")]
        jpg_files.sort(key=natural_sort_key)

        if not jpg_files:
            raise FileNotFoundError(f"No JPG files found in {input_dir}")

        logger.info(f"Found {len(jpg_files)} JPG files in {input_dir}")

        # Apply frame range
        if num_frames is not None:
            jpg_files = jpg_files[start_frame : start_frame + num_frames]
        else:
            jpg_files = jpg_files[start_frame:]

        if not jpg_files:
            raise ValueError("No frames selected with the given range")

        # Get the first image to determine frame size
        first_frame_path = os.path.join(input_dir, jpg_files[0])
        first_frame = cv2.imread(first_frame_path)
        if first_frame is None:
            raise ValueError(f"Failed to read first frame: {first_frame_path}")

        height, width = first_frame.shape[:2]
        if resize is not None:
            width, height = resize

        # Initialize video writer
        fourcc = get_video_codec(codec)
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

        if not out.isOpened():
            raise ValueError(f"Failed to create video writer for {output_file}")

        # Check for progress file
        progress_file = f"{output_file}.progress"
        current_frame = 0

        if resume:
            progress = load_progress(progress_file)
            if progress:
                current_frame = progress["current_frame"]
                logger.info(f"Resuming from frame {current_frame}")

        # Process frames with progress bar
        logger.info(f"Processing {len(jpg_files)} frames...")
        logger.info(f"Output: {output_file}")
        logger.info(f"Codec: {codec}, FPS: {fps}, Quality: {quality}")
        logger.info(f"Resolution: {width}x{height}")

        processed_frames = 0
        for i, frame_file in enumerate(
            tqdm(jpg_files[current_frame:], desc="Creating video")
        ):
            frame_path = os.path.join(input_dir, frame_file)
            frame = cv2.imread(frame_path)

            if frame is None:
                logger.warning(f"Failed to read frame: {frame_file}")
                continue

            # Apply preprocessing
            frame = preprocess_frame(frame, resize, brightness, contrast)

            # Write frame and verify it was written
            out.write(frame)
            processed_frames += 1

            # Save progress every 100 frames
            if (i + 1) % 100 == 0:
                save_progress(progress_file, i + 1, len(jpg_files))

        # Release video writer
        out.release()

        # Clean up progress file
        if os.path.exists(progress_file):
            os.remove(progress_file)

        # Verify the saved video
        logger.info("Verifying saved video...")
        success, message = verify_video_file(output_file, processed_frames)
        if not success:
            raise ValueError(f"Video verification failed: {message}")

        logger.info(f"Video saved and verified: {output_file}")
        logger.info(f"Total frames processed: {processed_frames}")
        logger.info(f"Video duration: {processed_frames/fps:.2f} seconds")
        logger.info(message)  # Print verification details

    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        # Clean up partial output file if it exists
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
                logger.info(f"Removed incomplete video file: {output_file}")
            except Exception as cleanup_error:
                logger.error(
                    f"Failed to remove incomplete video file: {str(cleanup_error)}"
                )
        raise


def main():
    parser = argparse.ArgumentParser(description="Convert JPG images to AVI video")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="/home/user/frames",
        help="Directory containing JPG images",
    )
    parser.add_argument(
        "--output_file", type=str, default="output.avi", help="Output AVI file path"
    )
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument(
        "--start_frame", type=int, default=0, help="Starting frame number"
    )
    parser.add_argument(
        "--num_frames",
        type=int,
        default=None,
        help="Number of frames to include (None for all frames)",
    )
    parser.add_argument(
        "--codec",
        type=str,
        default="xvid",
        choices=["xvid", "mjpg", "mp4v", "avc1", "h264"],
        help="Video codec to use",
    )
    parser.add_argument(
        "--quality", type=int, default=100, help="Video quality (0-100)"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume from previous progress"
    )
    parser.add_argument(
        "--resize", type=str, default=None, help="Target resolution (width,height)"
    )
    parser.add_argument(
        "--brightness", type=int, default=0, help="Brightness adjustment (-255 to 255)"
    )
    parser.add_argument(
        "--contrast", type=float, default=1.0, help="Contrast adjustment (0.0 to 3.0)"
    )

    args = parser.parse_args()

    # Parse resize argument
    resize = None
    if args.resize:
        try:
            width, height = map(int, args.resize.split(","))
            resize = (width, height)
        except ValueError:
            logger.error("Invalid resize format. Use width,height (e.g., 1920,1080)")
            return

    try:
        create_video_from_jpgs(
            args.input_dir,
            args.output_file,
            args.start_frame,
            args.num_frames,
            args.fps,
            args.codec,
            args.quality,
            args.resume,
            resize,
            args.brightness,
            args.contrast,
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
