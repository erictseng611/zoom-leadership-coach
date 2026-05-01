"""Google Calendar API client for creating events and todos."""

import logging
import pickle
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .utils import get_credentials_path, load_config

logger = logging.getLogger("zoom_coach")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar"
]


class CalendarClient:
    """Client for interacting with Google Calendar API."""

    def __init__(self):
        """Initialize Calendar client."""
        self.config = load_config()["calendar"]
        self.scheduling_config = load_config()["scheduling"]
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google Calendar API using OAuth2."""
        credentials = None
        token_path = get_credentials_path("token.pickle")
        credentials_path = get_credentials_path("google_credentials.json")

        # Load existing token if available
        if token_path.exists():
            with open(token_path, "rb") as token:
                credentials = pickle.load(token)

        # If no valid credentials, request authorization
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info("Refreshing expired credentials...")
                credentials.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        f"Google credentials not found at {credentials_path}"
                    )

                logger.info("Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                credentials = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(token_path, "wb") as token:
                pickle.dump(credentials, token)

        self.service = build("calendar", "v3", credentials=credentials)
        logger.info("Calendar authentication successful")

    def get_free_busy(
        self, start_time: datetime, end_time: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """
        Get busy time slots in the specified range.

        Args are naive local datetimes. They're attached to the local tz for
        the Google Calendar query, then busy periods are returned as naive
        LOCAL datetimes so slot arithmetic against local work hours is correct.
        """
        local_tz = datetime.now().astimezone().tzinfo
        start_aware = start_time.replace(tzinfo=local_tz)
        end_aware = end_time.replace(tzinfo=local_tz)

        try:
            body = {
                "timeMin": start_aware.isoformat(),
                "timeMax": end_aware.isoformat(),
                "items": [{"id": "primary"}],
            }

            response = self.service.freebusy().query(body=body).execute()
            busy_times = response["calendars"]["primary"]["busy"]

            result = []
            for slot in busy_times:
                busy_start = datetime.fromisoformat(
                    slot["start"].replace("Z", "+00:00")
                ).astimezone(local_tz).replace(tzinfo=None)
                busy_end = datetime.fromisoformat(
                    slot["end"].replace("Z", "+00:00")
                ).astimezone(local_tz).replace(tzinfo=None)
                result.append((busy_start, busy_end))
            return result

        except HttpError as error:
            logger.error(f"Error fetching free/busy: {error}")
            return []

    def find_available_slots(
        self,
        duration_minutes: int,
        days_ahead: int = 7,
        preferred_times: Optional[List[str]] = None,
    ) -> List[datetime]:
        """
        Find available time slots for scheduling tasks.

        Args:
            duration_minutes: Duration of the task in minutes
            days_ahead: Number of days to look ahead
            preferred_times: List of preferred time ranges (e.g., ["09:00-11:00"])

        Returns:
            List of available start times
        """
        now = datetime.now()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=days_ahead)

        busy_periods = self.get_free_busy(start_time, end_time)
        # Treat "now + 15 min" as the earliest schedulable moment so we don't
        # try to put a TODO in the past (or three minutes from now).
        earliest = now + timedelta(minutes=15)

        available_slots = []
        current_day = start_time

        work_start = datetime.strptime(
            self.scheduling_config["work_hours_start"], "%H:%M"
        ).time()
        work_end = datetime.strptime(
            self.scheduling_config["work_hours_end"], "%H:%M"
        ).time()

        # Parse lunch break
        lunch_parts = self.scheduling_config["lunch_break"].split("-")
        lunch_start = datetime.strptime(lunch_parts[0], "%H:%M").time()
        lunch_end = datetime.strptime(lunch_parts[1], "%H:%M").time()

        for day_offset in range(days_ahead):
            current_day = start_time + timedelta(days=day_offset)

            # Skip weekends
            if current_day.weekday() >= 5:
                continue

            # Check work hours
            day_start = current_day.replace(
                hour=work_start.hour, minute=work_start.minute
            )
            day_end = current_day.replace(hour=work_end.hour, minute=work_end.minute)

            # Generate 30-minute time slots
            current_slot = day_start
            while current_slot + timedelta(minutes=duration_minutes) <= day_end:
                slot_end = current_slot + timedelta(minutes=duration_minutes)

                # Never schedule in the past
                if current_slot < earliest:
                    current_slot += timedelta(minutes=30)
                    continue

                # Skip lunch break
                if not (
                    current_slot.time() >= lunch_end or slot_end.time() <= lunch_start
                ):
                    current_slot += timedelta(minutes=30)
                    continue

                # Check if slot overlaps with busy periods
                is_available = True
                for busy_start, busy_end in busy_periods:
                    if (
                        current_slot < busy_end
                        and slot_end > busy_start
                    ):
                        is_available = False
                        break

                if is_available:
                    # Check if in preferred time range
                    if preferred_times:
                        for time_range in preferred_times:
                            pref_start, pref_end = time_range.split("-")
                            pref_start_time = datetime.strptime(
                                pref_start, "%H:%M"
                            ).time()
                            pref_end_time = datetime.strptime(pref_end, "%H:%M").time()

                            if (
                                pref_start_time
                                <= current_slot.time()
                                < pref_end_time
                            ):
                                available_slots.append(current_slot)
                                break
                    else:
                        available_slots.append(current_slot)

                current_slot += timedelta(minutes=30)

        return available_slots

    def create_event(
        self,
        summary: str,
        description: str,
        start_time: datetime,
        duration_minutes: Optional[int] = None,
    ) -> Optional[str]:
        """
        Create a calendar event.

        Args:
            summary: Event title
            description: Event description
            start_time: Start time of the event
            duration_minutes: Duration in minutes (defaults to config value)

        Returns:
            Event ID if successful, None otherwise
        """
        if duration_minutes is None:
            duration_minutes = self.config["default_event_duration_minutes"]

        end_time = start_time + timedelta(minutes=duration_minutes)

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Los_Angeles",  # TODO: Make configurable
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Los_Angeles",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        try:
            event_result = (
                self.service.events().insert(calendarId="primary", body=event).execute()
            )
            logger.info(f"Created event: {summary} at {start_time}")
            return event_result["id"]

        except HttpError as error:
            logger.error(f"Error creating event: {error}")
            return None

    def create_todo(
        self,
        title: str,
        description: str,
        suggested_time: datetime,
        duration_minutes: int = 30,
        priority: str = "medium",
    ) -> Optional[str]:
        """
        Create a todo item as a calendar event.

        Args:
            title: Todo title
            description: Todo description
            suggested_time: Suggested time to complete
            duration_minutes: Estimated duration
            priority: Priority level (high, medium, low)

        Returns:
            Event ID if successful, None otherwise
        """
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            priority, "⚪"
        )

        summary = f"{priority_emoji} TODO: {title}"
        full_description = f"Priority: {priority.upper()}\n\n{description}"

        return self.create_event(
            summary=summary,
            description=full_description,
            start_time=suggested_time,
            duration_minutes=duration_minutes,
        )

    def batch_create_todos(
        self, todos: List[dict], available_slots: List[datetime]
    ) -> List[str]:
        """
        Create multiple todos and schedule them in available slots.

        Args:
            todos: List of todo dictionaries with title, description, priority, duration
            available_slots: List of available time slots

        Returns:
            List of created event IDs
        """
        created_ids = []

        # Sort todos by priority (high -> medium -> low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_todos = sorted(
            todos, key=lambda x: priority_order.get(x.get("priority", "medium"), 1)
        )

        slot_index = 0
        for todo in sorted_todos:
            if slot_index >= len(available_slots):
                logger.warning("No more available slots for todos")
                break

            event_id = self.create_todo(
                title=todo["title"],
                description=todo.get("description", ""),
                suggested_time=available_slots[slot_index],
                duration_minutes=todo.get("duration_minutes", 30),
                priority=todo.get("priority", "medium"),
            )

            if event_id:
                created_ids.append(event_id)
                # Add buffer between tasks
                buffer_slots = (
                    self.config["buffer_minutes_between_tasks"] // 30
                )
                slot_index += 1 + buffer_slots
            else:
                slot_index += 1

        return created_ids
