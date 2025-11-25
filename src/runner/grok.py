"""Grok Imagine interaction automation."""

import asyncio
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from rich.console import Console

console = Console()


class GenerationMode(Enum):
    """Grok Imagine generation modes."""
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


class GenerationStatus(Enum):
    """Status of generation attempt."""
    SUCCESS = "success"
    BLOCKED = "blocked"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class GenerationResult:
    """Result of a generation attempt."""
    status: GenerationStatus
    prompt: str
    mode: GenerationMode
    spicy: bool
    video_url: Optional[str] = None
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    generation_time_ms: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class GrokImagine:
    """Interact with Grok Imagine for automated testing."""

    # Selectors (may need updates if X changes their UI)
    SELECTORS = {
        # Main input
        "prompt_input": 'textarea[placeholder*="Ask"], textarea[data-testid="grok-composer-input"]',
        "submit_button": '[data-testid="grok-send-button"], button[aria-label*="Send"]',

        # Mode toggles
        "imagine_tab": '[role="tab"]:has-text("Imagine"), button:has-text("Imagine")',
        "spicy_toggle": '[data-testid="spicy-toggle"], button:has-text("Spicy"), [aria-label*="Spicy"]',

        # Image upload (for image-to-video)
        "image_upload": 'input[type="file"]',

        # Results
        "video_player": 'video, [data-testid="video-player"]',
        "video_download": '[data-testid="download-button"], button:has-text("Download")',

        # Error/blocked indicators
        "error_message": '[data-testid="error-message"], [class*="error"]',
        "blocked_message": ':text("cannot generate"), :text("unable to"), :text("policy"), :text("inappropriate")',

        # Loading states
        "loading": '[data-testid="loading"], [class*="loading"], [class*="spinner"]',
        "generating": ':text("Generating"), :text("Creating")',
    }

    def __init__(self, page: Page, timeout: int = 120000):
        """
        Initialize Grok Imagine automation.

        Args:
            page: Playwright page instance
            timeout: Timeout for generation in milliseconds
        """
        self.page = page
        self.timeout = timeout

    async def navigate_to_imagine(self) -> bool:
        """Navigate to Grok Imagine tab."""
        try:
            await self.page.goto("https://x.com/i/grok", wait_until="networkidle")

            # Look for and click Imagine tab
            imagine_tab = await self.page.query_selector(self.SELECTORS["imagine_tab"])
            if imagine_tab:
                await imagine_tab.click()
                await asyncio.sleep(1)
                return True

            # If no tab found, might already be on Imagine or UI changed
            console.print("[yellow]Imagine tab not found, continuing anyway[/yellow]")
            return True

        except Exception as e:
            console.print(f"[red]Error navigating to Imagine: {e}[/red]")
            return False

    async def set_spicy_mode(self, enabled: bool = True) -> bool:
        """Enable or disable Spicy mode."""
        try:
            spicy_toggle = await self.page.query_selector(self.SELECTORS["spicy_toggle"])
            if spicy_toggle:
                # Check current state
                is_active = await spicy_toggle.get_attribute("aria-pressed")
                current_enabled = is_active == "true"

                if current_enabled != enabled:
                    await spicy_toggle.click()
                    await asyncio.sleep(0.5)
                    console.print(f"[green]Spicy mode: {'enabled' if enabled else 'disabled'}[/green]")

                return True
            else:
                console.print("[yellow]Spicy toggle not found[/yellow]")
                return False

        except Exception as e:
            console.print(f"[red]Error setting spicy mode: {e}[/red]")
            return False

    async def generate_text_to_video(
        self,
        prompt: str,
        spicy: bool = True,
        screenshot_dir: Optional[str] = None,
    ) -> GenerationResult:
        """
        Generate video from text prompt.

        Args:
            prompt: Text prompt for generation
            spicy: Enable spicy mode
            screenshot_dir: Directory to save screenshots

        Returns:
            GenerationResult with status and details
        """
        start_time = datetime.now()

        try:
            # Set spicy mode
            await self.set_spicy_mode(spicy)

            # Enter prompt
            prompt_input = await self.page.wait_for_selector(
                self.SELECTORS["prompt_input"],
                timeout=10000
            )
            await prompt_input.fill(prompt)
            await asyncio.sleep(0.5)

            # Take screenshot before submission
            if screenshot_dir:
                pre_screenshot = os.path.join(screenshot_dir, f"pre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                await self.page.screenshot(path=pre_screenshot)

            # Submit
            submit_btn = await self.page.query_selector(self.SELECTORS["submit_button"])
            if submit_btn:
                await submit_btn.click()
            else:
                # Try pressing Enter
                await prompt_input.press("Enter")

            # Wait for generation
            status, video_url, error_msg = await self._wait_for_result()

            # Calculate generation time
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Take screenshot after result
            screenshot_path = None
            if screenshot_dir:
                screenshot_path = os.path.join(
                    screenshot_dir,
                    f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                await self.page.screenshot(path=screenshot_path)

            return GenerationResult(
                status=status,
                prompt=prompt,
                mode=GenerationMode.TEXT_TO_VIDEO,
                spicy=spicy,
                video_url=video_url,
                screenshot_path=screenshot_path,
                error_message=error_msg,
                generation_time_ms=generation_time,
            )

        except PlaywrightTimeout:
            return GenerationResult(
                status=GenerationStatus.TIMEOUT,
                prompt=prompt,
                mode=GenerationMode.TEXT_TO_VIDEO,
                spicy=spicy,
                error_message="Generation timed out",
            )
        except Exception as e:
            return GenerationResult(
                status=GenerationStatus.ERROR,
                prompt=prompt,
                mode=GenerationMode.TEXT_TO_VIDEO,
                spicy=spicy,
                error_message=str(e),
            )

    async def generate_image_to_video(
        self,
        image_path: str,
        prompt: str,
        screenshot_dir: Optional[str] = None,
    ) -> GenerationResult:
        """
        Generate video from image + prompt.

        Args:
            image_path: Path to input image
            prompt: Text prompt for generation
            screenshot_dir: Directory to save screenshots

        Returns:
            GenerationResult with status and details
        """
        start_time = datetime.now()

        try:
            # Upload image
            file_input = await self.page.query_selector(self.SELECTORS["image_upload"])
            if file_input:
                await file_input.set_input_files(image_path)
                await asyncio.sleep(1)
            else:
                return GenerationResult(
                    status=GenerationStatus.ERROR,
                    prompt=prompt,
                    mode=GenerationMode.IMAGE_TO_VIDEO,
                    spicy=False,
                    error_message="Image upload input not found",
                )

            # Enter prompt
            prompt_input = await self.page.wait_for_selector(
                self.SELECTORS["prompt_input"],
                timeout=10000
            )
            await prompt_input.fill(prompt)
            await asyncio.sleep(0.5)

            # Submit
            submit_btn = await self.page.query_selector(self.SELECTORS["submit_button"])
            if submit_btn:
                await submit_btn.click()
            else:
                await prompt_input.press("Enter")

            # Wait for generation
            status, video_url, error_msg = await self._wait_for_result()

            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)

            screenshot_path = None
            if screenshot_dir:
                screenshot_path = os.path.join(
                    screenshot_dir,
                    f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
                await self.page.screenshot(path=screenshot_path)

            return GenerationResult(
                status=status,
                prompt=prompt,
                mode=GenerationMode.IMAGE_TO_VIDEO,
                spicy=False,  # Image-to-video doesn't have spicy mode
                video_url=video_url,
                screenshot_path=screenshot_path,
                error_message=error_msg,
                generation_time_ms=generation_time,
            )

        except PlaywrightTimeout:
            return GenerationResult(
                status=GenerationStatus.TIMEOUT,
                prompt=prompt,
                mode=GenerationMode.IMAGE_TO_VIDEO,
                spicy=False,
                error_message="Generation timed out",
            )
        except Exception as e:
            return GenerationResult(
                status=GenerationStatus.ERROR,
                prompt=prompt,
                mode=GenerationMode.IMAGE_TO_VIDEO,
                spicy=False,
                error_message=str(e),
            )

    async def _wait_for_result(self) -> Tuple[GenerationStatus, Optional[str], Optional[str]]:
        """
        Wait for generation result.

        Returns:
            Tuple of (status, video_url, error_message)
        """
        try:
            # Wait for either video, error, or blocked message
            result = await self.page.wait_for_selector(
                f"{self.SELECTORS['video_player']}, {self.SELECTORS['error_message']}, {self.SELECTORS['blocked_message']}",
                timeout=self.timeout,
                state="visible"
            )

            # Check what we got
            page_content = await self.page.content()

            # Check for blocked/policy messages
            blocked_patterns = [
                r"cannot generate",
                r"unable to",
                r"policy",
                r"inappropriate",
                r"violat",
                r"not allowed",
                r"restricted",
            ]
            for pattern in blocked_patterns:
                if re.search(pattern, page_content, re.IGNORECASE):
                    return GenerationStatus.BLOCKED, None, f"Content blocked: matched '{pattern}'"

            # Check for video
            video = await self.page.query_selector(self.SELECTORS["video_player"])
            if video:
                video_url = await video.get_attribute("src")
                return GenerationStatus.SUCCESS, video_url, None

            # Check for error
            error = await self.page.query_selector(self.SELECTORS["error_message"])
            if error:
                error_text = await error.inner_text()
                return GenerationStatus.ERROR, None, error_text

            return GenerationStatus.UNKNOWN, None, "Could not determine result"

        except PlaywrightTimeout:
            return GenerationStatus.TIMEOUT, None, "Timed out waiting for result"

    async def download_video(self, video_url: str, output_path: str) -> bool:
        """Download generated video."""
        try:
            response = await self.page.request.get(video_url)
            if response.ok:
                content = await response.body()
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(content)
                return True
            return False
        except Exception as e:
            console.print(f"[red]Error downloading video: {e}[/red]")
            return False
