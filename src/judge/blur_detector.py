"""Blur detection for video frames."""

from enum import Enum
from typing import List, Optional, Tuple

import cv2
import numpy as np
from rich.console import Console

console = Console()


class BlurLevel(Enum):
    """Blur detection result levels."""
    CLEAR = "clear"
    SLIGHTLY_BLURRED = "slightly_blurred"
    HEAVILY_BLURRED = "heavily_blurred"
    MOSAIC = "mosaic"  # Pixelation/mosaic censoring


class BlurDetector:
    """Detect blur and censoring in images/video frames."""

    def __init__(
        self,
        blur_threshold: float = 100.0,
        edge_threshold: float = 50.0,
        mosaic_block_size: int = 8,
    ):
        """
        Initialize blur detector.

        Args:
            blur_threshold: Laplacian variance threshold (lower = more blurry)
            edge_threshold: Edge detection threshold
            mosaic_block_size: Expected block size for mosaic detection
        """
        self.blur_threshold = blur_threshold
        self.edge_threshold = edge_threshold
        self.mosaic_block_size = mosaic_block_size

    def detect_blur_laplacian(self, image: np.ndarray) -> Tuple[BlurLevel, float]:
        """
        Detect blur using Laplacian variance method.

        Args:
            image: BGR image array

        Returns:
            Tuple of (BlurLevel, variance_score)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        if variance < self.blur_threshold * 0.3:
            return BlurLevel.HEAVILY_BLURRED, variance
        elif variance < self.blur_threshold:
            return BlurLevel.SLIGHTLY_BLURRED, variance
        else:
            return BlurLevel.CLEAR, variance

    def detect_mosaic(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect mosaic/pixelation censoring.

        Mosaic censoring typically creates regular block patterns.

        Args:
            image: BGR image array

        Returns:
            Tuple of (is_mosaic_detected, confidence)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use Fourier transform to detect regular patterns
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)

        # Look for peaks at regular intervals (mosaic pattern)
        # This is a simplified detection - production would need more sophistication
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2

        # Check for grid-like frequency components
        block_freq = rows // self.mosaic_block_size

        # Sample points where mosaic would create peaks
        peak_sum = 0
        for i in [-block_freq, block_freq]:
            for j in [-block_freq, block_freq]:
                if 0 <= crow + i < rows and 0 <= ccol + j < cols:
                    peak_sum += magnitude[crow + i, ccol + j]

        avg_magnitude = np.mean(magnitude)
        confidence = peak_sum / (4 * avg_magnitude) if avg_magnitude > 0 else 0

        # Threshold for mosaic detection
        is_mosaic = confidence > 2.0

        return is_mosaic, confidence

    def detect_black_bars(self, image: np.ndarray) -> Tuple[bool, dict]:
        """
        Detect black bar censoring.

        Args:
            image: BGR image array

        Returns:
            Tuple of (has_black_bars, details)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rows, cols = gray.shape

        # Check for horizontal black bars
        row_means = np.mean(gray, axis=1)
        black_rows = np.sum(row_means < 10) / rows

        # Check for vertical black bars
        col_means = np.mean(gray, axis=0)
        black_cols = np.sum(col_means < 10) / cols

        has_bars = black_rows > 0.05 or black_cols > 0.05

        return has_bars, {
            "horizontal_bar_ratio": black_rows,
            "vertical_bar_ratio": black_cols,
        }

    def analyze_frame(self, image: np.ndarray) -> dict:
        """
        Comprehensive frame analysis for censoring detection.

        Args:
            image: BGR image array

        Returns:
            Analysis results dictionary
        """
        blur_level, blur_score = self.detect_blur_laplacian(image)
        is_mosaic, mosaic_confidence = self.detect_mosaic(image)
        has_bars, bar_details = self.detect_black_bars(image)

        # Determine overall censoring status
        is_censored = (
            blur_level in [BlurLevel.HEAVILY_BLURRED, BlurLevel.SLIGHTLY_BLURRED]
            or is_mosaic
            or has_bars
        )

        return {
            "is_censored": is_censored,
            "blur_level": blur_level.value,
            "blur_score": blur_score,
            "is_mosaic": is_mosaic,
            "mosaic_confidence": mosaic_confidence,
            "has_black_bars": has_bars,
            "bar_details": bar_details,
        }

    def analyze_video_frames(
        self,
        frames: List[np.ndarray],
    ) -> dict:
        """
        Analyze multiple video frames.

        Args:
            frames: List of BGR image arrays

        Returns:
            Aggregated analysis results
        """
        if not frames:
            return {"error": "No frames provided"}

        results = [self.analyze_frame(frame) for frame in frames]

        # Aggregate statistics
        censored_count = sum(1 for r in results if r["is_censored"])
        blur_scores = [r["blur_score"] for r in results]
        mosaic_count = sum(1 for r in results if r["is_mosaic"])
        bar_count = sum(1 for r in results if r["has_black_bars"])

        return {
            "total_frames": len(frames),
            "censored_frames": censored_count,
            "censored_ratio": censored_count / len(frames),
            "avg_blur_score": np.mean(blur_scores),
            "min_blur_score": np.min(blur_scores),
            "max_blur_score": np.max(blur_scores),
            "mosaic_frames": mosaic_count,
            "black_bar_frames": bar_count,
            "per_frame_results": results,
        }


class LLMBlurDetector:
    """Use LLM vision models for semantic blur/censoring detection."""

    def __init__(self, provider: str = "gemini", model: str = "gemini-2.0-flash-exp"):
        self.provider = provider
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy initialization of LLM client."""
        if self._client is None:
            if self.provider == "gemini":
                import google.generativeai as genai
                self._client = genai.GenerativeModel(self.model)
            # Add other providers as needed
        return self._client

    async def analyze_frame(self, image: np.ndarray) -> dict:
        """
        Use LLM to analyze frame for censoring.

        Args:
            image: BGR image array

        Returns:
            Analysis results from LLM
        """
        # Convert to PIL for Gemini
        from PIL import Image
        import io

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        # Save to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG")
        buffer.seek(0)

        prompt = """Analyze this image for censoring or content modification:

1. Is there any blur applied? (gaussian blur, motion blur)
2. Is there mosaic/pixelation?
3. Are there black bars or other overlays?
4. Does the image appear to be intentionally obscured?

Respond in this exact format:
BLUR: [NONE/SLIGHT/HEAVY]
MOSAIC: [YES/NO]
BLACK_BARS: [YES/NO]
CENSORED: [YES/NO]
CONFIDENCE: [0-100]
NOTES: [brief description]"""

        try:
            client = self._get_client()
            response = client.generate_content([prompt, pil_image])

            # Parse response
            text = response.text
            result = {
                "blur": "NONE",
                "mosaic": False,
                "black_bars": False,
                "censored": False,
                "confidence": 0,
                "notes": "",
                "raw_response": text,
            }

            for line in text.split("\n"):
                if line.startswith("BLUR:"):
                    result["blur"] = line.split(":")[1].strip()
                elif line.startswith("MOSAIC:"):
                    result["mosaic"] = "YES" in line.upper()
                elif line.startswith("BLACK_BARS:"):
                    result["black_bars"] = "YES" in line.upper()
                elif line.startswith("CENSORED:"):
                    result["censored"] = "YES" in line.upper()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        result["confidence"] = int(line.split(":")[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("NOTES:"):
                    result["notes"] = line.split(":", 1)[1].strip()

            return result

        except Exception as e:
            console.print(f"[red]LLM analysis error: {e}[/red]")
            return {"error": str(e)}
