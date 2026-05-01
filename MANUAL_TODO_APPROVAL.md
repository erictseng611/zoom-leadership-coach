# Manual Todo Approval Feature

## Overview

The Zoom Leadership Coach now includes an **interactive todo approval workflow** that gives you full control over which action items are added to your calendar, when they're scheduled, and with what details.

## Default Behavior (New)

By default, after processing meeting summaries, you'll enter an interactive approval flow where you can:

1. **Review** each action item with its suggested time slot
2. **Edit** the todo details (title, description, priority, duration)
3. **Change** the suggested time to another available slot or custom time
4. **Approve or skip** each item individually

This ensures you only add todos that are truly relevant and scheduled at times that work for you.

## Usage

### Standard Mode (Interactive Approval)

Process meetings with interactive approval:

```bash
python -m src.main
```

For each action item, you'll see:
- The todo title, description, priority, and duration
- A suggested calendar time slot
- Options to:
  - Accept and create the calendar event
  - Edit the todo details
  - Change the scheduled time
  - Skip the item

### Legacy Mode (Auto-Approve)

To skip the approval step and automatically create all calendar events (previous behavior):

```bash
python -m src.main --auto-approve
```

## Interactive Workflow Details

### Review Screen

For each action item, you'll see:

```
Action Item 1/3

Title:        Follow up on Q2 planning
Description:  From meeting: Leadership Team Sync
              Owner: Eric Tseng
              Due: Friday
Priority:     🟡 MEDIUM
Duration:     30 minutes
Suggested Time: Thursday, May 01 at 02:00 PM

Options:
  1. Accept and create calendar event
  2. Edit details
  3. Change time
  4. Skip this item

Choose action [1]:
```

### Editing Details

When you choose to edit (option 2), you can modify:
- **Title**: The todo summary text
- **Description**: Additional context (can be cleared)
- **Priority**: High (🔴), Medium (🟡), or Low (🟢)
- **Duration**: How many minutes to block (default: 30)

### Changing Time

When you choose to change time (option 3), you can:
- Select from the next 10 available time slots
- Enter a custom date/time (format: `YYYY-MM-DD HH:MM`)
- Keep the suggested time

Example:
```
Available Time Slots

#  Date & Time              Day
1  May 01 at 02:00 PM (suggested)  Thursday
2  May 01 at 02:30 PM       Thursday
3  May 01 at 03:00 PM       Thursday
4  May 01 at 03:30 PM       Thursday
...

Options:
  - Enter a number (1-10) to select from list
  - Enter 'custom' to specify a custom time
  - Press Enter to keep suggested time

Select time slot [suggested]:
```

## Configuration

The approval workflow respects all existing configuration settings:

- **Work hours**: Only suggests times within your configured work hours
- **Lunch break**: Avoids scheduling during lunch
- **Buffer time**: Maintains buffer between consecutive todos
- **Preferred times**: Prioritizes your configured focus time windows

These are configured in `config/config.yaml`:

```yaml
scheduling:
  work_hours_start: "09:00"
  work_hours_end: "17:00"
  lunch_break: "12:00-13:00"
  preferred_focus_times:
    - "09:00-11:00"
    - "14:00-16:00"
```

## Examples

### Example 1: Accept with Default Settings

```
Action Item 1/1

Title:        Send project update to stakeholders
Priority:     🔴 HIGH
Suggested Time: Thursday, May 01 at 09:00 AM

Choose action [1]: 1
Create this calendar event? [Y/n]: y
✓ Calendar event created
```

### Example 2: Edit Priority and Accept

```
Action Item 1/1

Title:        Review design mockups
Priority:     🟡 MEDIUM
Suggested Time: Thursday, May 01 at 02:00 PM

Choose action [1]: 2

Edit Todo Details
Title [Review design mockups]:
Description [From meeting: Design Review]:
Priority [medium]: low
Duration (minutes) [30]: 15
✓ Details updated

Create this calendar event? [Y/n]: y
✓ Calendar event created
```

### Example 3: Change Time to Custom Slot

```
Action Item 1/1

Title:        Prepare Q2 goals presentation
Suggested Time: Thursday, May 01 at 02:00 PM

Choose action [1]: 3

Available Time Slots
...

Select time slot [suggested]: custom

Enter Custom Time
Format: YYYY-MM-DD HH:MM
Example: 2026-05-01 14:30

Custom time: 2026-05-02 10:00

Create this calendar event? [Y/n]: y
✓ Calendar event created
```

### Example 4: Skip Unwanted Item

```
Action Item 1/1

Title:        Read industry report
Priority:     🟢 LOW

Choose action [1]: 4
Skipped
```

## Integration with Scheduled Runs

When using the `--schedule` option for automated daily runs, you should:

1. Use `--auto-approve` flag for fully automated behavior
2. Or review and approve todos manually during a scheduled time each day

Example launchd/cron configuration with auto-approve:

```bash
python -m src.main --auto-approve
```

## Benefits

### More Control
- Only add todos you actually want to track
- Avoid cluttering your calendar with non-actionable items
- Adjust priorities based on current context

### Better Scheduling
- Move todos to times that better fit your energy levels
- Avoid conflicts the automated system couldn't detect
- Schedule follow-ups at more strategic times

### Immediate Editing
- Fix typos or unclear action item text
- Adjust durations based on actual effort needed
- Add context before it goes on your calendar

## Troubleshooting

### No Available Slots Found

If the system shows "No more available calendar slots", you can:
- Use option 3 (Change time) and enter a custom time
- Clear some existing calendar events to free up slots
- Extend the `days_ahead` parameter in the config

### Approval Flow Interrupted

If you interrupt the approval flow (Ctrl+C), already-approved todos will be created, but remaining items will be skipped. The meeting will still be marked as processed.

## Future Enhancements

Potential future improvements:
- Batch approval (approve multiple at once)
- Save approval decisions as templates
- Smart suggestions based on past approval patterns
- Undo/edit already-created calendar events
