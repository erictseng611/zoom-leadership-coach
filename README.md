# Zoom Leadership Coach

An AI-powered application that processes Zoom meeting summaries from Gmail, creates calendar events and todos, and provides personalized leadership coaching insights.

## Features

- **Automated Email Processing**: Fetches Zoom AI summaries from Gmail
- **Interactive Todo Approval**: Review and edit action items before adding to calendar
  - Edit todo details (title, description, priority, duration)
  - Choose from suggested time slots or enter custom times
  - Skip items that aren't relevant
- **Calendar Integration**: Creates events and todos in Google Calendar based on meeting content
- **Smart Scheduling**: Suggests optimal times to tackle todos based on:
  - Your calendar availability
  - Task due dates
  - Priority levels
- **Leadership Coaching**: AI-powered analysis using your personal leadership principles
- **Flexible Input**: Process emails automatically or feed direct meeting transcripts
- **Scheduled & On-Demand**: Runs daily at end of day, or manually when needed

## Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Google APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable APIs:
   - Gmail API
   - Google Calendar API
4. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download the JSON file
5. Save as `credentials/google_credentials.json`

### 3. Configure Anthropic API

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Add to `.env` file:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### 4. (Optional) Configure Zoom API

For direct transcript access:
1. Create a Server-to-Server OAuth app at [Zoom Marketplace](https://marketplace.zoom.us/)
2. Add to `.env`:
   ```
   ZOOM_ACCOUNT_ID=your_account_id
   ZOOM_CLIENT_ID=your_client_id
   ZOOM_CLIENT_SECRET=your_client_secret
   ```

### 5. Customize Leadership Principles

Edit `config/leadership_principles.md` with your personal leadership framework.

## Usage

### First Run (Authentication)

```bash
python -m src.main --setup
```

This will open a browser to authorize Google API access.

### On-Demand Processing

```bash
# Process new Zoom summaries from Gmail (interactive approval)
python -m src.main

# Skip approval and auto-create all todos (legacy mode)
python -m src.main --auto-approve

# Process a specific transcript file
python -m src.main --transcript path/to/transcript.txt

# Process a specific meeting ID from Zoom
python -m src.main --zoom-meeting-id 123456789
```

**Interactive Todo Approval**: By default, you'll review each action item before it's added to your calendar. See [MANUAL_TODO_APPROVAL.md](MANUAL_TODO_APPROVAL.md) for details on the approval workflow.

### Schedule Daily Runs

The setup creates a daily scheduled task (see installation output for details).

To modify the schedule:
```bash
# macOS/Linux (cron)
crontab -e

# Windows (Task Scheduler)
python -m src.scheduler --configure
```

## Configuration

Edit `config/settings.json`:

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
  "coaching": {
    "include_communication_analysis": true,
    "include_decision_making_review": true,
    "include_team_dynamics": true
  },
  "scheduling": {
    "work_hours_start": "09:00",
    "work_hours_end": "17:00",
    "preferred_focus_times": ["09:00-11:00", "14:00-16:00"]
  }
}
```

## Project Structure

```
zoom-leadership-coach/
├── src/
│   ├── main.py                  # CLI entry point
│   ├── gmail_client.py          # Gmail API integration
│   ├── calendar_client.py       # Google Calendar API integration
│   ├── zoom_client.py           # Zoom API integration (optional)
│   ├── parser.py                # Parse meeting summaries
│   ├── coach.py                 # AI leadership coaching
│   ├── scheduler.py             # Task scheduling logic
│   └── utils.py                 # Utilities
├── config/
│   ├── settings.json            # Application settings
│   └── leadership_principles.md # Your leadership framework
├── credentials/                 # API credentials (gitignored)
├── data/                        # Processed meetings & todos
└── requirements.txt
```

## Output

After processing, you'll receive:

1. **Calendar events** created for follow-up meetings
2. **Todo items** added to your calendar with suggested times
3. **Coaching report** (saved to `data/coaching_reports/YYYY-MM-DD.md`):
   - Meeting summary
   - Action items with prioritization
   - Suggested schedule for todos
   - Leadership insights based on your principles
   - Communication patterns and suggestions

## Troubleshooting

- **Authentication errors**: Delete `credentials/token.pickle` and re-run `--setup`
- **No emails found**: Check `config/settings.json` filters and date range
- **Calendar creation fails**: Ensure you have write permissions to your Google Calendar
