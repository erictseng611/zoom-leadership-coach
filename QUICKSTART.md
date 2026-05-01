# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Gmail account
- Google Calendar
- Anthropic API key
- (Optional) Zoom account with API access

## Installation

### 1. Run the Setup Script

```bash
cd ~/src/zoom-leadership-coach
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create configuration files

### 2. Configure API Keys

Edit the `.env` file:

```bash
nano .env
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### 3. Setup Google APIs

#### A. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: "Zoom Leadership Coach"
3. In the sidebar, go to **APIs & Services > Library**

#### B. Enable Required APIs

Search for and enable:
- **Gmail API**
- **Google Calendar API**

#### C. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User type: **External**
   - App name: "Zoom Leadership Coach"
   - Add your email as a test user
4. Application type: **Desktop app**
5. Name: "Zoom Leadership Coach"
6. Click **CREATE**
7. Download the JSON file
8. Save it as: `credentials/google_credentials.json`

### 4. Customize Leadership Principles

Edit your personal leadership framework:

```bash
nano config/leadership_principles.md
```

This file guides the AI coach on how to analyze your meetings.

### 5. Run Initial Setup

Authenticate with Google:

```bash
source venv/bin/activate  # Activate virtual environment
python -m src.main --setup
```

This will:
- Open a browser for Google OAuth
- Verify all APIs are working
- Save authentication tokens

## Usage

### Process Emails On-Demand

```bash
python -m src.main
```

This will:
1. Fetch Zoom meeting summaries from Gmail
2. Parse meeting content
3. Analyze with AI coach
4. Create calendar todos with suggested times
5. Generate coaching reports

### Process a Direct Transcript

Have a meeting transcript file?

```bash
python -m src.main --transcript path/to/meeting_transcript.txt
```

### Process from Zoom API

If you configured Zoom API:

```bash
python -m src.main --zoom-meeting-id 123456789
```

### Schedule Daily Runs

Automatically process at end of day:

```bash
python -m src.main --schedule --run-time 20:00
```

## Output

After processing, you'll find:

### 1. Coaching Reports

Location: `data/coaching_reports/`

Example: `2026-04-30_20-15_team-sync.md`

Contains:
- Meeting effectiveness assessment
- Prioritized action items with time estimates
- Recommended schedule based on your calendar
- Leadership insights tied to your principles
- Areas for growth with specific examples
- Wins and positive reinforcement

### 2. Calendar Todos

Created in your Google Calendar with:
- Priority indicators (🔴 High, 🟡 Medium, 🟢 Low)
- Scheduled in available slots
- Smart timing based on task complexity
- Buffer time between tasks

### 3. Processing Log

Location: `data/processed_emails.json`

Tracks which emails have been processed to avoid duplicates.

## Configuration

### Adjust Settings

Edit `config/settings.json`:

```json
{
  "gmail": {
    "days_to_look_back": 7,
    "mark_as_read": false
  },
  "scheduling": {
    "work_hours_start": "09:00",
    "work_hours_end": "17:00",
    "preferred_focus_times": ["09:00-11:00", "14:00-16:00"]
  }
}
```

### Change Schedule Time

```bash
# Update to run at different time
python -m src.main --schedule --run-time 18:00
```

### Disable Schedule

```bash
python -m src.main --unschedule
```

## Troubleshooting

### "No module named 'google'"

Make sure you activated the virtual environment:
```bash
source venv/bin/activate
```

### "Google credentials not found"

Ensure you saved the OAuth JSON file to:
```
credentials/google_credentials.json
```

### "Token has been expired or revoked"

Delete the token and re-authenticate:
```bash
rm credentials/token.pickle
python -m src.main --setup
```

### "No new Zoom summaries found"

Check:
1. You have emails from `no-reply@zoom.us` with subject "Meeting assets"
2. The emails are within the `days_to_look_back` window
3. Adjust filters in `config/settings.json` if needed

### Permission Denied on setup.sh

Make the script executable:
```bash
chmod +x setup.sh
```

## Tips

1. **First Run**: Start with `--verbose` flag to see detailed processing:
   ```bash
   python -m src.main --verbose
   ```

2. **Test with Transcript**: Try a test transcript first before processing emails:
   ```bash
   echo "Test meeting content" > test.txt
   python -m src.main --transcript test.txt
   ```

3. **Review Reports**: Check the first few coaching reports to see if you want to adjust your `leadership_principles.md`

4. **Calendar Integration**: If todos aren't appearing, verify you have write access to your Google Calendar

5. **Customize Priorities**: Adjust priority keywords in `config/settings.json` to match your team's language

## Next Steps

- Review your first coaching report
- Adjust your leadership principles based on the analysis
- Configure your preferred focus times for optimal scheduling
- Set up the daily automated run
- (Optional) Configure Zoom API for direct transcript access

## Support

- Check the main [README.md](README.md) for detailed documentation
- Review configuration files in `config/`
- Enable verbose logging for debugging: `--verbose`

Happy coaching! 🎯
