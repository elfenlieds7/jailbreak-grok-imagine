"""Database operations."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from .models import Base, TestCase, TestResult


class Database:
    """Database manager for test results."""

    def __init__(self, db_path: str = "data/results.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)

        # Create tables
        Base.metadata.create_all(self.engine)

    def save_result(self, result: TestResult) -> TestResult:
        """Save a test result."""
        session = self.Session()
        try:
            session.add(result)
            session.commit()
            session.refresh(result)
            return result
        finally:
            session.close()

    def get_result(self, test_id: str) -> Optional[TestResult]:
        """Get a test result by ID."""
        session = self.Session()
        try:
            return session.query(TestResult).filter_by(test_id=test_id).first()
        finally:
            session.close()

    def get_results(
        self,
        classification: Optional[str] = None,
        category: Optional[str] = None,
        technique: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TestResult]:
        """Get test results with optional filters."""
        session = self.Session()
        try:
            query = session.query(TestResult)

            if classification:
                query = query.filter_by(classification=classification)
            if category:
                query = query.filter_by(category=category)
            if technique:
                query = query.filter_by(technique=technique)

            return query.order_by(TestResult.timestamp.desc()).offset(offset).limit(limit).all()
        finally:
            session.close()

    def get_statistics(self) -> dict:
        """Get aggregated statistics."""
        session = self.Session()
        try:
            total = session.query(TestResult).count()

            # Classification breakdown
            classification_counts = (
                session.query(TestResult.classification, func.count(TestResult.id))
                .group_by(TestResult.classification)
                .all()
            )

            # Technique breakdown
            technique_counts = (
                session.query(TestResult.technique, func.count(TestResult.id))
                .filter(TestResult.technique.isnot(None))
                .group_by(TestResult.technique)
                .all()
            )

            # Average blur ratio for generated videos
            avg_blur = (
                session.query(func.avg(TestResult.blur_ratio))
                .filter(TestResult.blur_ratio.isnot(None))
                .scalar()
            )

            return {
                "total_tests": total,
                "classification_breakdown": dict(classification_counts),
                "technique_breakdown": dict(technique_counts),
                "average_blur_ratio": avg_blur or 0.0,
            }
        finally:
            session.close()

    # Test Case Management

    def save_test_case(self, test_case: TestCase) -> TestCase:
        """Save a test case."""
        session = self.Session()
        try:
            session.add(test_case)
            session.commit()
            session.refresh(test_case)
            return test_case
        finally:
            session.close()

    def get_test_cases(
        self,
        category: Optional[str] = None,
        technique: Optional[str] = None,
        enabled_only: bool = True,
    ) -> List[TestCase]:
        """Get test cases with optional filters."""
        session = self.Session()
        try:
            query = session.query(TestCase)

            if enabled_only:
                query = query.filter_by(enabled=True)
            if category:
                query = query.filter_by(category=category)
            if technique:
                query = query.filter_by(technique=technique)

            return query.all()
        finally:
            session.close()

    def update_test_case_run(self, test_id: str):
        """Update test case run count and timestamp."""
        session = self.Session()
        try:
            test_case = session.query(TestCase).filter_by(test_id=test_id).first()
            if test_case:
                test_case.run_count += 1
                test_case.last_run = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def import_test_cases_from_csv(self, csv_path: str) -> int:
        """
        Import test cases from CSV file.

        Expected columns: test_id, prompt, mode, spicy, technique, category, notes

        Returns:
            Number of test cases imported
        """
        import csv

        session = self.Session()
        count = 0

        try:
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    test_case = TestCase(
                        test_id=row.get("test_id") or f"test_{count:04d}",
                        prompt=row["prompt"],
                        mode=row.get("mode", "text_to_video"),
                        image_path=row.get("image_path"),
                        spicy=row.get("spicy", "true").lower() == "true",
                        technique=row.get("technique"),
                        category=row.get("category"),
                        expected_result=row.get("expected_result"),
                        notes=row.get("notes"),
                    )
                    session.merge(test_case)
                    count += 1

            session.commit()
            return count

        finally:
            session.close()

    def export_results_to_csv(self, csv_path: str, **filters) -> int:
        """
        Export test results to CSV file.

        Returns:
            Number of results exported
        """
        import csv

        results = self.get_results(**filters, limit=10000)

        with open(csv_path, "w", newline="") as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
                writer.writeheader()
                for result in results:
                    writer.writerow(result.to_dict())

        return len(results)
