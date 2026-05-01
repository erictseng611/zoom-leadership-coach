#!/bin/bash

# Run Zoom Leadership Coach with AWS Bedrock
# This script authenticates via claude-up and runs the app

set -e

echo "🔐 Authenticating with AWS Bedrock..."
echo ""

# Run claude-up function
# Note: This requires the function to be loaded in your shell
if ! type claude-up &> /dev/null; then
    echo "❌ claude-up function not found"
    echo ""
    echo "Make sure you have the function defined in ~/.oh-my-zsh/custom/example.zsh"
    echo "Try running: source ~/.oh-my-zsh/custom/example.zsh"
    exit 1
fi

# Prompt for MFA
echo "This will run 'claude-up' to authenticate with AWS..."
echo ""

# Since claude-up is a shell function, we need to source it
# For now, instruct the user to run it manually
echo "⚠️  Please run 'claude-up' in your terminal first, then run this script again."
echo ""
echo "Or run the app directly after claude-up:"
echo "  1. claude-up"
echo "  2. cd ~/src/zoom-leadership-coach"
echo "  3. ./run.sh"
echo ""

# Check if AWS credentials are already set
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "✅ AWS credentials detected!"
    echo "🚀 Running Zoom Leadership Coach..."
    echo ""

    cd "$(dirname "$0")"
    source venv/bin/activate
    python3 -m src.main "$@"
else
    echo "❌ No AWS credentials found"
    echo ""
    echo "Please run 'claude-up' first:"
    echo "  1. Run: claude-up"
    echo "  2. Enter your MFA code"
    echo "  3. Then run this script again"
    exit 1
fi
