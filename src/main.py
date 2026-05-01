"""Main CLI entry point for Zoom Leadership Coach.

Presentation layer only — all business logic lives in `pipeline.py`. This
module handles argument parsing, terminal IO (rich console, spinners,
prompts via TodoApprovalWorkflow), and scheduler/setup commands.
"""

import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from .calendar_client import CalendarClient
from .coach import LeadershipCoach
from . import pipeline
from .gmail_client import GmailClient
from .scheduler import SchedulerSetup
from .todo_approval import TodoApprovalWorkflow
from .utils import (
    ensure_directories,
    get_data_path,
    get_leadership_principles_path,
    initialize_leadership_principles,
    setup_logging,
)
from .zoom_client import ZoomClient

load_dotenv()

console = Console()


def get_coach() -> LeadershipCoach:
    """Build a LeadershipCoach. Backend is selected by USE_BEDROCK env var."""
    return LeadershipCoach()


def parse_after_time(after_str: str) -> datetime:
    """Parse the --after time string into a datetime.

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


@click.command()
@click.option("--setup", is_flag=True, help="Run initial setup and authentication")
@click.option("--init-principles", is_flag=True, help="Create config/leadership_principles.md from the template")
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
    init_principles: bool,
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

    if init_principles:
        init_principles_file()
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


def init_principles_file():
    """Bootstrap config/leadership_principles.md from the template."""
    target = get_leadership_principles_path()

    if target.exists():
        console.print(
            Panel(
                f"Your leadership principles already exist at:\n  {target}\n\n"
                "To start over, delete the file first — I won't overwrite by default.",
                title="Leadership Principles",
                style="yellow",
            )
        )
        return

    try:
        path = initialize_leadership_principles()
    except Exception as e:
        console.print(f"[red]Could not create principles file: {e}[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"✓ Created {path}\n\n"
            "This file is your brief to the AI coach. Open it in your editor and\n"
            "customize it with your own values, frameworks, and growth edges.\n\n"
            "The template has inline instructions to guide you. The more specific\n"
            "and personal your edits, the better the coaching will be.\n\n"
            "When you're done, run: python -m src.main",
            title="Leadership Principles",
            style="green",
        )
    )


def _ensure_leadership_principles() -> bool:
    """During setup, offer to create the personal principles file if missing.

    Returns True if the file exists (already or after creation), False if the
    user declined to create one.
    """
    target = get_leadership_principles_path()
    if target.exists():
        console.print("[green]✓ Leadership principles found[/green]")
        return True

    console.print(
        "\n[yellow]No personal leadership principles file found.[/yellow]\n"
        "This file is what makes the coaching personal — without it the coach\n"
        "only has generic advice to give."
    )
    if not Confirm.ask("Create one from the template now?", default=True):
        console.print(
            "[dim]Skipped. You can create it later with: "
            "python -m src.main --init-principles[/dim]"
        )
        return False

    path = initialize_leadership_principles()
    console.print(f"[green]✓ Created {path}[/green]")
    console.print(
        "[cyan]Open that file in your editor and customize it before your "
        "first real run.[/cyan]"
    )
    return True


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
        # Leadership principles (personal, per-user)
        console.print("\n[cyan]Checking leadership principles...[/cyan]")
        _ensure_leadership_principles()

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
                f"Customize your coaching brief:\n  {get_leadership_principles_path()}\n\n"
                "Then run the application:\n"
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
    """Process Zoom summaries from Gmail. CLI presentation over pipeline.*"""
    cutoff_date = None
    if after_time:
        cutoff_date = parse_after_time(after_time)
        console.print(
            f"[cyan]Filtering meetings after: {cutoff_date.strftime('%Y-%m-%d %H:%M')}[/cyan]"
        )

    console.print(
        Panel("Processing Zoom meeting summaries from Gmail", title="Zoom Coach")
    )

    with console.status("[cyan]Fetching emails from Gmail...[/cyan]"):
        emails = pipeline.fetch_pending_emails(cutoff_date=cutoff_date, limit=limit)

    if not emails:
        console.print("[yellow]No new Zoom summaries found[/yellow]")
        return
    console.print(f"[green]Found {len(emails)} new meeting summary/summaries[/green]\n")

    calendar_client = CalendarClient()
    coach = get_coach()

    with console.status("[cyan]Checking calendar availability...[/cyan]"):
        available_slots = pipeline.compute_available_slots(calendar_client)
    console.print(f"[cyan]Available slots: {len(available_slots)}[/cyan]")

    for i, email in enumerate(emails, 1):
        console.print(
            f"\n[bold cyan]Processing meeting {i}/{len(emails)}[/bold cyan]"
        )
        _present_meeting_result(
            email, available_slots, coach, calendar_client, auto_approve
        )
        pipeline.mark_email_processed(email["id"])

    console.print(
        Panel(
            f"✓ Processed {len(emails)} meeting(s)\n\n"
            f"Coaching reports saved to: {get_data_path('coaching_reports')}",
            title="Complete",
            style="green",
        )
    )


def _present_meeting_result(email, available_slots, coach, calendar_client, auto_approve):
    """Run the pipeline for one email and narrate the result to the console."""
    with console.status("[cyan]Analyzing meeting with AI coach...[/cyan]") as status:
        def _progress(count: int) -> None:
            status.update(
                f"[cyan]Analyzing meeting with AI coach... ({count} chunks)[/cyan]"
            )

        result = pipeline.analyze_meeting(
            email,
            available_slots,
            coach=coach,
            on_chunk=_progress,
        )

    console.print(f"  Meeting: {result.meeting_title}")
    if result.stripped_personal_items:
        console.print(
            f"  [dim]Stripped {len(result.stripped_personal_items)} personal item(s) "
            f"from analysis[/dim]"
        )

    if result.error:
        console.print(f"  [red]✗ Coaching analysis failed: {result.error}[/red]")
        console.print(
            "  [yellow]Skipping report and todo scheduling for this meeting.[/yellow]"
        )
        return

    if result.report_path:
        console.print(
            f"  [green]✓ Coaching report saved: {result.report_path.name}[/green]"
        )

    if result.skipped_not_mine:
        console.print(
            f"  [dim]Skipped {len(result.skipped_not_mine)} item(s) owned by others[/dim]"
        )

    if not result.proposed_todos:
        if result.action_items:
            console.print("  [yellow]No user-owned work items to schedule[/yellow]")
        return

    if auto_approve:
        with console.status("[cyan]Creating calendar todos...[/cyan]"):
            created_ids = pipeline.apply_todos(result.proposed_todos, calendar_client)
        console.print(
            f"  [green]✓ Created {len(created_ids)} todo item(s) in calendar[/green]"
        )
    else:
        console.print(
            f"\n[cyan]Found {len(result.proposed_todos)} action item(s) to review[/cyan]"
        )
        # TodoApprovalWorkflow still expects the legacy dict shape + slots list.
        todos_for_calendar = [
            {
                "title": todo.title,
                "description": todo.description,
                "priority": todo.priority,
                "duration_minutes": todo.duration_minutes,
            }
            for todo in result.proposed_todos
        ]
        TodoApprovalWorkflow(calendar_client).approve_todos(
            todos_for_calendar, available_slots, result.meeting_title
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
        "summary": transcript_content[:500],
        "participants": [],
        "key_points": [],
        "action_items": [],
        "decisions": [],
        "questions": [],
        "raw_content": transcript_content,
    }

    calendar_client = CalendarClient()
    coach = get_coach()

    available_slots = pipeline.compute_available_slots(calendar_client)

    console.print("[cyan]Analyzing with AI coach...[/cyan]")
    analysis = coach.analyze_meeting(meeting_data, available_slots)

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

    process_transcript_file(transcript, logger, auto_approve)


if __name__ == "__main__":
    main()
