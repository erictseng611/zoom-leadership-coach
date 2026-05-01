# Quick Start: Todo Approval Workflow

## Running the Application

```bash
# Interactive approval (new default)
python -m src.main

# Automatic creation (legacy mode)
python -m src.main --auto-approve
```

## Approval Workflow Cheat Sheet

### When reviewing each action item:

```
1 = Accept and create     → Creates calendar event with current details
2 = Edit details          → Modify title, description, priority, duration
3 = Change time           → Select different time slot or enter custom time
4 = Skip this item        → Don't create calendar event for this item
```

### Editing Details

- **Title**: Press Enter to keep current, or type new title
- **Description**: Type new text, "clear" to remove, or Enter to keep
- **Priority**: Choose `high`, `medium`, or `low`
- **Duration**: Enter number of minutes (e.g., 15, 30, 60)

### Changing Time

- **Number (1-10)**: Select from available slots list
- **"custom"**: Enter custom time in format `YYYY-MM-DD HH:MM`
- **Enter**: Keep the suggested time

### Examples

#### Quick Accept
```
Choose action [1]: 1
Create this calendar event? [Y/n]: y
```

#### Edit Priority
```
Choose action [1]: 2
Priority [medium]: high
Create this calendar event? [Y/n]: y
```

#### Custom Time
```
Choose action [1]: 3
Select time slot [suggested]: custom
Custom time: 2026-05-02 14:00
Create this calendar event? [Y/n]: y
```

#### Skip Item
```
Choose action [1]: 4
Skipped
```

## Tips

- Press `Enter` to accept default values
- Type `n` to decline confirmation and return to options
- Use `Ctrl+C` to exit (already-approved items will be created)
- All times respect your configured work hours and lunch break

## Common Workflows

### Accept Most, Skip Some
- Press `1` then `Enter` for items you want
- Press `4` for items you want to skip

### Review and Adjust
- Press `1` then `Enter` for simple items
- Press `2` to edit complex items before accepting
- Press `3` to move items to better times

### Batch Processing
- Accept defaults quickly by pressing `1` then `Enter` repeatedly
- Or use `--auto-approve` flag to skip prompts entirely
