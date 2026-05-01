"""Zoom API client for fetching meeting transcripts (optional)."""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv

logger = logging.getLogger("zoom_coach")

load_dotenv()


class ZoomClient:
    """Client for interacting with Zoom API."""

    def __init__(self):
        """Initialize Zoom client."""
        self.account_id = os.getenv("ZOOM_ACCOUNT_ID")
        self.client_id = os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_CLIENT_SECRET")

        if not all([self.account_id, self.client_id, self.client_secret]):
            logger.warning(
                "Zoom API credentials not configured. Transcript fetching disabled."
            )
            self.enabled = False
            self.access_token = None
        else:
            self.enabled = True
            self.access_token = None
            self.token_expiry = None
            self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Zoom API using Server-to-Server OAuth."""
        if not self.enabled:
            return

        try:
            response = requests.post(
                "https://zoom.us/oauth/token",
                params={
                    "grant_type": "account_credentials",
                    "account_id": self.account_id,
                },
                auth=(self.client_id, self.client_secret),
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            self.access_token = data["access_token"]
            self.token_expiry = datetime.now() + timedelta(
                seconds=data["expires_in"] - 60
            )

            logger.info("Zoom API authentication successful")

        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom authentication failed: {e}")
            self.enabled = False

    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token."""
        if not self.enabled:
            return False

        if not self.access_token or datetime.now() >= self.token_expiry:
            self._authenticate()

        return self.enabled and self.access_token is not None

    def get_meeting_transcript(self, meeting_id: str) -> Optional[str]:
        """
        Fetch meeting transcript for a given meeting ID.

        Args:
            meeting_id: Zoom meeting ID

        Returns:
            Transcript text if available, None otherwise
        """
        if not self._ensure_authenticated():
            logger.error("Zoom API not authenticated")
            return None

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # First, get the list of transcript files
            response = requests.get(
                f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings",
                headers=headers,
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            # Find transcript file
            transcript_file = None
            for recording in data.get("recording_files", []):
                if recording.get("file_type") == "TRANSCRIPT":
                    transcript_file = recording
                    break

            if not transcript_file:
                logger.warning(f"No transcript found for meeting {meeting_id}")
                return None

            # Download transcript
            download_url = transcript_file.get("download_url")
            if not download_url:
                logger.error("Transcript download URL not available")
                return None

            transcript_response = requests.get(
                download_url,
                headers=headers,
                timeout=30,
            )

            transcript_response.raise_for_status()

            # Zoom transcripts are usually in VTT format
            transcript_text = transcript_response.text

            # Clean up VTT format to plain text
            transcript_lines = []
            for line in transcript_text.split("\n"):
                # Skip VTT headers and timestamps
                if (
                    line.startswith("WEBVTT")
                    or line.startswith("NOTE")
                    or "-->" in line
                    or not line.strip()
                ):
                    continue
                transcript_lines.append(line.strip())

            return "\n".join(transcript_lines)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching transcript for meeting {meeting_id}: {e}")
            return None
