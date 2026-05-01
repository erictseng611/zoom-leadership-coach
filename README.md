# Zoom Leadership Coach

An AI-powered tool that processes Zoom meeting summaries from Gmail, analyzes them against your personal leadership principles, and helps you turn action items into scheduled Google Calendar todos.

## Features

- **Automated email processing**: Fetches Zoom AI summaries from Gmail
- **Interactive todo approval**: Review, edit, or skip each action item before it hits your calendar
- **Smart scheduling**: Suggests times based on your availability, due dates, and priority
- **Leadership coaching**: AI analysis using your own leadership principles
- **Flexible input**: Email, direct transcript files, or specific Zoom meeting IDs
- **Two Claude backends**: Anthropic API or AWS Bedrock

## Setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure APIs

- **Google (Gmail + Calendar)** — see [docs/SETUP_GOOGLE.md](docs/SETUP_GOOGLE.md)
- **Claude (Anthropic or Bedrock)** — see [docs/SETUP_CLAUDE.md](docs/SETUP_CLAUDE.md) and [docs/SETUP_BEDROCK.md](docs/SETUP_BEDROCK.md)

Copy `.env.example` to `.env` and fill in your keys.

### 3. Customize leadership principles

Edit `config/leadership_principles.md` with your own framework.

### 4. Run initial auth

```bash
python -m src.main --setup
```

This opens a browser to authorize Google API access.

## Usage

```bash
# Process new Zoom summaries from Gmail (interactive approval, default)
python -m src.main

# Auto-create all todos without prompts
python -m src.main --auto-approve

# Process a specific transcript file
python -m src.main --transcript path/to/transcript.txt

# Process a specific Zoom meeting
python -m src.main --zoom-meeting-id 123456789

# Limit to first N emails
python -m src.main --limit 3

# Only process meetings after a time
python -m src.main --after "today 9am"
python -m src.main --after "2026-05-01 14:00"

# Faster/cheaper analysis with Haiku
python -m src.main --fast
```

### Interactive todo approval

By default, every action item is shown in a table and you choose: accept, edit, reschedule, or skip. Use `--auto-approve` to skip this and create all todos automatically.

### Scheduled runs

`src/scheduler.py` sets up a daily launchd job on macOS. To modify the schedule, edit the plist directly or re-run `--schedule`.

## Configuration

`config/settings.json` controls filters, work hours, and scheduling preferences:

```json
{
  "gmail": {
    "sender_filter": "no-reply@zoom.us",
    "subject_filter": "Meeting assets",
    "days_to_look_back": 7
  },
  "calendar": {
    "default_event_duration_minutes": 30,
    "todo_calendar_name": "Tasks"
  },
  "scheduling": {
    "work_hours_start": "09:00",
    "work_hours_end": "17:00",
    "preferred_focus_times": ["09:00-11:00", "14:00-16:00"]
  }
}
```

## Project structure

```
zoom-leadership-coach/
├── src/
│   ├── main.py              # CLI entry point
│   ├── gmail_client.py      # Gmail API
│   ├── calendar_client.py   # Google Calendar API
│   ├── zoom_client.py       # Zoom API (optional)
│   ├── parser.py            # Parse meeting summaries
│   ├── coach.py             # Claude coaching (Anthropic + Bedrock)
│   ├── todo_approval.py     # Interactive approval workflow
│   ├── scheduler.py         # Daily-run scheduling
│   └── utils.py             # Shared helpers
├── config/
│   ├── settings.json
│   └── leadership_principles.md
├── docs/                    # Setup guides
├── credentials/             # API credentials (gitignored)
└── data/                    # Processed meetings + reports (gitignored)
```

## Output

Each run produces:
1. **Calendar events** for follow-up meetings
2. **Todo items** scheduled into available slots
3. **Coaching report** at `data/coaching_reports/YYYY-MM-DD-<slug>.md` with:
   - Meeting summary
   - Prioritized action items
   - Leadership insights based on your principles
   - Communication patterns

## Troubleshooting

- **Auth errors**: delete `credentials/token.pickle` and re-run `--setup`
- **No emails found**: check `config/settings.json` filters and date range
- **Calendar write fails**: make sure your Google account has calendar write permission
