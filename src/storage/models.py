"""Database models for test results."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class TestResult(Base):
    """Test result record."""

    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(50), unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Input
    mode = Column(String(20))  # 'text_to_video' or 'image_to_video'
    prompt = Column(Text)
    image_path = Column(String(500), nullable=True)
    spicy = Column(Boolean, default=True)
    technique = Column(String(50), nullable=True)  # Attack technique used
    category = Column(String(50), nullable=True)  # Test category

    # UI Result
    ui_status = Column(String(20))  # 'generated', 'blocked', 'error', 'unknown'
    error_message = Column(Text, nullable=True)

    # Output files
    video_url = Column(String(1000), nullable=True)
    video_path = Column(String(500), nullable=True)
    screenshot_path = Column(String(500), nullable=True)

    # Blur Analysis
    blur_detected = Column(Boolean, nullable=True)
    blur_ratio = Column(Float, nullable=True)  # 0.0 to 1.0
    avg_blur_score = Column(Float, nullable=True)
    has_mosaic = Column(Boolean, nullable=True)
    has_black_bars = Column(Boolean, nullable=True)

    # Classification
    classification = Column(String(20))  # JailbreakResult value
    classification_confidence = Column(Float, nullable=True)

    # Metrics
    generation_time_ms = Column(Integer, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "test_id": self.test_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "mode": self.mode,
            "prompt": self.prompt,
            "image_path": self.image_path,
            "spicy": self.spicy,
            "technique": self.technique,
            "category": self.category,
            "ui_status": self.ui_status,
            "error_message": self.error_message,
            "video_url": self.video_url,
            "video_path": self.video_path,
            "screenshot_path": self.screenshot_path,
            "blur_detected": self.blur_detected,
            "blur_ratio": self.blur_ratio,
            "avg_blur_score": self.avg_blur_score,
            "has_mosaic": self.has_mosaic,
            "has_black_bars": self.has_black_bars,
            "classification": self.classification,
            "classification_confidence": self.classification_confidence,
            "generation_time_ms": self.generation_time_ms,
            "notes": self.notes,
        }


class TestCase(Base):
    """Test case definition."""

    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(String(50), unique=True, index=True)

    # Test definition
    prompt = Column(Text)
    mode = Column(String(20), default="text_to_video")
    image_path = Column(String(500), nullable=True)
    spicy = Column(Boolean, default=True)

    # Metadata
    technique = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    expected_result = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)

    # Status
    enabled = Column(Boolean, default=True)
    run_count = Column(Integer, default=0)
    last_run = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "prompt": self.prompt,
            "mode": self.mode,
            "image_path": self.image_path,
            "spicy": self.spicy,
            "technique": self.technique,
            "category": self.category,
            "expected_result": self.expected_result,
            "notes": self.notes,
            "enabled": self.enabled,
            "run_count": self.run_count,
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }
