"""Zoom API client for fetching meeting transcripts via User-managed OAuth.

Uses the OAuth 2.0 authorization code flow: on first run, opens a browser to
Zoom for consent, exchanges the code for an access + refresh token, caches
both at credentials/zoom_token.json. Subsequent runs refresh the access token
silently.

Requires a Zoom App Marketplace "OAuth" (user-managed) app — NOT Server-to-
Server OAuth. Scopes the app must request:
  - cloud_recording:read:list_user_recordings:user
  - cloud_recording:read:recording:user
  - cloud_recording:read:meeting_transcript:user
"""

import json
import logging
import os
import secrets
import socket
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

from .utils import get_credentials_path

logger = logging.getLogger("zoom_coach")

load_dotenv()


REDIRECT_PORT = int(os.getenv("ZOOM_REDIRECT_PORT", "8765"))
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/oauth/callback"
AUTHORIZE_URL = "https://zoom.us/oauth/authorize"
TOKEN_URL = "https://zoom.us/oauth/token"
TOKEN_FILE = "zoom_token.json"


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """One-shot HTTP handler that captures the ?code=... redirect from Zoom."""

    # Populated by the class via set_auth_state before serving.
    expected_state: str = ""
    received: dict = {}

    def do_GET(self):  # noqa: N802 (stdlib name)
        parsed = urlparse(self.path)
        if parsed.path != "/oauth/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        error = params.get("error", [None])[0]

        if error:
            _OAuthCallbackHandler.received = {"error": error}
            body = f"Zoom authorization failed: {error}. You can close this tab."
        elif state != _OAuthCallbackHandler.expected_state:
            _OAuthCallbackHandler.received = {"error": "state_mismatch"}
            body = "State mismatch — likely a stale callback. You can close this tab."
        elif not code:
            _OAuthCallbackHandler.received = {"error": "no_code"}
            body = "No authorization code returned. You can close this tab."
        else:
            _OAuthCallbackHandler.received = {"code": code}
            body = "Zoom authorization complete. You can close this tab and return to the terminal."

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):  # noqa: A002 (stdlib name)
        # Suppress default stderr access logging; we have our own logger.
        return


class ZoomClient:
    """Client for interacting with Zoom API using user-managed OAuth."""

    def __init__(self):
        self.client_id = os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_CLIENT_SECRET")

        if not all([self.client_id, self.client_secret]):
            logger.warning(
                "Zoom OAuth credentials not configured. Transcript fetching disabled."
            )
            self.enabled = False
            self.access_token = None
            self.refresh_token = None
            self.token_expiry = None
            return

        self.enabled = True
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self._load_or_authorize()

    # ---------- token lifecycle ----------

    def _token_path(self):
        return get_credentials_path(TOKEN_FILE)

    def _load_or_authorize(self) -> None:
        """Either load cached tokens and refresh, or start fresh OAuth flow."""
        cached = self._load_cached_tokens()
        if cached:
            self.access_token = cached["access_token"]
            self.refresh_token = cached["refresh_token"]
            self.token_expiry = datetime.fromisoformat(cached["token_expiry"])
            if datetime.now() >= self.token_expiry:
                logger.info("Cached Zoom token expired; refreshing...")
                if not self._refresh():
                    logger.warning("Refresh failed; re-running consent flow.")
                    self._run_oauth_flow()
            else:
                logger.info("Loaded cached Zoom token.")
            return

        self._run_oauth_flow()

    def _load_cached_tokens(self) -> Optional[dict]:
        path = self._token_path()
        if not path.exists() or path.stat().st_size == 0:
            return None
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            logger.warning(f"Malformed Zoom token cache at {path}; will re-authorize.")
            return None

    def _save_tokens(self) -> None:
        path = self._token_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_expiry": self.token_expiry.isoformat(),
                },
                f,
                indent=2,
            )
        os.chmod(path, 0o600)

    def _apply_token_response(self, data: dict) -> None:
        self.access_token = data["access_token"]
        # Zoom sometimes rotates the refresh token; prefer the new one.
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        # Subtract 60s so we refresh before actual expiry to avoid race conditions.
        self.token_expiry = datetime.now() + timedelta(
            seconds=data["expires_in"] - 60
        )
        self._save_tokens()

    def _refresh(self) -> bool:
        try:
            r = requests.post(
                TOKEN_URL,
                data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
                auth=(self.client_id, self.client_secret),
                timeout=10,
            )
            r.raise_for_status()
            self._apply_token_response(r.json())
            logger.info("Zoom token refreshed.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom token refresh failed: {e}")
            return False

    def _run_oauth_flow(self) -> None:
        """Open browser, capture ?code=..., exchange for tokens."""
        state = secrets.token_urlsafe(24)
        _OAuthCallbackHandler.expected_state = state
        _OAuthCallbackHandler.received = {}

        auth_url = AUTHORIZE_URL + "?" + urlencode({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": REDIRECT_URI,
            "state": state,
        })

        # Bind the callback server before opening the browser so we're guaranteed
        # to catch the redirect. Serve exactly one request, then shut down.
        try:
            server = HTTPServer(("localhost", REDIRECT_PORT), _OAuthCallbackHandler)
        except OSError as e:
            raise RuntimeError(
                f"Could not bind to localhost:{REDIRECT_PORT} for OAuth callback: {e}\n"
                f"Another process may be using the port. Set ZOOM_REDIRECT_PORT "
                f"in .env to a different free port (and update the app's Redirect URI)."
            )

        thread = threading.Thread(
            target=server.handle_request, daemon=True, name="zoom-oauth-callback"
        )
        thread.start()

        logger.info(f"Opening browser for Zoom OAuth consent... ({AUTHORIZE_URL})")
        print(
            "\nA browser tab will open asking you to authorize the Zoom app.\n"
            "If it doesn't, paste this URL into your browser manually:\n"
            f"  {auth_url}\n"
        )
        webbrowser.open(auth_url, new=1)

        # Wait up to 3 minutes for the user to complete consent.
        thread.join(timeout=180)
        server.server_close()

        if thread.is_alive():
            raise RuntimeError(
                "Zoom OAuth flow timed out after 3 minutes. Try again."
            )

        received = _OAuthCallbackHandler.received
        if "error" in received:
            raise RuntimeError(f"Zoom OAuth failed: {received['error']}")
        if "code" not in received:
            raise RuntimeError("Zoom OAuth callback produced no code.")

        # Exchange code for tokens
        r = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": received["code"],
                "redirect_uri": REDIRECT_URI,
            },
            auth=(self.client_id, self.client_secret),
            timeout=15,
        )
        r.raise_for_status()
        self._apply_token_response(r.json())
        logger.info("Zoom OAuth flow complete; token cached.")

    def _ensure_authenticated(self) -> bool:
        if not self.enabled:
            return False
        if not self.access_token:
            return False
        if datetime.now() >= self.token_expiry and not self._refresh():
            return False
        return True

    # ---------- API calls ----------

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    def list_user_recordings(self, days_back: int = 14) -> list:
        """List the authenticated user's cloud recordings in the last N days."""
        if not self._ensure_authenticated():
            logger.error("Zoom API not authenticated")
            return []

        params = {
            "from": (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
            "to": datetime.now().strftime("%Y-%m-%d"),
            "page_size": 100,
        }
        try:
            r = requests.get(
                "https://api.zoom.us/v2/users/me/recordings",
                headers=self._headers(),
                params=params,
                timeout=15,
            )
            r.raise_for_status()
            return r.json().get("meetings", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing recordings: {e}")
            return []

    def get_meeting_transcript(self, meeting_id: str) -> Optional[str]:
        """Fetch the cleaned plaintext transcript for a meeting ID."""
        if not self._ensure_authenticated():
            logger.error("Zoom API not authenticated")
            return None

        try:
            r = requests.get(
                f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings",
                headers=self._headers(),
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()

            transcript_file = next(
                (f for f in data.get("recording_files", []) if f.get("file_type") == "TRANSCRIPT"),
                None,
            )
            if not transcript_file:
                logger.warning(f"No transcript found for meeting {meeting_id}")
                return None

            download_url = transcript_file.get("download_url")
            if not download_url:
                logger.error("Transcript download URL not available")
                return None

            vtt = requests.get(download_url, headers=self._headers(), timeout=30)
            vtt.raise_for_status()
            return _vtt_to_plain_text(vtt.text)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching transcript for meeting {meeting_id}: {e}")
            return None


def _vtt_to_plain_text(vtt: str) -> str:
    """Strip WEBVTT headers, cue timestamps, and blank lines."""
    lines = []
    for line in vtt.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("WEBVTT") or stripped.startswith("NOTE") or "-->" in stripped:
            continue
        lines.append(stripped)
    return "\n".join(lines)


# Silence "imported but unused" for optional stdlib fallback import.
_ = (socket, time)
