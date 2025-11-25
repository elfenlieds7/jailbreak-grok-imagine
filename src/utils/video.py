"""Video processing utilities."""

import os
from pathlib import Path
from typing import Generator, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


class VideoProcessor:
    """Process videos for frame extraction and analysis."""

    def __init__(self, frame_interval: float = 1.0):
        """
        Initialize video processor.

        Args:
            frame_interval: Extract a frame every N seconds
        """
        self.frame_interval = frame_interval

    def extract_frames(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        max_frames: Optional[int] = None,
    ) -> List[str]:
        """
        Extract frames from video at specified intervals.

        Args:
            video_path: Path to video file
            output_dir: Directory to save frames (optional)
            max_frames: Maximum number of frames to extract

        Returns:
            List of frame file paths (if output_dir) or empty list
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval_frames = int(fps * self.frame_interval)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_paths = []
        frame_count = 0
        saved_count = 0

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval_frames == 0:
                if max_frames and saved_count >= max_frames:
                    break

                if output_dir:
                    frame_path = os.path.join(
                        output_dir, f"frame_{saved_count:04d}.jpg"
                    )
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)

                saved_count += 1

            frame_count += 1

        cap.release()
        return frame_paths

    def iterate_frames(
        self, video_path: str, max_frames: Optional[int] = None
    ) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        Iterate over video frames without saving to disk.

        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to yield

        Yields:
            Tuple of (frame_index, frame_array)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval_frames = int(fps * self.frame_interval)

        frame_count = 0
        yielded_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval_frames == 0:
                if max_frames and yielded_count >= max_frames:
                    break
                yield yielded_count, frame
                yielded_count += 1

            frame_count += 1

        cap.release()

    def get_video_info(self, video_path: str) -> dict:
        """Get video metadata."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration_seconds": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            / cap.get(cv2.CAP_PROP_FPS),
        }
        cap.release()
        return info

    @staticmethod
    def frame_to_pil(frame: np.ndarray) -> Image.Image:
        """Convert OpenCV frame (BGR) to PIL Image (RGB)."""
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    @staticmethod
    def frame_to_base64(frame: np.ndarray) -> str:
        """Convert frame to base64 string for LLM APIs."""
        import base64

        _, buffer = cv2.imencode(".jpg", frame)
        return base64.b64encode(buffer).decode("utf-8")
