"""Gmail API client for fetching Zoom meeting summaries."""

import base64
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .utils import get_google_credentials, load_config

logger = logging.getLogger("zoom_coach")


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self):
        self.config = load_config()["gmail"]
        self.service = build("gmail", "v1", credentials=get_google_credentials())
        logger.info("Gmail authentication successful")

    def fetch_zoom_summaries(
        self, days_back: Optional[int] = None, mark_as_read: bool = False
    ) -> List[dict]:
        """
        Fetch Zoom meeting summary emails.

        Args:
            days_back: Number of days to look back. Defaults to config value.
            mark_as_read: Whether to mark fetched emails as read.

        Returns:
            List of email dictionaries with parsed content.
        """
        if days_back is None:
            days_back = self.config["days_to_look_back"]

        sender = self.config["sender_filter"]
        subject = self.config["subject_filter"]

        # Build query
        after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
        query = f'from:{sender} subject:"{subject}" after:{after_date}'

        logger.info(f"Searching for emails: {query}")

        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=50)
                .execute()
            )

            messages = results.get("messages", [])
            logger.info(f"Found {len(messages)} email(s)")

            parsed_emails = []
            for message in messages:
                email_data = self._parse_email(message["id"])
                if email_data:
                    parsed_emails.append(email_data)

                    if mark_as_read:
                        self._mark_as_read(message["id"])

            return parsed_emails

        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise

    def _parse_email(self, message_id: str) -> Optional[dict]:
        """
        Parse email message and extract content.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email content or None if parsing fails
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = message["payload"]["headers"]
            subject = next(h["value"] for h in headers if h["name"].lower() == "subject")
            date_str = next(h["value"] for h in headers if h["name"].lower() == "date")

            # Extract body content
            body = self._extract_body(message["payload"])

            if not body:
                logger.warning(f"No body content found in message {message_id}")
                return None

            return {
                "id": message_id,
                "subject": subject,
                "date": date_str,
                "body": body,
                "snippet": message.get("snippet", ""),
            }

        except Exception as e:
            logger.error(f"Error parsing email {message_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """
        Extract body text from email payload.

        Args:
            payload: Email payload from Gmail API

        Returns:
            Decoded body text
        """
        body = ""

        if "body" in payload and "data" in payload["body"]:
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        # Handle multipart messages
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body += base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                elif part["mimeType"] == "text/html":
                    # Fallback to HTML if no plain text
                    if not body and "data" in part["body"]:
                        body += base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                elif "parts" in part:
                    # Recursively handle nested parts
                    body += self._extract_body(part)

        return body

    def _mark_as_read(self, message_id: str) -> None:
        """Mark email as read."""
        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.debug(f"Marked message {message_id} as read")
        except HttpError as error:
            logger.error(f"Error marking message as read: {error}")

    def get_latest_unprocessed_summaries(
        self, processed_ids: List[str]
    ) -> List[dict]:
        """
        Fetch summaries that haven't been processed yet.

        Args:
            processed_ids: List of already processed email IDs

        Returns:
            List of new email dictionaries
        """
        all_summaries = self.fetch_zoom_summaries()
        return [email for email in all_summaries if email["id"] not in processed_ids]
