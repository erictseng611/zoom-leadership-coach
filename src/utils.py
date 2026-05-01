"""Utility functions for the application."""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.logging import RichHandler

console = Console()

# Shared Google OAuth scopes for Gmail + Calendar. Both clients reuse the same
# token.pickle, so the scope set is combined rather than per-client.
GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]


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
    """Load data from JSON file. Returns {} if missing, empty, or malformed."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.getLogger("zoom_coach").warning(
            f"Malformed JSON at {filepath}, treating as empty"
        )
        return {}


def get_credentials_path(filename: str) -> Path:
    """Get path to credentials file."""
    return get_project_root() / "credentials" / filename


def get_data_path(filename: str) -> Path:
    """Get path to data file."""
    return get_project_root() / "data" / filename


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    root = get_project_root()
    for directory in [
        root / "credentials",
        root / "data",
        root / "data" / "coaching_reports",
        root / "data" / "todos",
        root / "logs",
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def get_google_credentials():
    """Load or refresh shared Google OAuth credentials for Gmail + Calendar."""
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    logger = logging.getLogger("zoom_coach")
    token_path = get_credentials_path("token.pickle")
    credentials_path = get_credentials_path("google_credentials.json")

    credentials = None
    if token_path.exists():
        with open(token_path, "rb") as token:
            credentials = pickle.load(token)

    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        logger.info("Refreshing expired Google credentials...")
        credentials.refresh(Request())
    else:
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Google credentials not found at {credentials_path}. "
                "Please download OAuth2 credentials from Google Cloud Console."
            )
        logger.info("Starting OAuth2 flow...")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), GOOGLE_OAUTH_SCOPES
        )
        credentials = flow.run_local_server(port=0)

    with open(token_path, "wb") as token:
        pickle.dump(credentials, token)

    return credentials


