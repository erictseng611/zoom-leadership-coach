"""Shared constants used across the application."""

# Granularity for walking the calendar when looking for free slots.
SLOT_GRANULARITY_MINUTES = 30

# Default duration for a TODO calendar event when none is specified.
DEFAULT_TODO_DURATION_MINUTES = 30

# Earliest time (from now) we're willing to schedule a TODO — avoids placing
# one a few minutes into the future.
MIN_LEAD_TIME_MINUTES = 15

PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def priority_emoji(priority: str) -> str:
    return PRIORITY_EMOJI.get(priority, "⚪")


def priority_sort_key(todo: dict) -> int:
    return PRIORITY_ORDER.get(todo.get("priority", "medium"), 1)
