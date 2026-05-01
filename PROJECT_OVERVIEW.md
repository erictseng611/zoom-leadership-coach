# Zoom Leadership Coach - Project Overview

## 🎯 What This Application Does

An AI-powered leadership coaching application that:
1. **Fetches** Zoom meeting summaries from your Gmail
2. **Parses** meeting content (action items, participants, decisions)
3. **Analyzes** meetings using Claude AI based on your personal leadership principles
4. **Creates** smart calendar todos scheduled in your available time slots
5. **Generates** detailed coaching reports with actionable insights

## 📁 Project Structure

```
zoom-leadership-coach/
├── 📄 README.md                    # Comprehensive project documentation
├── 📄 QUICKSTART.md                # 5-minute getting started guide
├── 📄 GOOGLE_API_SETUP.md          # Step-by-step Google API setup
├── 📄 SAMPLE_REPORT.md             # Example coaching report output
├── 📄 PROJECT_OVERVIEW.md          # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment variables template
├── 📄 .gitignore                   # Git ignore rules
├── 🔧 setup.sh                     # Automated setup script
│
├── 📂 config/                      # Configuration files
│   ├── settings.json               # Application settings
│   └── leadership_principles.md   # Your personal leadership framework
│
├── 📂 credentials/                 # API credentials (gitignored)
│   ├── google_credentials.json    # Google OAuth credentials (you add)
│   └── token.pickle                # Auth token (auto-generated)
│
├── 📂 data/                        # Application data
│   ├── processed_emails.json      # Tracking of processed emails
│   ├── coaching_reports/           # Generated coaching reports
│   └── todos/                      # Todo tracking data
│
└── 📂 src/                         # Source code
    ├── __init__.py                 # Package initialization
    ├── main.py                     # CLI entry point
    ├── gmail_client.py             # Gmail API integration
    ├── calendar_client.py          # Google Calendar API integration
    ├── zoom_client.py              # Zoom API integration (optional)
    ├── parser.py                   # Meeting summary parser
    ├── coach.py                    # AI leadership coach
    ├── scheduler.py                # Task scheduling logic
    └── utils.py                    # Utility functions
```

## 🔄 Application Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER TRIGGERS RUN                        │
│  (End of day schedule OR on-demand command)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   GMAIL CLIENT                │
         │   • Fetch emails from         │
         │     no-reply@zoom.us          │
         │   • Filter "Meeting assets"   │
         │   • Check against processed   │
         │     list to avoid duplicates  │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │   MEETING PARSER              │
         │   • Extract meeting title     │
         │   • Parse action items        │
         │   • Identify participants     │
         │   • Extract decisions         │
         │   • Determine priorities      │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │   CALENDAR CLIENT             │
         │   • Fetch free/busy data      │
         │   • Find available time slots │
         │   • Consider work hours       │
         │   • Respect lunch breaks      │
         │   • Prioritize focus times    │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │   AI LEADERSHIP COACH         │
         │   • Load leadership principles│
         │   • Analyze meeting content   │
         │   • Evaluate communication    │
         │   • Review decision-making    │
         │   • Suggest improvements      │
         │   • Prioritize action items   │
         │   • Recommend schedule        │
         └───────────┬───────────────────┘
                     │
                     ├─────────────────┬─────────────────┐
                     ▼                 ▼                 ▼
         ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
         │ CALENDAR       │ │ COACHING       │ │ TRACKING       │
         │ Create todos   │ │ Save report    │ │ Mark as        │
         │ with priority  │ │ (.md file)     │ │ processed      │
         │ indicators     │ │                │ │                │
         └────────────────┘ └────────────────┘ └────────────────┘
```

## 🚀 Quick Start Commands

```bash
# 1. Initial setup
cd ~/src/zoom-leadership-coach
./setup.sh

# 2. Add your API keys
nano .env  # Add ANTHROPIC_API_KEY

# 3. Add Google OAuth credentials
# (Follow GOOGLE_API_SETUP.md)
# Save to: credentials/google_credentials.json

# 4. Authenticate with Google
source venv/bin/activate
python -m src.main --setup

# 5. Customize your leadership principles
nano config/leadership_principles.md

# 6. Process meetings on-demand
python -m src.main

# 7. Schedule daily runs (end of day)
python -m src.main --schedule --run-time 20:00
```

## 🔑 Required API Keys & Credentials

| Service | Required | How to Get | Where to Put |
|---------|----------|------------|--------------|
| **Anthropic Claude** | ✅ Yes | [console.anthropic.com](https://console.anthropic.com/) | `.env` → `ANTHROPIC_API_KEY` |
| **Google OAuth 2.0** | ✅ Yes | See `GOOGLE_API_SETUP.md` | `credentials/google_credentials.json` |
| **Zoom API** | ⚪ Optional | [marketplace.zoom.us](https://marketplace.zoom.us/) | `.env` → `ZOOM_*` vars |

## 📊 What You Get

### 1. **Coaching Reports** (`data/coaching_reports/`)

Each report includes:
- ✅ Meeting effectiveness assessment (with ratings)
- ✅ Prioritized action items with time estimates
- ✅ Recommended schedule based on your availability
- ✅ Leadership insights aligned with your principles
- ✅ Communication pattern analysis
- ✅ Areas for growth with specific examples
- ✅ Wins and positive reinforcement

**See:** `SAMPLE_REPORT.md` for a full example

### 2. **Smart Calendar Todos**

Created in Google Calendar with:
- 🔴 High priority indicator
- 🟡 Medium priority indicator
- 🟢 Low priority indicator
- ⏰ Scheduled in optimal time slots
- 📋 Context from the meeting
- ⚡ Buffer time between tasks

### 3. **Processing Logs** (`data/processed_emails.json`)

Tracks which emails have been processed to prevent duplicates.

## ⚙️ Configuration Options

### `config/settings.json`

```json
{
  "gmail": {
    "days_to_look_back": 7,           // How far back to search
    "mark_as_read": false             // Mark processed emails as read
  },
  "scheduling": {
    "work_hours_start": "09:00",      // Your work day start
    "work_hours_end": "17:00",        // Your work day end
    "preferred_focus_times": [        // Best times for complex work
      "09:00-11:00",
      "14:00-16:00"
    ],
    "lunch_break": "12:00-13:00"     // Don't schedule during lunch
  },
  "calendar": {
    "buffer_minutes_between_tasks": 15  // Break between todos
  },
  "coaching": {
    "include_communication_analysis": true,
    "include_decision_making_review": true,
    "include_team_dynamics": true
  }
}
```

### `config/leadership_principles.md`

Your personal leadership framework that guides the AI coach. Customize:
- Core values
- Communication style goals
- Areas you're working on
- Red flags to watch for
- Meeting analysis preferences

## 🎨 Use Cases

### 1. **Daily End-of-Day Processing**
```bash
# Schedule to run automatically at 8 PM
python -m src.main --schedule --run-time 20:00
```

**What happens:**
- Fetches all new Zoom summaries from today
- Analyzes meetings and creates coaching reports
- Schedules todos for tomorrow/next few days

### 2. **On-Demand Processing**
```bash
# Process immediately when you need it
python -m src.main
```

### 3. **Direct Transcript Processing**
```bash
# Process a transcript file directly (not from email)
python -m src.main --transcript path/to/transcript.txt
```

**Use when:**
- Meeting wasn't recorded via Zoom
- You have a transcript from another source
- You want to analyze a specific conversation

### 4. **Zoom API Integration**
```bash
# Fetch directly from Zoom by meeting ID
python -m src.main --zoom-meeting-id 123456789
```

**Use when:**
- You want the full transcript, not just the summary
- Email summary wasn't detailed enough

## 🏗️ Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.8+ | Core application |
| **AI Model** | Claude Sonnet 4.5 | Leadership coaching analysis |
| **Gmail API** | Google API Client | Fetch meeting summaries |
| **Calendar API** | Google API Client | Create todos and check availability |
| **Zoom API** | REST API (optional) | Fetch full transcripts |
| **CLI** | Click | Command-line interface |
| **Output** | Rich | Beautiful terminal output |
| **Auth** | OAuth 2.0 | Secure Google authentication |
| **Scheduling** | cron/launchd/Task Scheduler | Automated daily runs |

## 🔐 Security & Privacy

- ✅ **Local execution:** Runs entirely on your machine
- ✅ **Secure credentials:** OAuth tokens stored locally
- ✅ **No data sharing:** Your meetings never leave your control
- ✅ **Read-only Gmail:** Can't modify or delete emails (unless you enable mark-as-read)
- ✅ **Gitignored credentials:** API keys never committed to version control
- ✅ **Claude API:** Only meeting content sent for analysis (via encrypted HTTPS)

## 📈 Roadmap / Future Enhancements

Possible additions you could make:

- [ ] **Multi-account support:** Process multiple Gmail accounts
- [ ] **Slack integration:** Post coaching summaries to Slack
- [ ] **Weekly digest:** Aggregate insights from the week
- [ ] **Trend analysis:** Track leadership patterns over time
- [ ] **Team coaching:** Analyze team-wide meeting patterns
- [ ] **Custom prompts:** User-defined coaching focus areas
- [ ] **Export formats:** PDF, HTML, Notion integration
- [ ] **Meeting prep:** AI suggestions before meetings based on past patterns

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No module named 'google'"** | Activate venv: `source venv/bin/activate` |
| **"Credentials not found"** | Follow `GOOGLE_API_SETUP.md` to create credentials |
| **"Token expired"** | Delete `credentials/token.pickle` and re-run setup |
| **"No emails found"** | Check filters in `config/settings.json` and date range |
| **"Claude API error"** | Verify `ANTHROPIC_API_KEY` in `.env` is correct |
| **"Permission denied"** | Make scripts executable: `chmod +x setup.sh` |

Enable verbose logging for detailed debugging:
```bash
python -m src.main --verbose
```

## 📚 Documentation Files

- **README.md** - Comprehensive project documentation
- **QUICKSTART.md** - Fast 5-minute setup guide
- **GOOGLE_API_SETUP.md** - Detailed Google API configuration
- **SAMPLE_REPORT.md** - Example of coaching report output
- **PROJECT_OVERVIEW.md** - This file (high-level overview)

## 💡 Tips for Best Results

1. **Customize Leadership Principles:** Spend time making `leadership_principles.md` specific to your leadership style
2. **Review First Reports:** Check the first few coaching reports and adjust principles if needed
3. **Set Accurate Work Hours:** Configure realistic work hours in settings for better scheduling
4. **Use Preferred Focus Times:** Tell the app when you're most productive for complex tasks
5. **Process Regularly:** Daily processing gives better continuity than weekly batches
6. **Act on Insights:** The coaching is only valuable if you apply it

## 🎓 Learning Resources

Want to understand the components better?

- **Gmail API:** [developers.google.com/gmail/api](https://developers.google.com/gmail/api)
- **Calendar API:** [developers.google.com/calendar](https://developers.google.com/calendar)
- **Anthropic Claude:** [docs.anthropic.com](https://docs.anthropic.com)
- **Zoom API:** [marketplace.zoom.us/docs/api-reference](https://marketplace.zoom.us/docs/api-reference)

---

## 🎉 You're All Set!

You now have a complete AI-powered leadership coaching system that:
- ✅ Automatically processes your meeting summaries
- ✅ Provides personalized coaching based on your principles
- ✅ Intelligently schedules your action items
- ✅ Helps you grow as a leader

**Next step:** Follow `QUICKSTART.md` to get started!

Questions? Check the troubleshooting sections in each documentation file.

Happy coaching! 🚀
