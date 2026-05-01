"""Main CLI entry point for Zoom Leadership Coach."""

import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from email.utils import parsedate_to_datetime

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from .calendar_client import CalendarClient
from .coach import LeadershipCoach
from .constants import DEFAULT_TODO_DURATION_MINUTES
from .gmail_client import GmailClient
from .parser import MeetingSummaryParser
from .scheduler import SchedulerSetup
from .todo_approval import TodoApprovalWorkflow
from .utils import (
    ensure_directories,
    get_data_path,
    load_config,
    load_json,
    save_json,
    setup_logging,
)
from .zoom_client import ZoomClient

# Load environment variables
load_dotenv()

console = Console()


def get_coach():
    """Build a LeadershipCoach. Backend is selected by USE_BEDROCK env var."""
    return LeadershipCoach()


def parse_after_time(after_str: str) -> datetime:
    """
    Parse the --after time string into a datetime.

    Accepts "YYYY-MM-DD", "YYYY-MM-DD HH:MM", and "today <HH:MM|HHam|HHpm>".
    """
    cleaned = after_str.strip().lower()

    if cleaned.startswith("today"):
        today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_part = cleaned[len("today"):].strip()
        for fmt in ("%I%p", "%I:%M%p", "%H:%M", "%H"):
            try:
                parsed_time = datetime.strptime(time_part, fmt).time()
                return today_midnight.replace(
                    hour=parsed_time.hour, minute=parsed_time.minute
                )
            except ValueError:
                continue
        raise ValueError(f"Could not parse time part of {after_str!r}")

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Could not parse time: {after_str}\n"
        "Supported formats: 'YYYY-MM-DD HH:MM', 'today 9am', 'today 14:00'"
    )


def _slugify(title: str, max_length: int = 30) -> str:
    """Turn a meeting title into a filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", title[:max_length].lower()).strip("-") or "meeting"


def _normalize_name(name: str) -> str:
    return (name or "").strip().lower()


def is_personal_item(item: dict, personal_keywords: list) -> bool:
    """True if the action item's text matches a personal keyword."""
    task_text = (item.get("task") or "").lower()
    return any(keyword.lower() in task_text for keyword in (personal_keywords or []))


def strip_personal_items(action_items: list, personal_keywords: list) -> tuple:
    """
    Return (work_items, personal_items) split.
    Work items are passed to the coach and report; personal are dropped.
    """
    work, personal = [], []
    for item in action_items:
        if is_personal_item(item, personal_keywords):
            personal.append(item)
        else:
            work.append(item)
    return work, personal


def filter_todo_candidates(
    action_items: list,
    user_names: list,
) -> tuple:
    """
    Partition (already-work-only) action items into (keep, skipped_not_mine).

    - keep: items owned by the user
    - skipped_not_mine: owner is another participant
    """
    user_set = {_normalize_name(n) for n in user_names if n}

    keep, not_mine = [], []
    for item in action_items:
        owner = _normalize_name(item.get("owner", ""))
        if not owner or owner not in user_set:
            not_mine.append(item)
            continue
        keep.append(item)

    return keep, not_mine


def filter_emails_by_date(emails: list, cutoff_date: datetime) -> list:
    """Filter emails to only those received after cutoff_date."""
    filtered = []
    for email in emails:
        try:
            # Parse the email date
            email_date = parsedate_to_datetime(email["date"])
            # Make it timezone-naive for comparison
            email_date = email_date.replace(tzinfo=None)

            if email_date >= cutoff_date:
                filtered.append(email)
        except Exception:
            # If we can't parse the date, include it to be safe
            filtered.append(email)

    return filtered


@click.command()
@click.option("--setup", is_flag=True, help="Run initial setup and authentication")
@click.option("--transcript", type=click.Path(exists=True), help="Process a transcript file directly")
@click.option("--zoom-meeting-id", help="Fetch and process a specific Zoom meeting")
@click.option("--schedule", is_flag=True, help="Setup automated daily runs")
@click.option("--unschedule", is_flag=True, help="Remove automated daily runs")
@click.option("--run-time", default="20:00", help="Time for daily runs (HH:MM format)")
@click.option("--after", help="Only process meetings after this time (format: 'YYYY-MM-DD HH:MM' or 'today 9am')")
@click.option("--limit", type=int, help="Only process the first N emails")
@click.option("--fast", is_flag=True, help="Use Claude Haiku for faster (cheaper, less deep) analysis")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--auto-approve", is_flag=True, help="Automatically create calendar events without approval (legacy mode)")
def main(
    setup: bool,
    transcript: str,
    zoom_meeting_id: str,
    schedule: bool,
    unschedule: bool,
    run_time: str,
    after: str,
    limit: int,
    fast: bool,
    verbose: bool,
    auto_approve: bool,
):
    """
    Zoom Leadership Coach - AI-powered meeting analysis and leadership coaching.

    Processes Zoom meeting summaries from Gmail, provides personalized leadership
    coaching insights, and allows interactive approval of calendar todos.

    By default, you'll review each action item before it's added to your calendar.
    Use --auto-approve to skip the review step (legacy behavior).
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)

    # --fast selects Haiku via env var read by the Bedrock provider
    if fast:
        os.environ["USE_FAST_MODEL"] = "true"

    # Ensure directories exist
    ensure_directories()

    # Handle setup mode
    if setup:
        run_setup()
        return

    # Handle scheduling
    if schedule:
        scheduler = SchedulerSetup(run_time)
        if scheduler.setup_daily_schedule():
            console.print(
                Panel(
                    f"✓ Scheduled daily runs at {run_time}",
                    title="Schedule Setup",
                    style="green",
                )
            )
        return

    if unschedule:
        scheduler = SchedulerSetup()
        if scheduler.remove_schedule():
            console.print(
                Panel("✓ Removed scheduled runs", title="Schedule", style="green")
            )
        return

    # Run the main processing workflow
    try:
        if transcript:
            process_transcript_file(transcript, logger, auto_approve)
        elif zoom_meeting_id:
            process_zoom_meeting(zoom_meeting_id, logger, auto_approve)
        else:
            process_gmail_summaries(logger, after_time=after, limit=limit, auto_approve=auto_approve)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def run_setup():
    """Run initial setup and authentication."""
    console.print(
        Panel(
            "Welcome to Zoom Leadership Coach!\n\n"
            "This will guide you through initial setup and authentication.",
            title="Setup",
            style="cyan",
        )
    )

    try:
        # Test Gmail authentication
        console.print("\n[cyan]Authenticating with Gmail...[/cyan]")
        GmailClient()
        console.print("[green]✓ Gmail authentication successful[/green]")

        # Test Calendar authentication
        console.print("\n[cyan]Authenticating with Google Calendar...[/cyan]")
        CalendarClient()
        console.print("[green]✓ Calendar authentication successful[/green]")

        # Test Claude API (Anthropic or Bedrock)
        use_bedrock = os.getenv("USE_BEDROCK", "false").lower() == "true"
        if use_bedrock:
            console.print("\n[cyan]Testing AWS Bedrock access...[/cyan]")
        else:
            console.print("\n[cyan]Testing Anthropic API...[/cyan]")

        get_coach()

        if use_bedrock:
            console.print("[green]✓ AWS Bedrock configured[/green]")
        else:
            console.print("[green]✓ Anthropic API configured[/green]")

        # Optional: Test Zoom API
        console.print("\n[cyan]Testing Zoom API (optional)...[/cyan]")
        zoom_client = ZoomClient()
        if zoom_client.enabled:
            console.print("[green]✓ Zoom API configured[/green]")
        else:
            console.print("[yellow]⚠ Zoom API not configured (optional)[/yellow]")

        console.print(
            Panel(
                "✓ Setup complete!\n\n"
                "You can now run the application:\n"
                "  python -m src.main\n\n"
                "Or schedule daily runs:\n"
                "  python -m src.main --schedule --run-time 20:00",
                title="Success",
                style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        console.print(
            "\n[yellow]Please check the README for setup instructions.[/yellow]"
        )
        sys.exit(1)


def process_gmail_summaries(
    logger: logging.Logger,
    after_time: str = None,
    limit: int = None,
    auto_approve: bool = False,
):
    """Process Zoom summaries from Gmail."""
    cutoff_date = None
    if after_time:
        cutoff_date = parse_after_time(after_time)
        console.print(
            f"[cyan]Filtering meetings after: {cutoff_date.strftime('%Y-%m-%d %H:%M')}[/cyan]"
        )

    console.print(
        Panel("Processing Zoom meeting summaries from Gmail", title="Zoom Coach")
    )

    processed_file = get_data_path("processed_emails.json")
    processed_ids = load_json(processed_file).get("processed_ids", [])

    with console.status("[cyan]Fetching emails from Gmail...[/cyan]"):
        emails = GmailClient().get_latest_unprocessed_summaries(processed_ids)
    emails = _apply_email_filters(emails, cutoff_date, limit)

    if not emails:
        console.print("[yellow]No new Zoom summaries found[/yellow]")
        return
    console.print(f"[green]Found {len(emails)} new meeting summary/summaries[/green]\n")

    parser = MeetingSummaryParser()
    calendar_client = CalendarClient()
    coach = get_coach()
    config = load_config()

    with console.status("[cyan]Checking calendar availability...[/cyan]"):
        available_slots = calendar_client.find_available_slots(
            duration_minutes=DEFAULT_TODO_DURATION_MINUTES,
            days_ahead=14,
            preferred_times=config["scheduling"]["preferred_focus_times"],
        )
    console.print(f"[cyan]Available slots: {len(available_slots)}[/cyan]")

    for i, email in enumerate(emails, 1):
        console.print(
            f"\n[bold cyan]Processing meeting {i}/{len(emails)}[/bold cyan]"
        )
        _process_one_email(
            email=email,
            parser=parser,
            coach=coach,
            calendar_client=calendar_client,
            available_slots=available_slots,
            config=config,
            auto_approve=auto_approve,
        )
        processed_ids.append(email["id"])

    save_json(
        {"processed_ids": processed_ids, "last_run": datetime.now().isoformat()},
        processed_file,
    )
    console.print(
        Panel(
            f"✓ Processed {len(emails)} meeting(s)\n\n"
            f"Coaching reports saved to: {get_data_path('coaching_reports')}",
            title="Complete",
            style="green",
        )
    )


def _apply_email_filters(emails, cutoff_date, limit):
    if cutoff_date:
        emails = filter_emails_by_date(emails, cutoff_date)
        console.print(
            f"[cyan]Filtered to {len(emails)} meeting(s) after cutoff[/cyan]"
        )
    if limit is not None and limit > 0:
        emails = emails[:limit]
        console.print(f"[cyan]Limited to first {len(emails)} meeting(s)[/cyan]")
    return emails


def _process_one_email(
    email, parser, coach, calendar_client, available_slots, config, auto_approve
):
    meeting_data = parser.parse(email["body"], email["subject"])
    console.print(f"  Meeting: {meeting_data['title']}")

    # Drop personal items before they hit the coach prompt, report, or calendar.
    todo_cfg = config.get("todos", {})
    if todo_cfg.get("skip_personal", True):
        work_items, personal_items = strip_personal_items(
            meeting_data["action_items"],
            todo_cfg.get("personal_keywords", []),
        )
        meeting_data["action_items"] = work_items
        if personal_items:
            console.print(
                f"  [dim]Stripped {len(personal_items)} personal item(s) from analysis[/dim]"
            )

    with console.status("[cyan]Analyzing meeting with AI coach...[/cyan]"):
        analysis = coach.analyze_meeting(meeting_data, available_slots)

    if analysis.get("error"):
        console.print(
            f"  [red]✗ Coaching analysis failed: {analysis['error']}[/red]"
        )
        console.print(
            "  [yellow]Skipping report and todo scheduling for this meeting.[/yellow]"
        )
        return

    report_path = (
        get_data_path("coaching_reports")
        / f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_{_slugify(meeting_data['title'])}.md"
    )
    coach.generate_coaching_report(analysis, str(report_path))
    console.print(f"  [green]✓ Coaching report saved: {report_path.name}[/green]")

    if not meeting_data["action_items"]:
        return

    user_cfg = config.get("user", {})
    user_names = [user_cfg.get("name", "")] + list(user_cfg.get("aliases", []))
    kept, not_mine = filter_todo_candidates(meeting_data["action_items"], user_names=user_names)

    if not_mine:
        console.print(f"  [dim]Skipped {len(not_mine)} item(s) owned by others[/dim]")

    if not kept:
        console.print("  [yellow]No user-owned work items to schedule[/yellow]")
        return

    todos_for_calendar = [
        {
            "title": item["task"],
            "description": (
                f"From meeting: {meeting_data['title']}\n"
                f"Owner: {item.get('owner', 'Not assigned')}\n"
                f"Due: {item.get('due_date', 'Not specified')}"
            ),
            "priority": item.get("priority", "medium"),
            "duration_minutes": DEFAULT_TODO_DURATION_MINUTES,
        }
        for item in kept
    ]

    if auto_approve:
        with console.status("[cyan]Creating calendar todos...[/cyan]"):
            created_ids = calendar_client.batch_create_todos(todos_for_calendar, available_slots)
        console.print(
            f"  [green]✓ Created {len(created_ids)} todo item(s) in calendar[/green]"
        )
    else:
        console.print(f"\n[cyan]Found {len(kept)} action item(s) to review[/cyan]")
        TodoApprovalWorkflow(calendar_client).approve_todos(
            todos_for_calendar, available_slots, meeting_data["title"]
        )


def process_transcript_file(file_path: str, logger: logging.Logger, auto_approve: bool = False):
    """Process a transcript from a file."""
    console.print(f"[cyan]Processing transcript file: {file_path}[/cyan]")

    with open(file_path, "r") as f:
        transcript_content = f.read()

    # Create a pseudo-meeting structure
    meeting_data = {
        "title": Path(file_path).stem.replace("_", " ").title(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summary": transcript_content[:500],  # First 500 chars as summary
        "participants": [],
        "key_points": [],
        "action_items": [],
        "decisions": [],
        "questions": [],
        "raw_content": transcript_content,
    }

    # Initialize clients
    calendar_client = CalendarClient()
    coach = get_coach()

    # Get calendar availability
    available_slots = calendar_client.find_available_slots(
        duration_minutes=30,
        days_ahead=14,
        preferred_times=load_config()["scheduling"]["preferred_focus_times"],
    )

    # Analyze with coach
    console.print("[cyan]Analyzing with AI coach...[/cyan]")
    analysis = coach.analyze_meeting(meeting_data, available_slots)

    # Save report
    report_path = get_data_path("coaching_reports") / f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_transcript.md"
    coach.generate_coaching_report(analysis, str(report_path))

    console.print(f"[green]✓ Coaching report saved: {report_path}[/green]")


def process_zoom_meeting(meeting_id: str, logger: logging.Logger, auto_approve: bool = False):
    """Process a specific Zoom meeting by ID."""
    console.print(f"[cyan]Fetching Zoom meeting: {meeting_id}[/cyan]")

    zoom_client = ZoomClient()
    if not zoom_client.enabled:
        console.print("[red]Zoom API not configured. Please add credentials to .env[/red]")
        return

    transcript = zoom_client.get_meeting_transcript(meeting_id)
    if not transcript:
        console.print("[red]Could not fetch transcript[/red]")
        return

    # Process as transcript file
    process_transcript_file(transcript, logger, auto_approve)


if __name__ == "__main__":
    main()
