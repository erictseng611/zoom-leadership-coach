"""UI-free orchestration.

This module runs the same meeting-processing pipeline that the CLI drives, but
without any terminal IO, prompts, or logging decoration. Callers (CLI, web app,
desktop app, tests) import these functions to drive the work and render results
however they want.

Shape:
- `MeetingResult` — everything produced by analyzing one email.
- `analyze_meeting(email, ...)` — parse + coach + save report, returns MeetingResult.
- `apply_todos(...)` — create calendar events for an already-approved todo list.
- `fetch_pending_emails(...)` — list unprocessed Zoom summaries with filters applied.
- `mark_email_processed(email_id)` — persist that an email was handled.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .calendar_client import CalendarClient
from .coach import LeadershipCoach
from .constants import DEFAULT_TODO_DURATION_MINUTES
from .gmail_client import GmailClient
from .parser import MeetingSummaryParser
from .utils import get_data_path, load_config, load_json, save_json

logger = logging.getLogger("zoom_coach")

PROCESSED_EMAILS_FILE = "processed_emails.json"


@dataclass
class ProposedTodo:
    """A todo the pipeline proposes for scheduling, before any approval UI."""

    title: str
    description: str
    priority: str
    duration_minutes: int
    suggested_slot: Optional[datetime] = None


@dataclass
class MeetingResult:
    """Everything produced by analyzing one meeting email."""

    email_id: str
    meeting_title: str
    meeting_date: Optional[str]
    action_items: List[Dict]
    stripped_personal_items: List[Dict]
    skipped_not_mine: List[Dict]
    proposed_todos: List[ProposedTodo]
    report_path: Optional[Path] = None
    analysis: Dict = field(default_factory=dict)
    error: Optional[str] = None


# ---------- email discovery / state ----------


def fetch_pending_emails(
    gmail_client: Optional[GmailClient] = None,
    cutoff_date: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> List[Dict]:
    """Return unprocessed Zoom summary emails, filtered by cutoff / limit."""
    gmail_client = gmail_client or GmailClient()
    processed_ids = _load_processed_ids()
    emails = gmail_client.get_latest_unprocessed_summaries(processed_ids)

    if cutoff_date:
        emails = _filter_by_date(emails, cutoff_date)
    if limit is not None and limit > 0:
        emails = emails[:limit]
    return emails


def mark_email_processed(email_id: str) -> None:
    """Record that an email has been handled end-to-end."""
    path = get_data_path(PROCESSED_EMAILS_FILE)
    state = load_json(path)
    processed = state.get("processed_ids", [])
    if email_id not in processed:
        processed.append(email_id)
    save_json(
        {"processed_ids": processed, "last_run": datetime.now().isoformat()},
        path,
    )


def _load_processed_ids() -> List[str]:
    return load_json(get_data_path(PROCESSED_EMAILS_FILE)).get("processed_ids", [])


def _filter_by_date(emails: List[Dict], cutoff_date: datetime) -> List[Dict]:
    """Keep emails received at or after cutoff_date."""
    kept = []
    for email in emails:
        try:
            received = parsedate_to_datetime(email["date"]).replace(tzinfo=None)
        except Exception as e:
            logger.warning(f"Could not parse email date {email.get('date')!r}: {e}")
            kept.append(email)
            continue
        if received >= cutoff_date:
            kept.append(email)
    return kept


# ---------- per-meeting analysis ----------


def compute_available_slots(
    calendar_client: Optional[CalendarClient] = None,
    days_ahead: int = 14,
) -> List[datetime]:
    """Compute available calendar slots using the user's configured preferences."""
    calendar_client = calendar_client or CalendarClient()
    config = load_config()
    return calendar_client.find_available_slots(
        duration_minutes=DEFAULT_TODO_DURATION_MINUTES,
        days_ahead=days_ahead,
        preferred_times=config["scheduling"]["preferred_focus_times"],
    )


def analyze_meeting(
    email: Dict,
    available_slots: List[datetime],
    parser: Optional[MeetingSummaryParser] = None,
    coach: Optional[LeadershipCoach] = None,
    config: Optional[Dict] = None,
    on_chunk: Optional[Callable[[int], None]] = None,
    write_report: bool = True,
) -> MeetingResult:
    """Parse, coach-analyze, and propose todos for one email. No IO beyond the report file."""
    parser = parser or MeetingSummaryParser()
    coach = coach or LeadershipCoach()
    config = config or load_config()

    meeting_data = parser.parse(email["body"], email["subject"])
    email_id = email.get("id", "")

    # Drop personal items before they hit the coach prompt, report, or calendar.
    todo_cfg = config.get("todos", {})
    personal_items: List[Dict] = []
    if todo_cfg.get("skip_personal", True):
        work_items, personal_items = _partition_personal(
            meeting_data["action_items"],
            todo_cfg.get("personal_keywords", []),
        )
        meeting_data["action_items"] = work_items

    analysis = coach.analyze_meeting(meeting_data, available_slots, on_chunk=on_chunk)

    result = MeetingResult(
        email_id=email_id,
        meeting_title=meeting_data["title"],
        meeting_date=meeting_data.get("date"),
        action_items=meeting_data.get("action_items", []),
        stripped_personal_items=personal_items,
        skipped_not_mine=[],
        proposed_todos=[],
        analysis=analysis,
    )

    if analysis.get("error"):
        result.error = analysis["error"]
        return result

    if write_report:
        result.report_path = _write_report(coach, analysis, meeting_data["title"])

    user_cfg = config.get("user", {})
    user_names = [user_cfg.get("name", "")] + list(user_cfg.get("aliases", []))
    kept, not_mine = _partition_by_owner(meeting_data["action_items"], user_names)
    result.skipped_not_mine = not_mine
    result.proposed_todos = _build_proposed_todos(
        kept, meeting_data["title"], available_slots
    )

    return result


# ---------- todo application ----------


def apply_todos(
    todos: List[ProposedTodo],
    calendar_client: Optional[CalendarClient] = None,
) -> List[str]:
    """Create calendar events for a list of already-approved todos."""
    calendar_client = calendar_client or CalendarClient()
    created_ids: List[str] = []
    for todo in todos:
        if todo.suggested_slot is None:
            logger.warning(f"Skipping todo {todo.title!r}: no suggested slot")
            continue
        event_id = calendar_client.create_todo(
            title=todo.title,
            description=todo.description,
            suggested_time=todo.suggested_slot,
            duration_minutes=todo.duration_minutes,
            priority=todo.priority,
        )
        if event_id:
            created_ids.append(event_id)
    return created_ids


# ---------- internals ----------


def _normalize_name(name: str) -> str:
    return (name or "").strip().lower()


def _partition_personal(
    action_items: List[Dict], personal_keywords: List[str]
) -> tuple:
    """Split items into (work, personal) based on task-text keyword match."""
    keywords = [k.lower() for k in (personal_keywords or [])]
    work, personal = [], []
    for item in action_items:
        task_text = (item.get("task") or "").lower()
        if any(kw in task_text for kw in keywords):
            personal.append(item)
        else:
            work.append(item)
    return work, personal


def _partition_by_owner(
    action_items: List[Dict], user_names: List[str]
) -> tuple:
    """Split items into (user's, others') based on owner name match."""
    user_set = {_normalize_name(n) for n in user_names if n}
    mine, not_mine = [], []
    for item in action_items:
        owner = _normalize_name(item.get("owner", ""))
        if owner and owner in user_set:
            mine.append(item)
        else:
            not_mine.append(item)
    return mine, not_mine


def _build_proposed_todos(
    action_items: List[Dict],
    meeting_title: str,
    available_slots: List[datetime],
) -> List[ProposedTodo]:
    """Pair each action item with the next-available slot (if any)."""
    todos: List[ProposedTodo] = []
    for i, item in enumerate(action_items):
        slot = available_slots[i] if i < len(available_slots) else None
        todos.append(
            ProposedTodo(
                title=item["task"],
                description=(
                    f"From meeting: {meeting_title}\n"
                    f"Owner: {item.get('owner', 'Not assigned')}\n"
                    f"Due: {item.get('due_date', 'Not specified')}"
                ),
                priority=item.get("priority", "medium"),
                duration_minutes=DEFAULT_TODO_DURATION_MINUTES,
                suggested_slot=slot,
            )
        )
    return todos


def _write_report(coach: LeadershipCoach, analysis: Dict, meeting_title: str) -> Path:
    from .main import _slugify  # local import to avoid a module cycle

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    report_path = get_data_path("coaching_reports") / f"{stamp}_{_slugify(meeting_title)}.md"
    coach.generate_coaching_report(analysis, str(report_path))
    return report_path
