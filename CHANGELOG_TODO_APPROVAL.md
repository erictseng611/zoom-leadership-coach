# Changelog: Manual Todo Approval Feature

## Summary

Added an interactive todo approval workflow that allows manual review and editing of action items before they're added to Google Calendar. This replaces the previous automatic calendar event creation with a user-controlled approval process.

## What Changed

### New Files

1. **`src/todo_approval.py`**
   - New module containing `TodoApprovalWorkflow` class
   - Implements interactive review, editing, and approval of todos
   - Uses `rich` library for interactive prompts and tables

2. **`MANUAL_TODO_APPROVAL.md`**
   - Comprehensive documentation for the new feature
   - Usage examples and troubleshooting guide

3. **`CHANGELOG_TODO_APPROVAL.md`**
   - This file documenting the changes

### Modified Files

1. **`src/main.py`**
   - Added import for `TodoApprovalWorkflow`
   - Added `--auto-approve` CLI flag to enable legacy behavior
   - Updated function signatures to pass `auto_approve` parameter:
     - `process_gmail_summaries()`
     - `process_transcript_file()`
     - `process_zoom_meeting()`
   - Modified todo creation logic to use approval workflow by default
   - Updated docstring to reflect new default behavior

2. **`README.md`**
   - Added "Interactive Todo Approval" to features list
   - Added documentation for `--auto-approve` flag
   - Added reference to detailed approval documentation

## Behavioral Changes

### Default Behavior (New)

When running `python -m src.main`:
1. Meetings are processed and analyzed as before
2. Action items are identified and prioritized
3. **NEW**: For each action item, the user is prompted to:
   - Review the todo details and suggested time
   - Edit the todo (title, description, priority, duration)
   - Change the scheduled time
   - Approve or skip the item
4. Only approved items are added to Google Calendar

### Legacy Behavior (--auto-approve flag)

When running `python -m src.main --auto-approve`:
- Maintains the previous automatic behavior
- All action items are automatically added to calendar
- No interactive prompts
- Useful for scheduled/automated runs

## New Features

### Interactive Review
- See all todo details before calendar creation
- Clear visual presentation with priority emojis
- Option to skip irrelevant items

### Todo Editing
- Edit title and description
- Change priority level (High/Medium/Low)
- Adjust duration (minutes)

### Time Selection
- View suggested time slot
- Choose from next 10 available slots
- Enter custom date/time
- Smart scheduling respects work hours and existing events

### User Experience
- Clean, table-based UI using `rich` library
- Intuitive menu-driven prompts
- Confirmation before creating each event
- Progress tracking (e.g., "Action Item 2/5")

## Migration Guide

### For Interactive Use

No changes required! The new behavior is the default:

```bash
# Before
python -m src.main

# After (same command, new interactive workflow)
python -m src.main
```

### For Automated/Scheduled Runs

Add the `--auto-approve` flag to maintain automatic behavior:

```bash
# Before
python -m src.main

# After (for cron jobs, launchd, etc.)
python -m src.main --auto-approve
```

### For Scheduled Setup

If you've already configured scheduled runs, update the command:

**macOS (launchd)**:
Edit `~/Library/LaunchAgents/com.user.zoom-leadership-coach.plist`
Add `--auto-approve` to the ProgramArguments array.

**Linux (cron)**:
```bash
crontab -e
# Add --auto-approve to the command
```

**Windows (Task Scheduler)**:
Update the task's action to include `--auto-approve`.

## Dependencies

No new dependencies required. The feature uses:
- `rich` (already in requirements.txt)
- Standard library modules

## Testing Recommendations

1. **Interactive Flow**: Run `python -m src.main` with test meeting data
2. **Edit Functionality**: Test editing title, description, priority, duration
3. **Time Selection**: Test selecting from list and custom time entry
4. **Skip Functionality**: Test skipping unwanted items
5. **Auto-approve Mode**: Verify `--auto-approve` flag works as before

## Rollback

To revert to automatic calendar creation:

1. **Temporary**: Use `--auto-approve` flag
2. **Permanent**: Revert changes to `src/main.py` to always use batch_create_todos()

## Future Enhancements

Potential improvements for future iterations:
- Bulk approve/skip operations
- Save approval preferences as templates
- Edit already-created calendar events
- Undo last approval
- Preview all items before starting approval flow
- Integration with task management systems beyond Google Calendar
