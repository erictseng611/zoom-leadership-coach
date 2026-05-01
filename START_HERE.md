# 🚀 START HERE - Zoom Leadership Coach

## ✅ Setup Complete!

The application is installed and ready to configure. Follow these steps:

---

## Step 1: Choose Your Claude Access Method (2 minutes)

You have **TWO options** for accessing Claude AI:

### Option A: AWS Bedrock (RECOMMENDED FOR YOU ✅)

You already have `claude-up` configured! This is the easiest option.

```bash
cd ~/src/zoom-leadership-coach
nano .env
```

Set:
```
USE_BEDROCK=true
AWS_REGION=us-west-2
```

That's it! Skip to Step 2.

**Detailed guide:** See `BEDROCK_SETUP.md` for complete instructions.

### Option B: Direct Anthropic API

If you prefer direct API access:

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-api03-`)

```bash
cd ~/src/zoom-leadership-coach
nano .env
```

Set:
```
USE_BEDROCK=false
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
```

**Note:** You can switch between these options anytime by editing `.env`.

---

## Step 2: Setup Google APIs (10 minutes)

You need to create OAuth credentials for Gmail and Google Calendar access.

### Detailed Instructions

Open and follow this guide:
```bash
open GOOGLE_API_SETUP.md
```

Or read it in your editor:
```bash
cat GOOGLE_API_SETUP.md
```

### Quick Summary

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: "Zoom Leadership Coach"
3. Enable **Gmail API** and **Google Calendar API**
4. Create **OAuth 2.0 Desktop App** credentials
5. Download the JSON file
6. Save it as: `credentials/google_credentials.json`

```bash
# Example: Copy from Downloads
cp ~/Downloads/client_secret_*.json ~/src/zoom-leadership-coach/credentials/google_credentials.json
```

---

## Step 3: Customize Your Leadership Principles (5 minutes)

This is the most important step! The AI coach uses these principles to analyze your meetings.

```bash
cd ~/src/zoom-leadership-coach
nano config/leadership_principles.md
```

Edit the file to reflect:
- Your core leadership values
- Communication style goals
- Areas you're working on
- Red flags to watch for

The more specific you are, the better the coaching will be!

---

## Step 4: Run Initial Setup & Authentication (2 minutes)

Now let's authenticate with Google and Claude:

### If Using Bedrock (Option A):

```bash
# First, authenticate with AWS
claude-up
# (Enter MFA code when prompted)

# Then run setup
cd ~/src/zoom-leadership-coach
source venv/bin/activate
python3 -m src.main --setup
```

### If Using Direct API (Option B):

```bash
cd ~/src/zoom-leadership-coach
source venv/bin/activate

# Run the setup
python3 -m src.main --setup
```

### What Will Happen:

1. **Browser Opens**: A Google sign-in page will appear
2. **Warning Screen**: You'll see "Google hasn't verified this app"
   - This is normal! It's your own app
   - Click **Advanced** → **Go to Zoom Leadership Coach (unsafe)**
3. **Grant Permissions**: Allow access to Gmail and Calendar
4. **Success**: You'll see ✓ marks for each service

The terminal will show:
```
✓ Gmail authentication successful
✓ Calendar authentication successful
✓ Anthropic API configured
✓ Setup complete!
```

---

## Step 5: Test with a Sample Meeting (1 minute)

Let's test the app with a sample transcript before processing real emails:

```bash
# Still in the virtual environment
cd ~/src/zoom-leadership-coach

# Create a test meeting
cat > test_meeting.txt << 'EOF'
Team Sync - Product Planning

Participants: Alice (Product), Bob (Engineering), Carol (Design)

Summary:
We discussed the Q2 roadmap and decided to prioritize the payment integration
feature over the reporting dashboard. Alice will lead the product requirements,
Bob will handle the technical architecture, and Carol will create the user flows.

Action Items:
- Alice: Draft product requirements document (Due: Friday)
- Bob: Create technical design proposal (Due: Next Monday) 
- Carol: Design user flows for payment screens (Due: Next week)
- Alice: Schedule follow-up with stakeholders (Due: ASAP)

Decisions:
- Prioritize payment integration (Q2 focus)
- Defer reporting dashboard to Q3
- Weekly check-ins every Monday at 2pm

Questions:
- Do we have API access to the payment provider?
- What's the timeline for security review?
EOF

# Process it
python3 -m src.main --transcript test_meeting.txt
```

### What You'll Get:

1. **Coaching Report** saved to `data/coaching_reports/`
2. **Calendar Todos** created in Google Calendar (if time slots available)
3. **Terminal Output** showing the analysis

View your report:
```bash
# List all reports
ls -la data/coaching_reports/

# Open the most recent one
open data/coaching_reports/*.md
# Or on Linux: xdg-open data/coaching_reports/*.md
```

---

## Step 6: Process Real Zoom Summaries (1 minute)

Now process actual Zoom meeting summaries from your Gmail:

```bash
# Make sure you're still in the virtual environment
source venv/bin/activate

# Process emails
python3 -m src.main
```

This will:
1. ✅ Fetch Zoom "Meeting assets" emails from Gmail
2. ✅ Parse meeting content
3. ✅ Analyze with AI coach
4. ✅ Create calendar todos
5. ✅ Generate coaching reports

If you see "No new Zoom summaries found":
- Check if you have emails from `no-reply@zoom.us` with subject "Meeting assets"
- Adjust `days_to_look_back` in `config/settings.json` if needed

---

## Step 7: (Optional) Schedule Daily Runs

Set up automatic end-of-day processing:

```bash
python3 -m src.main --schedule --run-time 20:00
```

This will run at 8 PM every day. To change the time:

```bash
# Run at 6 PM instead
python3 -m src.main --schedule --run-time 18:00
```

To disable:
```bash
python3 -m src.main --unschedule
```

---

## 🎯 Using the Helper Script

For convenience, I've created a helper script that automatically activates the virtual environment:

```bash
# Instead of: source venv/bin/activate && python3 -m src.main
# Just use:
./run.sh

# With options:
./run.sh --verbose
./run.sh --transcript my_meeting.txt
./run.sh --schedule --run-time 20:00
```

---

## 📊 What You'll Get

After each run:

### 1. Coaching Reports (`data/coaching_reports/`)

Markdown files with:
- Meeting effectiveness assessment
- Prioritized action items with time estimates
- Recommended schedule based on your calendar
- Leadership insights tied to your principles
- Communication pattern analysis
- Areas for growth with specific examples
- Wins and positive reinforcement

**Example:** See `SAMPLE_REPORT.md` for a full example

### 2. Smart Calendar Todos

Created in Google Calendar:
- 🔴 High priority tasks
- 🟡 Medium priority tasks
- 🟢 Low priority tasks
- Scheduled in your available time slots
- Buffer time between tasks

### 3. Processing Logs (`data/processed_emails.json`)

Tracks which emails have been processed (prevents duplicates)

---

## ⚙️ Configuration

### Work Hours & Focus Times

Edit `config/settings.json`:

```json
{
  "scheduling": {
    "work_hours_start": "09:00",
    "work_hours_end": "17:00",
    "preferred_focus_times": ["09:00-11:00", "14:00-16:00"],
    "lunch_break": "12:00-13:00"
  }
}
```

### Email Filters

```json
{
  "gmail": {
    "sender_filter": "no-reply@zoom.us",
    "subject_filter": "Meeting assets",
    "days_to_look_back": 7
  }
}
```

---

## 🐛 Troubleshooting

### "No module named 'google'"

You need to activate the virtual environment first:
```bash
cd ~/src/zoom-leadership-coach
source venv/bin/activate
```

### "Google credentials not found"

Make sure the file exists:
```bash
ls -la ~/src/zoom-leadership-coach/credentials/google_credentials.json
```

If not, follow Step 2 again.

### "Token has been expired or revoked"

Delete the token and re-authenticate:
```bash
rm ~/src/zoom-leadership-coach/credentials/token.pickle
source venv/bin/activate
python3 -m src.main --setup
```

### "No new Zoom summaries found"

Check:
1. Do you have emails from `no-reply@zoom.us`?
2. Are they within the last 7 days?
3. Do they have "Meeting assets" in the subject?

Adjust the lookback period if needed:
```bash
nano config/settings.json
# Change "days_to_look_back": 14
```

### "ANTHROPIC_API_KEY not found"

Make sure your `.env` file has the key:
```bash
cat ~/src/zoom-leadership-coach/.env | grep ANTHROPIC
```

Should show:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## 📚 Additional Resources

- **README.md** - Complete technical documentation
- **QUICKSTART.md** - Alternative quick start guide
- **GOOGLE_API_SETUP.md** - Detailed Google API setup
- **SAMPLE_REPORT.md** - Example coaching report
- **PROJECT_OVERVIEW.md** - Architecture and design

---

## 🎉 You're All Set!

Your Zoom Leadership Coach is ready to use!

### Daily Workflow:

1. **Morning**: Review yesterday's coaching report
2. **Throughout the day**: Attend meetings as usual
3. **End of day**: App automatically processes (if scheduled) OR run manually:
   ```bash
   ./run.sh
   ```
4. **Review**: Check coaching insights and scheduled todos

### Quick Commands Reference:

```bash
# Process emails now
./run.sh

# Process a specific transcript
./run.sh --transcript meeting.txt

# Setup daily run at 8 PM
./run.sh --schedule --run-time 20:00

# View verbose logs
./run.sh --verbose

# Stop scheduled runs
./run.sh --unschedule
```

---

## 💡 Tips for Best Results

1. **Be Specific in Leadership Principles**: The more detailed your principles, the better the coaching
2. **Review Reports Weekly**: Look for patterns in your leadership style
3. **Act on Insights**: The coaching is only valuable if you apply it
4. **Adjust Settings**: Tweak work hours and focus times to match your actual schedule
5. **Use the Test Transcript**: Before processing real emails, test with sample data

---

## 🆘 Need Help?

- **Setup issues**: Check `GOOGLE_API_SETUP.md` troubleshooting
- **Technical details**: Read `PROJECT_OVERVIEW.md`
- **Usage questions**: See `QUICKSTART.md`
- **Enable debugging**: Run with `--verbose` flag

---

Happy coaching! 🎯

Questions or feedback? Adjust `config/leadership_principles.md` to tune the coaching to your needs.
