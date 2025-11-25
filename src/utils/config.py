"""Configuration management."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager with environment variable support."""

    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()
        self.config_path = Path(config_path)
        self._config: dict = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            # Try example config
            example_path = self.config_path.with_suffix(".example.yaml")
            if example_path.exists():
                self.config_path = example_path
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            self._config = yaml.safe_load(f) or {}

        # Expand environment variables
        self._expand_env_vars(self._config)

    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand ${VAR} patterns in config values."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._expand_env_vars(value)
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.environ.get(env_var, "")
        return obj

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key (e.g., 'grok.timeout')."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    @property
    def grok(self) -> dict:
        return self._config.get("grok", {})

    @property
    def judge(self) -> dict:
        return self._config.get("judge", {})

    @property
    def storage(self) -> dict:
        return self._config.get("storage", {})

    @property
    def runner(self) -> dict:
        return self._config.get("runner", {})
