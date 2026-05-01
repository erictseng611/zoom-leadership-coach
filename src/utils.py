"""Utility functions for the application."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure logging with rich output."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )
    return logging.getLogger("zoom_coach")


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def load_config(config_name: str = "settings") -> Dict[str, Any]:
    """Load configuration from JSON file."""
    config_path = get_project_root() / "config" / f"{config_name}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        return json.load(f)


def load_leadership_principles() -> str:
    """Load leadership principles from markdown file."""
    principles_path = get_project_root() / "config" / "leadership_principles.md"
    if not principles_path.exists():
        raise FileNotFoundError(f"Leadership principles file not found: {principles_path}")

    with open(principles_path, "r") as f:
        return f.read()


def save_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load data from JSON file."""
    if not filepath.exists():
        return {}

    with open(filepath, "r") as f:
        return json.load(f)


def get_credentials_path(filename: str) -> Path:
    """Get path to credentials file."""
    return get_project_root() / "credentials" / filename


def get_data_path(filename: str) -> Path:
    """Get path to data file."""
    return get_project_root() / "data" / filename


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime object."""
    return dt.strftime(format_str)


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    root = get_project_root()
    directories = [
        root / "credentials",
        root / "data",
        root / "data" / "coaching_reports",
        root / "data" / "todos",
        root / "logs",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
