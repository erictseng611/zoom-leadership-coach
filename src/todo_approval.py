"""Interactive approval workflow for calendar todos."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

logger = logging.getLogger("zoom_coach")
console = Console()


class TodoApprovalWorkflow:
    """Interactive workflow for approving and editing todos before calendar creation."""

    def __init__(self, calendar_client):
        """
        Initialize the approval workflow.

        Args:
            calendar_client: CalendarClient instance for creating approved events
        """
        self.calendar_client = calendar_client
        self.console = console

    def approve_todos(
        self,
        todos: List[Dict],
        available_slots: List[datetime],
        meeting_title: str,
    ) -> List[str]:
        """
        Interactive approval workflow for todos.

        Args:
            todos: List of todo dictionaries with title, description, priority, duration
            available_slots: List of available time slots
            meeting_title: Title of the meeting for context

        Returns:
            List of created event IDs
        """
        if not todos:
            return []

        self.console.print(
            Panel(
                f"[bold]Review and approve {len(todos)} action item(s) from:[/bold]\n{meeting_title}",
                title="Todo Approval",
                style="cyan",
            )
        )

        # Sort todos by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_todos = sorted(
            todos, key=lambda x: priority_order.get(x.get("priority", "medium"), 1)
        )

        approved_events = []
        slot_index = 0

        for index, todo in enumerate(sorted_todos, 1):
            self.console.print(f"\n[bold cyan]Action Item {index}/{len(sorted_todos)}[/bold cyan]")

            # Check if we have available slots
            if slot_index >= len(available_slots):
                self.console.print(
                    "[yellow]⚠ No more available calendar slots. Remaining todos will be skipped.[/yellow]"
                )
                break

            # Show the current todo
            suggested_slot = available_slots[slot_index]
            edited_todo, edited_slot = self._review_and_edit_todo(
                todo, suggested_slot, available_slots[slot_index:]
            )

            if edited_todo is None:
                # User chose to skip this todo
                self.console.print("[dim]Skipped[/dim]")
                continue

            # Ask for final confirmation
            if not Confirm.ask("Create this calendar event?", default=True):
                self.console.print("[dim]Skipped[/dim]")
                continue

            # Create the calendar event
            event_id = self.calendar_client.create_todo(
                title=edited_todo["title"],
                description=edited_todo["description"],
                suggested_time=edited_slot,
                duration_minutes=edited_todo.get("duration_minutes", 30),
                priority=edited_todo.get("priority", "medium"),
            )

            if event_id:
                approved_events.append(event_id)
                self.console.print("[green]✓ Calendar event created[/green]")

                # Update slot index with buffer
                buffer_slots = (
                    self.calendar_client.config["buffer_minutes_between_tasks"] // 30
                )
                # Find the index of the used slot and advance
                if edited_slot in available_slots:
                    slot_index = available_slots.index(edited_slot) + 1 + buffer_slots
                else:
                    slot_index += 1 + buffer_slots
            else:
                self.console.print("[red]✗ Failed to create calendar event[/red]")

        self.console.print(
            f"\n[green]Created {len(approved_events)} calendar event(s)[/green]"
        )
        return approved_events

    def _review_and_edit_todo(
        self,
        todo: Dict,
        suggested_slot: datetime,
        remaining_slots: List[datetime],
    ) -> Tuple[Optional[Dict], Optional[datetime]]:
        """
        Show a todo and allow user to edit or skip.

        Args:
            todo: Todo dictionary
            suggested_slot: Suggested time slot
            remaining_slots: List of remaining available slots

        Returns:
            Tuple of (edited_todo, selected_slot) or (None, None) if skipped
        """
        # Display the todo details
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            todo.get("priority", "medium"), "⚪"
        )

        table.add_row("Title", todo["title"])
        table.add_row("Description", todo.get("description", ""))
        table.add_row("Priority", f"{priority_emoji} {todo.get('priority', 'medium').upper()}")
        table.add_row("Duration", f"{todo.get('duration_minutes', 30)} minutes")
        table.add_row(
            "Suggested Time",
            suggested_slot.strftime("%A, %B %d at %I:%M %p"),
        )

        self.console.print(table)

        # Ask what the user wants to do
        self.console.print("\nOptions:")
        self.console.print("  1. Accept and create calendar event")
        self.console.print("  2. Edit details")
        self.console.print("  3. Change time")
        self.console.print("  4. Skip this item")

        choice = IntPrompt.ask(
            "Choose action",
            choices=["1", "2", "3", "4"],
            default=1,
        )

        if choice == 4:
            return None, None

        edited_todo = todo.copy()
        selected_slot = suggested_slot

        if choice == 2:
            # Edit details
            edited_todo = self._edit_todo_details(edited_todo)

        if choice == 3:
            # Change time
            selected_slot = self._select_time_slot(remaining_slots, suggested_slot)

        return edited_todo, selected_slot

    def _edit_todo_details(self, todo: Dict) -> Dict:
        """
        Allow user to edit todo details.

        Args:
            todo: Original todo dictionary

        Returns:
            Edited todo dictionary
        """
        self.console.print("\n[bold]Edit Todo Details[/bold]")

        edited = todo.copy()

        # Edit title
        new_title = Prompt.ask("Title", default=todo["title"])
        if new_title:
            edited["title"] = new_title

        # Edit description
        self.console.print(
            "[dim]Description (press Enter to keep current, 'clear' to remove):[/dim]"
        )
        new_description = Prompt.ask("Description", default=todo.get("description", ""))
        if new_description.lower() == "clear":
            edited["description"] = ""
        elif new_description:
            edited["description"] = new_description

        # Edit priority
        current_priority = todo.get("priority", "medium")
        new_priority = Prompt.ask(
            "Priority",
            choices=["high", "medium", "low"],
            default=current_priority,
        )
        edited["priority"] = new_priority

        # Edit duration
        current_duration = todo.get("duration_minutes", 30)
        new_duration = IntPrompt.ask(
            "Duration (minutes)",
            default=current_duration,
        )
        edited["duration_minutes"] = new_duration

        self.console.print("[green]✓ Details updated[/green]")
        return edited

    def _select_time_slot(
        self,
        available_slots: List[datetime],
        suggested_slot: datetime,
    ) -> datetime:
        """
        Allow user to select a different time slot.

        Args:
            available_slots: List of available slots
            suggested_slot: Currently suggested slot

        Returns:
            Selected datetime slot
        """
        self.console.print("\n[bold]Available Time Slots[/bold]")

        # Show next 10 slots
        display_slots = available_slots[:10]

        table = Table(show_header=True)
        table.add_column("#", style="cyan")
        table.add_column("Date & Time")
        table.add_column("Day")

        for i, slot in enumerate(display_slots, 1):
            marker = " (suggested)" if slot == suggested_slot else ""
            table.add_row(
                str(i),
                slot.strftime("%b %d at %I:%M %p") + marker,
                slot.strftime("%A"),
            )

        self.console.print(table)

        # Allow custom time or selection
        self.console.print("\nOptions:")
        self.console.print("  - Enter a number (1-10) to select from list")
        self.console.print("  - Enter 'custom' to specify a custom time")
        self.console.print("  - Press Enter to keep suggested time")

        response = Prompt.ask("Select time slot", default="suggested")

        if response.lower() == "custom":
            return self._enter_custom_time()

        if response.lower() == "suggested":
            return suggested_slot

        try:
            slot_index = int(response) - 1
            if 0 <= slot_index < len(display_slots):
                return display_slots[slot_index]
            else:
                self.console.print("[yellow]Invalid selection, using suggested time[/yellow]")
                return suggested_slot
        except ValueError:
            self.console.print("[yellow]Invalid input, using suggested time[/yellow]")
            return suggested_slot

    def _enter_custom_time(self) -> datetime:
        """
        Allow user to enter a custom time.

        Returns:
            Custom datetime
        """
        self.console.print("\n[bold]Enter Custom Time[/bold]")
        self.console.print("Format: YYYY-MM-DD HH:MM (24-hour)")
        self.console.print("Example: 2026-05-01 14:30")

        while True:
            time_str = Prompt.ask("Custom time")
            try:
                custom_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                return custom_time
            except ValueError:
                self.console.print(
                    "[red]Invalid format. Please use: YYYY-MM-DD HH:MM[/red]"
                )
