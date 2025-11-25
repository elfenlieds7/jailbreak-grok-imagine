"""UI state detection for Grok Imagine results."""

import re
from enum import Enum
from typing import Optional, Tuple

from playwright.async_api import Page
from rich.console import Console

console = Console()


class UIState(Enum):
    """Detected UI states."""
    GENERATED = "generated"      # Video successfully generated
    BLOCKED = "blocked"          # Content blocked by policy
    ERROR = "error"              # Technical error
    LOADING = "loading"          # Still generating
    UNKNOWN = "unknown"          # Cannot determine


class UIDetector:
    """Detect UI state from Grok Imagine page."""

    # Patterns for different states
    BLOCKED_PATTERNS = [
        r"cannot generate",
        r"unable to generate",
        r"can't create",
        r"policy",
        r"inappropriate",
        r"violat",
        r"not allowed",
        r"restricted",
        r"against our guidelines",
        r"content policy",
        r"safety",
    ]

    ERROR_PATTERNS = [
        r"error",
        r"something went wrong",
        r"try again",
        r"failed",
        r"unavailable",
    ]

    LOADING_PATTERNS = [
        r"generating",
        r"creating",
        r"loading",
        r"please wait",
    ]

    SUCCESS_SELECTORS = [
        "video",
        "[data-testid='video-player']",
        "video[src]",
    ]

    def __init__(self):
        pass

    async def detect_state(self, page: Page) -> Tuple[UIState, Optional[str]]:
        """
        Detect current UI state from page.

        Args:
            page: Playwright page

        Returns:
            Tuple of (UIState, detail_message)
        """
        try:
            # Get page content for text analysis
            content = await page.content()
            text_content = await page.inner_text("body")
            text_lower = text_content.lower()

            # Check for video element first (success)
            for selector in self.SUCCESS_SELECTORS:
                video = await page.query_selector(selector)
                if video:
                    video_src = await video.get_attribute("src")
                    if video_src:
                        return UIState.GENERATED, f"Video found: {video_src[:50]}..."

            # Check for blocked messages
            for pattern in self.BLOCKED_PATTERNS:
                if re.search(pattern, text_lower):
                    # Extract the specific message
                    match = re.search(f".{{0,50}}{pattern}.{{0,50}}", text_lower)
                    detail = match.group(0) if match else pattern
                    return UIState.BLOCKED, detail

            # Check for error messages
            for pattern in self.ERROR_PATTERNS:
                if re.search(pattern, text_lower):
                    match = re.search(f".{{0,50}}{pattern}.{{0,50}}", text_lower)
                    detail = match.group(0) if match else pattern
                    return UIState.ERROR, detail

            # Check for loading state
            for pattern in self.LOADING_PATTERNS:
                if re.search(pattern, text_lower):
                    return UIState.LOADING, "Generation in progress"

            return UIState.UNKNOWN, "Could not determine state"

        except Exception as e:
            return UIState.ERROR, f"Detection error: {str(e)}"

    async def wait_for_result(
        self,
        page: Page,
        timeout: int = 120000,
        poll_interval: int = 2000,
    ) -> Tuple[UIState, Optional[str]]:
        """
        Wait for generation to complete and return final state.

        Args:
            page: Playwright page
            timeout: Maximum wait time in ms
            poll_interval: Check interval in ms

        Returns:
            Tuple of (UIState, detail_message)
        """
        import asyncio

        elapsed = 0
        while elapsed < timeout:
            state, detail = await self.detect_state(page)

            if state in [UIState.GENERATED, UIState.BLOCKED, UIState.ERROR]:
                return state, detail

            await asyncio.sleep(poll_interval / 1000)
            elapsed += poll_interval

        return UIState.ERROR, "Timeout waiting for result"

    async def get_video_url(self, page: Page) -> Optional[str]:
        """Extract video URL from page if present."""
        for selector in self.SUCCESS_SELECTORS:
            video = await page.query_selector(selector)
            if video:
                src = await video.get_attribute("src")
                if src:
                    return src
        return None

    async def get_error_message(self, page: Page) -> Optional[str]:
        """Extract error/blocked message from page."""
        try:
            text_content = await page.inner_text("body")
            text_lower = text_content.lower()

            # Look for blocked messages
            for pattern in self.BLOCKED_PATTERNS + self.ERROR_PATTERNS:
                match = re.search(f".{{0,100}}{pattern}.{{0,100}}", text_lower)
                if match:
                    return match.group(0).strip()

            return None
        except Exception:
            return None
