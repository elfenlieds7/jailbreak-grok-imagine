"""Browser management with Playwright."""

import asyncio
import os
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from rich.console import Console

console = Console()


class BrowserManager:
    """Manage browser instance and authentication state."""

    def __init__(
        self,
        headless: bool = False,
        storage_state_path: str = "data/auth/storage_state.json",
        timeout: int = 120000,
    ):
        """
        Initialize browser manager.

        Args:
            headless: Run browser in headless mode
            storage_state_path: Path to save/load auth cookies
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.storage_state_path = Path(storage_state_path)
        self.timeout = timeout

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self) -> Page:
        """Start browser and return page."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # Load storage state if exists
        storage_state = None
        if self.storage_state_path.exists():
            storage_state = str(self.storage_state_path)
            console.print(f"[green]Loading saved session from {storage_state}[/green]")

        self._context = await self._browser.new_context(
            storage_state=storage_state,
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._context.set_default_timeout(self.timeout)

        self._page = await self._context.new_page()
        return self._page

    async def close(self):
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def save_storage_state(self):
        """Save current cookies and localStorage."""
        if self._context:
            self.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(self.storage_state_path))
            console.print(
                f"[green]Session saved to {self.storage_state_path}[/green]"
            )

    async def login_interactive(self, url: str = "https://x.com/i/grok"):
        """
        Open browser for manual login, then save session.

        This is used for initial setup - user logs in manually,
        then we save the session for future automated runs.
        """
        console.print("\n[yellow]═══ Interactive Login ═══[/yellow]")
        console.print(f"1. Browser will open to: {url}")
        console.print("2. Please log in to your X/Twitter account")
        console.print("3. Navigate to Grok and ensure you can access it")
        console.print("4. Press Enter in this terminal when done\n")

        await self._page.goto(url)

        # Wait for user to complete login
        input("Press Enter after logging in...")

        # Save the session
        await self.save_storage_state()
        console.print("[green]Login session saved successfully![/green]")

    async def is_logged_in(self) -> bool:
        """Check if currently logged in to X/Grok."""
        try:
            # Navigate to Grok
            await self._page.goto("https://x.com/i/grok", wait_until="networkidle")

            # Check for login indicators
            # If we see the Grok interface, we're logged in
            # If we see login page, we're not
            grok_indicator = await self._page.query_selector(
                '[data-testid="grok-composer"], textarea[placeholder*="Ask"], textarea[placeholder*="Grok"]'
            )

            return grok_indicator is not None
        except Exception as e:
            console.print(f"[red]Error checking login status: {e}[/red]")
            return False

    @property
    def page(self) -> Optional[Page]:
        return self._page

    @property
    def context(self) -> Optional[BrowserContext]:
        return self._context
