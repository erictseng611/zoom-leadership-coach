# 🚀 Next Steps - Getting Started

You've successfully created the Zoom Leadership Coach application! Here's what to do next.

## ✅ What's Been Built

A complete Python application with:
- 📧 Gmail integration to fetch Zoom summaries
- 📅 Google Calendar integration for smart todo scheduling
- 🤖 AI-powered leadership coaching using Claude
- 📊 Detailed coaching reports
- ⏰ Automated daily processing
- 🔧 Full configuration system

## 📋 Your Setup Checklist

### 1. Install Dependencies (5 minutes)

```bash
cd ~/src/zoom-leadership-coach
./setup.sh
```

This creates a virtual environment and installs all Python packages.

### 2. Get Your Anthropic API Key (2 minutes)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to API Keys section
4. Create a new key
5. Copy the key (starts with `sk-ant-api03-`)

### 3. Configure API Keys (1 minute)

```bash
cd ~/src/zoom-leadership-coach
nano .env  # or use your favorite editor
```

Add this line:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Save and exit (Ctrl+O, Enter, Ctrl+X in nano).

### 4. Setup Google APIs (10 minutes)

Follow the detailed guide:

```bash
open GOOGLE_API_SETUP.md  # Or read it in your editor
```

This walks you through:
- Creating a Google Cloud project
- Enabling Gmail and Calendar APIs
- Creating OAuth credentials
- Downloading the credentials file

**Important:** Save the downloaded JSON file as:
```
credentials/google_credentials.json
```

### 5. Customize Your Leadership Principles (5 minutes)

```bash
nano config/leadership_principles.md
```

This is the most important file! It tells the AI coach:
- Your core leadership values
- What behaviors to look for
- What areas you're working on
- Red flags to watch for

The more specific you are, the better the coaching will be.

### 6. Run Initial Setup (2 minutes)

```bash
source venv/bin/activate
python -m src.main --setup
```

This will:
- Open a browser for Google authentication
- Test all your API connections
- Save authentication tokens

**You'll see a Google warning:** "This app isn't verified"
- This is normal! It's your own app.
- Click "Advanced" → "Go to Zoom Leadership Coach (unsafe)"
- Grant permissions for Gmail and Calendar

### 7. Process Your First Meeting! (1 minute)

```bash
python -m src.main
```

This will:
- Fetch Zoom summaries from your Gmail
- Analyze meetings with AI
- Create calendar todos
- Generate coaching reports

Check the output:
```bash
ls -la data/coaching_reports/
```

### 8. Review Your First Report

```bash
# Open the most recent report
open data/coaching_reports/*.md
# Or on Linux:
# xdg-open data/coaching_reports/*.md
```

Read through the coaching insights and see how it analyzed your meeting!

### 9. (Optional) Schedule Daily Runs

```bash
python -m src.main --schedule --run-time 20:00
```

This sets up automated daily processing at 8 PM.

## 🎯 Testing Without Real Emails

Want to test before you have Zoom summaries? Create a test transcript:

```bash
cat > test_meeting.txt << 'TRANSCRIPT'
Team Sync Meeting - Q2 Planning

Participants: Alice, Bob, Charlie

Summary:
We discussed Q2 priorities and decided to focus on the new payment integration.
Alice will lead the technical design. Bob will handle customer communication.

Action Items:
- Alice: Draft technical design document (Due: Friday)
- Bob: Schedule customer interviews (Due: Next week)
- Charlie: Research competitive solutions (Due: ASAP)

Decisions:
- Prioritize payment integration over reporting features
- Weekly check-ins every Monday at 2pm

Questions:
- Do we have budget approval for the third-party API?
- Should we wait for the mobile app release?
TRANSCRIPT

# Process it
python -m src.main --transcript test_meeting.txt

# Check the output
ls -la data/coaching_reports/
```

## 📚 Documentation Reference

- **README.md** - Full documentation
- **QUICKSTART.md** - Fast setup guide
- **GOOGLE_API_SETUP.md** - Detailed Google API setup
- **SAMPLE_REPORT.md** - Example coaching report
- **PROJECT_OVERVIEW.md** - Technical overview
- **NEXT_STEPS.md** - This file!

## 🔧 Configuration Files

- **config/settings.json** - App settings (work hours, email filters, etc.)
- **config/leadership_principles.md** - Your leadership framework
- **.env** - API keys (never commit to git)

## 🎨 Advanced Usage

### Process Specific Meeting from Zoom

If you configure Zoom API (optional):

```bash
python -m src.main --zoom-meeting-id 123456789
```

### View Verbose Logs

```bash
python -m src.main --verbose
```

### Customize Work Hours

Edit `config/settings.json`:

```json
{
  "scheduling": {
    "work_hours_start": "08:00",
    "work_hours_end": "18:00",
    "preferred_focus_times": ["08:00-10:00", "15:00-17:00"],
    "lunch_break": "12:00-13:00"
  }
}
```

### Change Email Filters

Edit `config/settings.json`:

```json
{
  "gmail": {
    "sender_filter": "no-reply@zoom.us",
    "subject_filter": "Meeting assets",
    "days_to_look_back": 14
  }
}
```

## ❓ Common Questions

**Q: Do I need a paid Anthropic account?**
A: You need API credits, but there's no monthly subscription. Pay as you go. Each meeting analysis costs ~$0.10-0.30.

**Q: Will this modify my emails?**
A: No, it only reads them. There's an optional `mark_as_read` feature, but it's disabled by default.

**Q: Can I use this with multiple Google accounts?**
A: Currently designed for one account. You can modify the code to support multiple accounts.

**Q: What if I don't use Zoom?**
A: You can still use the transcript feature! Just feed it any meeting transcript.

**Q: How do I stop the scheduled daily runs?**
A: Run `python -m src.main --unschedule`

**Q: Where is my data stored?**
A: Everything is local on your machine in the `data/` folder. Nothing is sent to external servers except the API calls to Google and Anthropic.

## 🐛 Troubleshooting

**"No module named X"**
```bash
source venv/bin/activate  # Activate the virtual environment
```

**"Google credentials not found"**
```bash
# Make sure the file exists
ls -la credentials/google_credentials.json
```

**"No emails found"**
```bash
# Check your Gmail for emails from no-reply@zoom.us
# Or adjust days_to_look_back in config/settings.json
```

**"API key invalid"**
```bash
# Check your .env file
cat .env | grep ANTHROPIC
# Make sure there are no extra spaces or quotes
```

**"Permission denied" on setup.sh**
```bash
chmod +x setup.sh
```

## 🎉 You're Ready!

Your application is complete and ready to use. Follow the checklist above and you'll be getting AI-powered leadership coaching in no time!

**Quick Start Command Sequence:**
```bash
cd ~/src/zoom-leadership-coach
./setup.sh
nano .env  # Add ANTHROPIC_API_KEY
# [Follow GOOGLE_API_SETUP.md to get OAuth credentials]
source venv/bin/activate
python -m src.main --setup
python -m src.main
```

Good luck with your leadership journey! 🚀
