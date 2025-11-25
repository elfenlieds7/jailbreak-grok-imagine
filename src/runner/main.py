"""Main test runner for Grok Imagine jailbreak research."""

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..judge.blur_detector import BlurDetector
from ..judge.classifier import ResultClassifier
from ..judge.ui_detector import UIDetector, UIState
from ..storage.database import Database
from ..storage.models import TestCase, TestResult
from ..utils.config import Config
from ..utils.video import VideoProcessor
from .browser import BrowserManager
from .capture import CaptureManager
from .grok import GenerationStatus, GrokImagine

console = Console()


class TestRunner:
    """Orchestrate jailbreak testing."""

    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.get("storage.path", "data/results.db"))
        self.capture = CaptureManager(
            screenshots_dir=config.get("storage.screenshots_dir", "output/screenshots"),
            videos_dir=config.get("storage.videos_dir", "output/videos"),
        )
        self.classifier = ResultClassifier(
            blur_threshold=config.get("judge.opencv.blur_threshold", 100.0)
        )
        self.video_processor = VideoProcessor(
            frame_interval=config.get("runner.frame_interval", 1.0)
        )
        self.ui_detector = UIDetector()
        self.blur_detector = BlurDetector()

    async def run_single_test(
        self,
        browser: BrowserManager,
        grok: GrokImagine,
        prompt: str,
        test_id: Optional[str] = None,
        spicy: bool = True,
        technique: Optional[str] = None,
        category: Optional[str] = None,
    ) -> TestResult:
        """
        Run a single test case.

        Args:
            browser: Browser manager instance
            grok: Grok Imagine automation instance
            prompt: Test prompt
            test_id: Optional test identifier
            spicy: Enable spicy mode
            technique: Attack technique name
            category: Test category

        Returns:
            TestResult record
        """
        test_id = test_id or f"test_{uuid.uuid4().hex[:8]}"
        console.print(f"\n[bold blue]Running test: {test_id}[/bold blue]")
        console.print(f"[dim]Prompt: {prompt[:100]}...[/dim]" if len(prompt) > 100 else f"[dim]Prompt: {prompt}[/dim]")

        # Generate
        result = await grok.generate_text_to_video(
            prompt=prompt,
            spicy=spicy,
            screenshot_dir=str(self.capture.screenshots_dir),
        )

        # Detect UI state
        ui_state, ui_detail = await self.ui_detector.detect_state(browser.page)

        # Download video if generated
        video_path = None
        blur_analysis = None
        classification_result = None

        if result.status == GenerationStatus.SUCCESS and result.video_url:
            video_path = await self.capture.download_video(
                browser.page,
                result.video_url,
                test_id,
            )

            # Analyze video frames if downloaded
            if video_path and self.config.get("runner.extract_frames", True):
                frames_dir = Path(self.config.get("storage.frames_dir", "output/frames")) / test_id
                frame_paths = self.video_processor.extract_frames(
                    video_path,
                    output_dir=str(frames_dir),
                    max_frames=30,
                )

                if frame_paths:
                    import cv2
                    frames = [cv2.imread(p) for p in frame_paths]
                    blur_analysis = self.blur_detector.analyze_video_frames(frames)

        # Classify result
        classification_result = self.classifier.classify(
            ui_state=ui_state,
            blur_analysis=blur_analysis,
        )

        # Create result record
        test_result = TestResult(
            test_id=test_id,
            timestamp=datetime.utcnow(),
            mode="text_to_video",
            prompt=prompt,
            spicy=spicy,
            technique=technique,
            category=category,
            ui_status=ui_state.value,
            error_message=result.error_message or ui_detail,
            video_url=result.video_url,
            video_path=video_path,
            screenshot_path=result.screenshot_path,
            blur_detected=blur_analysis.get("censored_frames", 0) > 0 if blur_analysis else None,
            blur_ratio=blur_analysis.get("censored_ratio") if blur_analysis else None,
            avg_blur_score=blur_analysis.get("avg_blur_score") if blur_analysis else None,
            has_mosaic=blur_analysis.get("mosaic_frames", 0) > 0 if blur_analysis else None,
            has_black_bars=blur_analysis.get("black_bar_frames", 0) > 0 if blur_analysis else None,
            classification=classification_result.result.value,
            classification_confidence=classification_result.confidence,
            generation_time_ms=result.generation_time_ms,
            notes=classification_result.notes,
        )

        # Save to database
        self.db.save_result(test_result)

        # Print result
        self._print_result(test_result)

        return test_result

    async def run_batch(
        self,
        test_cases: List[TestCase],
        delay: int = 10,
    ) -> List[TestResult]:
        """
        Run multiple test cases.

        Args:
            test_cases: List of test cases to run
            delay: Delay between tests in seconds

        Returns:
            List of test results
        """
        results = []

        async with BrowserManager(
            headless=self.config.get("grok.headless", False),
            storage_state_path=self.config.get("grok.storage_state_path", "data/auth/storage_state.json"),
            timeout=self.config.get("grok.timeout", 120000),
        ) as browser:
            # Check login
            if not await browser.is_logged_in():
                console.print("[yellow]Not logged in. Starting interactive login...[/yellow]")
                await browser.login_interactive()

            grok = GrokImagine(browser.page, timeout=self.config.get("grok.timeout", 120000))
            await grok.navigate_to_imagine()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Running {len(test_cases)} tests...", total=len(test_cases))

                for i, test_case in enumerate(test_cases):
                    progress.update(task, description=f"Test {i+1}/{len(test_cases)}: {test_case.test_id}")

                    result = await self.run_single_test(
                        browser=browser,
                        grok=grok,
                        prompt=test_case.prompt,
                        test_id=test_case.test_id,
                        spicy=test_case.spicy,
                        technique=test_case.technique,
                        category=test_case.category,
                    )
                    results.append(result)

                    # Update test case run info
                    self.db.update_test_case_run(test_case.test_id)

                    progress.advance(task)

                    # Delay between tests
                    if i < len(test_cases) - 1:
                        await asyncio.sleep(delay)

        return results

    def _print_result(self, result: TestResult):
        """Print test result summary."""
        status_colors = {
            "full_success": "green",
            "partial_success": "yellow",
            "soft_block": "orange3",
            "hard_block": "red",
            "error": "red",
            "unknown": "dim",
        }
        color = status_colors.get(result.classification, "white")

        console.print(f"  [{color}]Result: {result.classification.upper()}[/{color}]")
        if result.blur_ratio is not None:
            console.print(f"  [dim]Blur ratio: {result.blur_ratio:.1%}[/dim]")
        if result.notes:
            console.print(f"  [dim]Notes: {result.notes}[/dim]")


@click.command()
@click.option("--config", "-c", default="config.yaml", help="Config file path")
@click.option("--prompt", "-p", help="Single prompt to test")
@click.option("--category", help="Run tests from specific category")
@click.option("--technique", help="Run tests with specific technique")
@click.option("--csv", help="Import and run test cases from CSV")
@click.option("--login", is_flag=True, help="Run interactive login only")
@click.option("--stats", is_flag=True, help="Show statistics only")
def main(config, prompt, category, technique, csv, login, stats):
    """Grok Imagine Jailbreak Test Runner."""
    cfg = Config(config)
    runner = TestRunner(cfg)

    if stats:
        # Show statistics
        statistics = runner.db.get_statistics()
        console.print("\n[bold]Test Statistics[/bold]")
        console.print(f"Total tests: {statistics['total_tests']}")

        if statistics['classification_breakdown']:
            table = Table(title="Classification Breakdown")
            table.add_column("Classification")
            table.add_column("Count")
            for cls, count in statistics['classification_breakdown'].items():
                table.add_row(cls, str(count))
            console.print(table)

        console.print(f"Average blur ratio: {statistics['average_blur_ratio']:.1%}")
        return

    async def run():
        if login:
            # Interactive login only
            async with BrowserManager(
                headless=False,
                storage_state_path=cfg.get("grok.storage_state_path"),
            ) as browser:
                await browser.login_interactive()
            return

        if prompt:
            # Single prompt test
            async with BrowserManager(
                headless=cfg.get("grok.headless", False),
                storage_state_path=cfg.get("grok.storage_state_path"),
                timeout=cfg.get("grok.timeout", 120000),
            ) as browser:
                if not await browser.is_logged_in():
                    await browser.login_interactive()

                grok = GrokImagine(browser.page)
                await grok.navigate_to_imagine()

                await runner.run_single_test(
                    browser=browser,
                    grok=grok,
                    prompt=prompt,
                    spicy=cfg.get("grok.spicy_mode", True),
                )
            return

        # Batch test
        if csv:
            count = runner.db.import_test_cases_from_csv(csv)
            console.print(f"[green]Imported {count} test cases from {csv}[/green]")

        test_cases = runner.db.get_test_cases(
            category=category,
            technique=technique,
        )

        if not test_cases:
            console.print("[yellow]No test cases found. Use --csv to import or --prompt for single test.[/yellow]")
            return

        console.print(f"[bold]Running {len(test_cases)} test cases[/bold]")
        await runner.run_batch(
            test_cases,
            delay=cfg.get("runner.delay_between_tests", 10),
        )

    asyncio.run(run())


if __name__ == "__main__":
    main()
