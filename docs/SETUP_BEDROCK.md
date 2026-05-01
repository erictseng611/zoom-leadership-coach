# AWS Bedrock Setup Guide

Use AWS Bedrock instead of direct Anthropic API access.

## Why Use Bedrock?

- ✅ Access Claude through your AWS account
- ✅ Use existing AWS credentials and SSO
- ✅ Leverage AWS billing and cost tracking
- ✅ Take advantage of enterprise AWS agreements

## Prerequisites

- AWS account with Bedrock access
- `claude-up` function configured in your shell (already done!)
- AWS CLI installed and configured

## Setup Instructions

### Step 1: Verify Your `claude-up` Script

You already have this configured! Verify it's working:

```bash
# Check that claude-up function exists
type claude-up
```

Should show your function definition.

### Step 2: Configure the App for Bedrock

Edit your `.env` file:

```bash
cd ~/src/zoom-leadership-coach
nano .env
```

Set `USE_BEDROCK=true`:

```env
# Claude API Access Method
USE_BEDROCK=true
AWS_REGION=us-west-2

# You can leave ANTHROPIC_API_KEY blank when using Bedrock
# ANTHROPIC_API_KEY=
```

### Step 3: Authenticate with AWS

Before running the app, authenticate using your existing `claude-up` function:

```bash
# This prompts for MFA and sets up AWS credentials
claude-up
```

You'll be prompted for your MFA code. After successful authentication, you'll see:
```
AWS credentials exported successfully!
Account ID: 410444354559
Expires: [timestamp]
```

The `claude-up` function exports these environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `ANTHROPIC_MODEL` (set to your Bedrock model ID)

### Step 4: Run the App

In the same terminal session where you ran `claude-up`:

```bash
cd ~/src/zoom-leadership-coach
source venv/bin/activate

# Test the setup
python3 -m src.main --setup

# Process meetings
python3 -m src.main
```

## Usage Workflow

Every time you want to run the app with Bedrock:

1. **Authenticate** (credentials expire after 12 hours):
   ```bash
   claude-up
   ```

2. **Run the app** (in the same terminal):
   ```bash
   cd ~/src/zoom-leadership-coach
   ./run.sh
   ```

That's it! The app will automatically use Bedrock because `USE_BEDROCK=true`.

## Model Configuration

Your `claude-up` script already sets the model:
```bash
export ANTHROPIC_MODEL='us.anthropic.claude-sonnet-4-5-20250929-v1:0'
```

The app will use this model automatically. To change it:

1. Edit your `~/.oh-my-zsh/custom/example.zsh`
2. Update the `ANTHROPIC_MODEL` variable in `claude-up`
3. Re-run `claude-up`

Available models:
- `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (default)
- `us.anthropic.claude-haiku-4-5-20251001-v1:0` (faster, cheaper)
- Check AWS Bedrock console for latest models

## Helper Script for Bedrock

Create a convenience script that combines authentication and execution:

```bash
cat > ~/src/zoom-leadership-coach/run-bedrock.sh << 'EOF'
#!/bin/bash

# Run Zoom Leadership Coach with AWS Bedrock

echo "🔐 Authenticating with AWS Bedrock..."
claude-up

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Authentication successful!"
    echo "🚀 Running Zoom Leadership Coach..."
    echo ""
    
    cd ~/src/zoom-leadership-coach
    source venv/bin/activate
    python3 -m src.main "$@"
else
    echo "❌ Authentication failed"
    exit 1
fi
EOF

chmod +x ~/src/zoom-leadership-coach/run-bedrock.sh
```

Usage:
```bash
# Run with authentication
~/src/zoom-leadership-coach/run-bedrock.sh

# Or with options
~/src/zoom-leadership-coach/run-bedrock.sh --transcript meeting.txt
```

## Switching Between Anthropic and Bedrock

You can easily switch between direct Anthropic API and Bedrock:

### Use Bedrock (via AWS):
```bash
# In .env:
USE_BEDROCK=true

# Then authenticate and run:
claude-up
./run.sh
```

### Use Direct Anthropic API:
```bash
# In .env:
USE_BEDROCK=false
ANTHROPIC_API_KEY=sk-ant-api03-your-key

# Just run (no claude-up needed):
./run.sh
```

## Troubleshooting

### "Missing AWS credentials"

You need to run `claude-up` first:
```bash
claude-up
# Enter MFA code when prompted
# Then run the app in the same terminal
```

### "Failed to connect to AWS Bedrock"

Check your AWS credentials are set:
```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $AWS_SESSION_TOKEN
```

All three should show values. If not, run `claude-up` again.

### "Credentials expired"

AWS credentials from `claude-up` last 12 hours. Just re-run:
```bash
claude-up
```

### "Access denied to Bedrock"

Your AWS account needs Bedrock access. Check:
1. Go to AWS Bedrock console
2. Verify you have access to Claude models
3. Request access if needed (usually instant for Sonnet)

### "Model not found"

Check the model ID:
```bash
echo $ANTHROPIC_MODEL
```

Should show: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`

If different, the model may not be available in your region.

## Region Configuration

Your `claude-up` doesn't specify a region, so it uses your AWS CLI default.

To specify a region for Bedrock:

```bash
# In .env:
AWS_REGION=us-west-2
```

Bedrock-supported regions:
- `us-west-2` (Oregon)
- `us-east-1` (N. Virginia)
- Check AWS docs for latest

## Cost Comparison

### Anthropic Direct API:
- Sonnet 4.5: ~$3 per million input tokens, ~$15 per million output tokens

### AWS Bedrock:
- Same pricing as direct API
- But billed through your AWS account
- Can use AWS cost allocation tags
- May have enterprise discounts

## Scheduled Runs with Bedrock

For automated daily runs with Bedrock, you need persistent credentials.

### Option 1: Use Anthropic API for Scheduled Runs

The easiest approach:
```bash
# In .env for cron/scheduled runs:
USE_BEDROCK=false
ANTHROPIC_API_KEY=sk-ant-api03-your-key
```

### Option 2: Service Account with IAM Role

For production scheduled runs with Bedrock:
1. Create an IAM role with Bedrock permissions
2. Attach to EC2 instance or ECS task
3. No `claude-up` needed - uses instance role

This is more complex and typically for production deployments.

## Verification

Test that Bedrock is working:

```bash
# Authenticate
claude-up

# Test setup
cd ~/src/zoom-leadership-coach
source venv/bin/activate
python3 -m src.main --setup
```

You should see:
```
✓ Gmail authentication successful
✓ Calendar authentication successful
✓ AWS Bedrock configured
```

If you see "AWS Bedrock configured", you're all set!

## Security Notes

- AWS credentials from `claude-up` are temporary (12 hours)
- Session tokens are required and automatically included
- Never commit `.env` file with credentials
- The app only needs read access to Bedrock (no write/admin)

## Next Steps

1. ✅ Set `USE_BEDROCK=true` in `.env`
2. ✅ Run `claude-up` to authenticate
3. ✅ Run `python3 -m src.main --setup` to verify
4. ✅ Process your first meeting: `python3 -m src.main`

That's it! You're now using Claude through AWS Bedrock instead of the direct API.
