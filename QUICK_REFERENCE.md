# Quick Reference Card

## Using AWS Bedrock (Your Setup)

```bash
# Authenticate (do this first, lasts 12 hours)
claude-up

# Run the app
cd ~/src/zoom-leadership-coach
./run.sh

# Or with options
./run.sh --transcript meeting.txt
./run.sh --verbose
```

## Common Commands

```bash
# Setup (first time only)
claude-up
cd ~/src/zoom-leadership-coach
source venv/bin/activate
python3 -m src.main --setup

# Process emails
./run.sh

# Process a transcript file
./run.sh --transcript path/to/file.txt

# Schedule daily runs (8 PM)
./run.sh --schedule --run-time 20:00

# Unschedule
./run.sh --unschedule

# View detailed logs
./run.sh --verbose
```

## Configuration

### Switch to Bedrock
Edit `.env`:
```
USE_BEDROCK=true
```

### Switch to Direct API
Edit `.env`:
```
USE_BEDROCK=false
ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### Customize Work Hours
Edit `config/settings.json`:
```json
{
  "scheduling": {
    "work_hours_start": "09:00",
    "work_hours_end": "17:00",
    "preferred_focus_times": ["09:00-11:00", "14:00-16:00"]
  }
}
```

## Output Locations

```bash
# Coaching reports
data/coaching_reports/

# View latest report
ls -lt data/coaching_reports/ | head -2
open data/coaching_reports/$(ls -t data/coaching_reports/ | head -1)

# Processing log
data/processed_emails.json
```

## Troubleshooting

### "Missing AWS credentials"
```bash
claude-up
```

### "No module named X"
```bash
source venv/bin/activate
```

### "No emails found"
```bash
# Increase lookback period in config/settings.json
"days_to_look_back": 14
```

### "Credentials expired"
```bash
claude-up  # Re-authenticate (needed every 12 hours)
```

## File Locations

```
~/src/zoom-leadership-coach/
├── config/
│   ├── settings.json              # App configuration
│   └── leadership_principles.md   # Your principles (EDIT THIS!)
├── credentials/
│   ├── google_credentials.json    # Google OAuth
│   └── token.pickle               # Auth token
├── data/
│   ├── coaching_reports/          # Generated reports
│   └── processed_emails.json      # Tracking
└── .env                           # API keys & settings
```

## Documentation

- `START_HERE.md` - Complete setup guide
- `BEDROCK_SETUP.md` - Bedrock details
- `CLAUDE_ACCESS_OPTIONS.md` - Compare Bedrock vs API
- `GOOGLE_API_SETUP.md` - Google OAuth setup
- `SAMPLE_REPORT.md` - Example output
