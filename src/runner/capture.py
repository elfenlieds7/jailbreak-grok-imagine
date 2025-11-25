"""Screenshot and video capture management."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import Page
from rich.console import Console

console = Console()


class CaptureManager:
    """Manage screenshots and video captures."""

    def __init__(
        self,
        screenshots_dir: str = "output/screenshots",
        videos_dir: str = "output/videos",
    ):
        self.screenshots_dir = Path(screenshots_dir)
        self.videos_dir = Path(videos_dir)

        # Create directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)

    def get_screenshot_path(self, test_id: str, suffix: str = "") -> str:
        """Generate screenshot path for a test."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_id}_{timestamp}{suffix}.png"
        return str(self.screenshots_dir / filename)

    def get_video_path(self, test_id: str) -> str:
        """Generate video path for a test."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_id}_{timestamp}.mp4"
        return str(self.videos_dir / filename)

    async def capture_screenshot(
        self,
        page: Page,
        test_id: str,
        suffix: str = "",
        full_page: bool = False,
    ) -> str:
        """
        Capture screenshot of current page.

        Args:
            page: Playwright page
            test_id: Test identifier
            suffix: Optional suffix for filename
            full_page: Capture full scrollable page

        Returns:
            Path to saved screenshot
        """
        path = self.get_screenshot_path(test_id, suffix)
        await page.screenshot(path=path, full_page=full_page)
        console.print(f"[dim]Screenshot saved: {path}[/dim]")
        return path

    async def capture_element_screenshot(
        self,
        page: Page,
        selector: str,
        test_id: str,
        suffix: str = "",
    ) -> Optional[str]:
        """
        Capture screenshot of specific element.

        Args:
            page: Playwright page
            selector: CSS selector for element
            test_id: Test identifier
            suffix: Optional suffix for filename

        Returns:
            Path to saved screenshot or None if element not found
        """
        element = await page.query_selector(selector)
        if element:
            path = self.get_screenshot_path(test_id, suffix)
            await element.screenshot(path=path)
            console.print(f"[dim]Element screenshot saved: {path}[/dim]")
            return path
        return None

    async def download_video(
        self,
        page: Page,
        video_url: str,
        test_id: str,
    ) -> Optional[str]:
        """
        Download video from URL.

        Args:
            page: Playwright page (for request context)
            video_url: URL of video to download
            test_id: Test identifier

        Returns:
            Path to saved video or None on failure
        """
        try:
            path = self.get_video_path(test_id)
            response = await page.request.get(video_url)

            if response.ok:
                content = await response.body()
                with open(path, "wb") as f:
                    f.write(content)
                console.print(f"[green]Video saved: {path}[/green]")
                return path
            else:
                console.print(f"[red]Failed to download video: {response.status}[/red]")
                return None

        except Exception as e:
            console.print(f"[red]Error downloading video: {e}[/red]")
            return None

    def list_screenshots(self, test_id: Optional[str] = None) -> list:
        """List all screenshots, optionally filtered by test_id."""
        pattern = f"{test_id}_*.png" if test_id else "*.png"
        return sorted(self.screenshots_dir.glob(pattern))

    def list_videos(self, test_id: Optional[str] = None) -> list:
        """List all videos, optionally filtered by test_id."""
        pattern = f"{test_id}_*.mp4" if test_id else "*.mp4"
        return sorted(self.videos_dir.glob(pattern))
