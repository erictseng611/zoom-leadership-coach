#!/bin/bash

# Zoom Leadership Coach - Setup Script

set -e

echo "╔═══════════════════════════════════════════════════╗"
echo "║   Zoom Leadership Coach - Installation Setup    ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✓ Installation complete!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (required)"
    echo "   - ZOOM_* credentials (optional)"
    echo ""
fi

# Check for Google credentials
if [ ! -f credentials/google_credentials.json ]; then
    echo "⚠️  Google OAuth credentials not found!"
    echo ""
    echo "Next steps:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a new project or select existing"
    echo "3. Enable Gmail API and Google Calendar API"
    echo "4. Create OAuth 2.0 credentials (Desktop app)"
    echo "5. Download JSON and save as: credentials/google_credentials.json"
    echo ""
fi

echo "═══════════════════════════════════════════════════"
echo ""
echo "🎉 Setup complete! Next steps:"
echo ""
echo "1. Edit your .env file with API keys:"
echo "   nano .env"
echo ""
echo "2. Add your Google OAuth credentials:"
echo "   Save to: credentials/google_credentials.json"
echo ""
echo "3. Customize your leadership principles:"
echo "   nano config/leadership_principles.md"
echo ""
echo "4. Run initial authentication setup:"
echo "   python3 -m src.main --setup"
echo ""
echo "5. Process your first batch of summaries:"
echo "   python3 -m src.main"
echo ""
echo "6. (Optional) Schedule daily runs:"
echo "   python3 -m src.main --schedule --run-time 20:00"
echo ""
echo "═══════════════════════════════════════════════════"
