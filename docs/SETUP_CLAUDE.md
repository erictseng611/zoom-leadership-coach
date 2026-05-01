# Claude Access Options

The Zoom Leadership Coach supports **two ways** to access Claude AI for leadership coaching.

## Overview

| Feature | AWS Bedrock | Direct Anthropic API |
|---------|-------------|---------------------|
| **Authentication** | Uses your `claude-up` script | Requires API key |
| **Setup Complexity** | Easier (you already have it!) | Simple |
| **Credentials Validity** | 12 hours (refresh with `claude-up`) | Permanent |
| **Billing** | Through your AWS account | Direct from Anthropic |
| **Model** | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | `claude-sonnet-4-20250514` |
| **Cost** | Same pricing, AWS billing | Same pricing, Anthropic billing |
| **Scheduled Runs** | Needs permanent credentials | Easy with API key |
| **Best For** | Interactive use, AWS integration | Automation, simplicity |

---

## Option 1: AWS Bedrock (Recommended for You)

### Why Choose This?

✅ You already have `claude-up` configured  
✅ Leverages your existing AWS setup  
✅ No need for additional API keys  
✅ Uses your AWS cost tracking  

### Setup

**Edit `.env`:**
```bash
USE_BEDROCK=true
AWS_REGION=us-west-2
```

**Usage:**
```bash
# Authenticate (good for 12 hours)
claude-up

# Run the app
cd ~/src/zoom-leadership-coach
./run.sh
```

### Detailed Guide

See `BEDROCK_SETUP.md` for complete instructions.

---

## Option 2: Direct Anthropic API

### Why Choose This?

✅ Simpler for scheduled/automated runs  
✅ Credentials don't expire  
✅ No AWS dependency  
✅ Direct relationship with Anthropic  

### Setup

1. **Get API key** from https://console.anthropic.com/

2. **Edit `.env`:**
```bash
USE_BEDROCK=false
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

**Usage:**
```bash
cd ~/src/zoom-leadership-coach
./run.sh
```

No authentication step needed - API key is permanent.

---

## Switching Between Options

You can easily switch by editing `.env`:

### Switch to Bedrock:
```bash
nano .env
# Set: USE_BEDROCK=true
```

Then authenticate and run:
```bash
claude-up
./run.sh
```

### Switch to Direct API:
```bash
nano .env
# Set: USE_BEDROCK=false
# Set: ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

Then just run (no `claude-up` needed):
```bash
./run.sh
```

---

## Recommendation for Different Use Cases

### For Interactive Use (Running manually when needed)
→ **Use Bedrock** with `claude-up`

Advantages:
- No need to manage API keys
- Leverages your existing AWS setup
- Same credentials for all your AWS/Claude tools

### For Scheduled/Automated Runs (Daily end-of-day processing)
→ **Use Direct Anthropic API**

Advantages:
- No need to refresh credentials
- Simpler cron/scheduled task setup
- No dependency on AWS authentication

### For Development/Testing
→ **Either works fine**

Choose whichever you're more comfortable with.

---

## Configuration Reference

### Bedrock Configuration (`.env`)

```bash
# Enable Bedrock
USE_BEDROCK=true

# AWS Region (where Bedrock is enabled)
AWS_REGION=us-west-2

# Model is set by your claude-up script
# Default: us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

### Direct API Configuration (`.env`)

```bash
# Disable Bedrock
USE_BEDROCK=false

# Set your API key
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Model is hardcoded in the app
# Uses: claude-sonnet-4-20250514
```

---

## Cost Comparison

Both options have the **same Claude API pricing**:

- **Input tokens**: ~$3 per million tokens
- **Output tokens**: ~$15 per million tokens

Typical meeting analysis (with coaching report):
- Input: ~2,000 tokens ($0.006)
- Output: ~3,000 tokens ($0.045)
- **Total per meeting: ~$0.05**

The difference is only in **how it's billed**:
- **Bedrock**: Appears in your AWS bill
- **Direct API**: Appears on Anthropic invoice

---

## Security Considerations

### Bedrock:
- ✅ Uses temporary credentials (12-hour sessions)
- ✅ Requires MFA authentication
- ✅ No long-lived secrets to manage
- ⚠️ Need to re-authenticate periodically

### Direct API:
- ✅ Simple key management
- ✅ Easy to rotate keys
- ⚠️ Long-lived secret (store securely)
- ⚠️ Keep `.env` file private

Both options are secure when used properly.

---

## Troubleshooting

### Bedrock Issues

**"Missing AWS credentials"**
→ Run `claude-up` first

**"Credentials expired"**
→ Run `claude-up` again (lasts 12 hours)

**"Access denied to Bedrock"**
→ Check your AWS account has Bedrock access

### Direct API Issues

**"API key invalid"**
→ Check your key in `.env` is correct

**"Rate limit exceeded"**
→ Wait a moment and retry (Anthropic has rate limits)

---

## Making the Choice

**Quick Decision Guide:**

1. **Are you running this manually when needed?**
   → Use Bedrock (you already have `claude-up`!)

2. **Are you setting up automated daily runs?**
   → Use Direct API (simpler for automation)

3. **Unsure?**
   → Start with Bedrock (easy to switch later)

---

## Next Steps

**Chose Bedrock?**
→ Read `BEDROCK_SETUP.md` for detailed setup

**Chose Direct API?**
→ Continue with `START_HERE.md` Option B

**Want to try both?**
→ You can switch between them anytime by editing `.env`!

The app automatically detects which method to use based on the `USE_BEDROCK` setting.
