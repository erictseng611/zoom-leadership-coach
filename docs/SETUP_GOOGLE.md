# Google API Setup Guide

Step-by-step guide to configure Gmail and Google Calendar APIs.

## Overview

You'll need to:
1. Create a Google Cloud Project
2. Enable Gmail API and Google Calendar API
3. Create OAuth 2.0 credentials
4. Download and save the credentials file

**Time required:** ~10 minutes

---

## Step 1: Create a Google Cloud Project

### 1.1 Go to Google Cloud Console

Open your browser and navigate to:
```
https://console.cloud.google.com/
```

### 1.2 Create a New Project

1. Click the project dropdown at the top of the page (next to "Google Cloud")
2. Click **NEW PROJECT** in the top right
3. Enter project details:
   - **Project name:** "Zoom Leadership Coach" (or your preferred name)
   - **Organization:** Leave as default (usually "No organization")
4. Click **CREATE**
5. Wait a few seconds for the project to be created
6. You'll be automatically switched to your new project

**Confirm:** Check that the project name appears in the top navigation bar

---

## Step 2: Enable Required APIs

### 2.1 Navigate to APIs & Services

1. Click the ☰ hamburger menu (top left)
2. Navigate to: **APIs & Services** → **Library**

### 2.2 Enable Gmail API

1. In the API Library search bar, type: `Gmail API`
2. Click on **Gmail API** from the results
3. Click the blue **ENABLE** button
4. Wait for it to activate (usually a few seconds)

### 2.3 Enable Google Calendar API

1. Click **← SEARCH FOR APIS & SERVICES** (or use the back button)
2. In the search bar, type: `Google Calendar API`
3. Click on **Google Calendar API** from the results
4. Click the blue **ENABLE** button
5. Wait for it to activate

**Confirm:** Both APIs should now show as enabled in your project

---

## Step 3: Configure OAuth Consent Screen

Before creating credentials, you need to configure the OAuth consent screen.

### 3.1 Navigate to OAuth Consent Screen

1. Click the ☰ hamburger menu
2. Go to: **APIs & Services** → **OAuth consent screen**

### 3.2 Choose User Type

1. Select **External** (unless you have a Google Workspace organization)
2. Click **CREATE**

### 3.3 Fill Out App Information

**Page 1: OAuth consent screen**

Fill in the required fields:
- **App name:** Zoom Leadership Coach
- **User support email:** [Your email]
- **Developer contact information:** [Your email]

Optional fields can be left blank.

Click **SAVE AND CONTINUE**

**Page 2: Scopes**

Click **SAVE AND CONTINUE** (we'll set scopes automatically in the app)

**Page 3: Test users**

1. Click **+ ADD USERS**
2. Enter your Gmail address (the one you'll use with the app)
3. Click **ADD**
4. Click **SAVE AND CONTINUE**

**Page 4: Summary**

Review and click **BACK TO DASHBOARD**

**Important:** Your app will be in "Testing" mode, which is perfect for personal use. It allows up to 100 test users.

---

## Step 4: Create OAuth 2.0 Credentials

### 4.1 Navigate to Credentials

1. Click the ☰ hamburger menu
2. Go to: **APIs & Services** → **Credentials**

### 4.2 Create OAuth Client ID

1. Click **+ CREATE CREDENTIALS** at the top
2. Select **OAuth client ID**

### 4.3 Configure the OAuth Client

1. **Application type:** Select **Desktop app** from the dropdown
2. **Name:** Zoom Leadership Coach Desktop
3. Click **CREATE**

### 4.4 Download Credentials

1. A dialog will appear showing your Client ID and Client Secret
2. Click **DOWNLOAD JSON**
3. The file will download (usually named something like `client_secret_123456.json`)

**Important:** Keep this file secure! It allows access to your Gmail and Calendar.

---

## Step 5: Save Credentials to Your Project

### 5.1 Locate the Downloaded File

The file is typically in your `~/Downloads` folder.

### 5.2 Rename and Move the File

```bash
# Navigate to your project
cd ~/src/zoom-leadership-coach

# Create credentials directory if it doesn't exist
mkdir -p credentials

# Copy and rename the file
cp ~/Downloads/client_secret_*.json credentials/google_credentials.json
```

### 5.3 Verify the File

Check that the file exists and has the correct structure:

```bash
cat credentials/google_credentials.json
```

You should see JSON with fields like:
- `client_id`
- `client_secret`
- `redirect_uris`
- `auth_uri`
- `token_uri`

---

## Step 6: Test Authentication

Now that you have the credentials, test the authentication flow:

```bash
# Make sure you're in the project directory
cd ~/src/zoom-leadership-coach

# Activate virtual environment
source venv/bin/activate

# Run setup
python -m src.main --setup
```

### What Should Happen:

1. A browser window will open
2. You'll see a Google sign-in page
3. Sign in with the Google account you added as a test user
4. You'll see a warning: "Google hasn't verified this app"
   - This is normal! It's your own app.
   - Click **Continue** (or **Advanced** → **Go to Zoom Leadership Coach**)
5. Review the permissions:
   - Read your Gmail messages
   - Manage your calendars
6. Click **Allow**
7. You'll see "The authentication flow has completed"
8. The terminal will show: ✓ Gmail authentication successful
9. The terminal will show: ✓ Calendar authentication successful

### Troubleshooting

**"Access blocked: This app's request is invalid"**
- Make sure you added yourself as a test user in Step 3.3
- Try signing in with a different Google account

**"OAuth consent screen is not configured"**
- Go back to Step 3 and complete the OAuth consent screen setup

**"API has not been used in project before"**
- Go back to Step 2 and ensure both APIs are enabled
- Wait a few minutes and try again

**"Credentials not found"**
- Check that the file is at: `credentials/google_credentials.json`
- Verify the file is valid JSON (use `cat` to inspect it)

---

## Step 7: Verify Permissions

After successful authentication, verify that the app can access your data:

### Test Gmail Access

```bash
python -m src.main --verbose
```

You should see:
```
Found X email(s)
```

If you see "0 email(s)" and you know you have Zoom meeting summaries, check:
1. The emails are from `no-reply@zoom.us`
2. The subject line contains "Meeting assets"
3. The emails are within the last 7 days (default setting)

### Test Calendar Access

The app will automatically check calendar availability during processing.

If you see errors about calendar access:
1. Go to your [Google Account permissions](https://myaccount.google.com/permissions)
2. Find "Zoom Leadership Coach"
3. Verify it has Calendar access
4. If not, revoke and re-run the setup

---

## Security Best Practices

### Protect Your Credentials

```bash
# Verify .gitignore includes credentials
cat .gitignore | grep credentials
```

Should show:
```
credentials/*.json
credentials/*.pickle
```

### Revoke Access (If Needed)

If you need to revoke the app's access:

1. Go to: https://myaccount.google.com/permissions
2. Find "Zoom Leadership Coach"
3. Click **Remove Access**
4. Delete `credentials/token.pickle`
5. Re-run setup to re-authenticate

### Rotating Credentials

If you think credentials were compromised:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Find your OAuth 2.0 Client ID
5. Click the trash icon to delete it
6. Create a new one (repeat Step 4)
7. Download new credentials and replace the file
8. Delete `credentials/token.pickle`
9. Re-run setup

---

## Frequently Asked Questions

### Q: Do I need a paid Google Cloud account?

**A:** No! The Gmail and Calendar APIs are free for personal use with reasonable quotas.

### Q: What are the API usage limits?

**A:** 
- Gmail API: 1 billion quota units/day (reading emails uses 5 units each)
- Calendar API: 1 million queries/day

For personal use, you'll never hit these limits.

### Q: Will this app modify my emails?

**A:** The app only has read access to Gmail. It can optionally mark emails as read, but this is disabled by default in `config/settings.json`.

### Q: Can I use this with multiple Google accounts?

**A:** Yes, but you'll need to:
1. Run setup for each account separately
2. Create separate token files for each account
3. Modify the code to specify which account to use

For simplicity, start with one account.

### Q: The OAuth consent screen shows a warning. Is this safe?

**A:** Yes! Google shows warnings for unverified apps. Since this is your own app running locally, it's safe to proceed. To remove the warning, you'd need to go through Google's verification process, which isn't necessary for personal use.

### Q: Can I run this on a server?

**A:** The current setup uses OAuth 2.0 for Desktop Apps, which requires a browser. For server deployment, you'd need to use a Service Account instead. This is more advanced and not covered in this guide.

---

## Next Steps

Once you've completed this setup:

1. ✅ Google APIs are configured
2. ✅ Authentication is working
3. ✅ You're ready to process meetings

Continue with the [Quick Start Guide](QUICKSTART.md) to:
- Customize your leadership principles
- Process your first meeting summary
- Schedule automated daily runs

---

**Need Help?**

If you get stuck:
1. Check the **Troubleshooting** sections above
2. Enable verbose logging: `python -m src.main --verbose`
3. Review the [README.md](README.md) for more details
4. Check that all prerequisites are installed correctly
