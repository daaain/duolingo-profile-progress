#!/bin/bash

# Setup script for Duolingo Family League
# Run this script to quickly set up the automation

set -e

echo "🦉 Setting up Duolingo Family League..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USERNAME=$(whoami)

echo "📁 Project directory: $SCRIPT_DIR"
echo "👤 Username: $USERNAME"

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x "$SCRIPT_DIR/duolingo_wrapper.sh"
chmod +x "$SCRIPT_DIR/duolingo_cron.sh"

# Update the LaunchAgent plist with correct username
echo "📝 Updating LaunchAgent configuration..."
cp "$SCRIPT_DIR/com.duolingo.familyleague.plist.example" "$SCRIPT_DIR/com.duolingo.familyleague.plist"
sed -i '' "s/YOUR_USERNAME/$USERNAME/g" "$SCRIPT_DIR/com.duolingo.familyleague.plist"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync

# Create .env file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "⚙️  Creating environment configuration file..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "📝 Please edit .env with your configuration"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env with your family's Duolingo usernames (DUOLINGO_USERNAMES)"
echo "2. Set up Gmail App Password and update email settings"
echo "3. Test the system:"
echo "   python3 duolingo_family_league.py"
echo "4. Set up automation (choose one):"
echo ""
echo "   🤖 Option 1 - LaunchAgent (Recommended):"
echo "   cp com.duolingo.familyleague.plist ~/Library/LaunchAgents/"
echo "   launchctl load ~/Library/LaunchAgents/com.duolingo.familyleague.plist"
echo ""
echo "   ⏰ Option 2 - Cron:"
echo "   crontab -e"
echo "   # Add: 0 9-18 * * 1 $SCRIPT_DIR/duolingo_cron.sh"
echo ""
echo "📖 See README.md for detailed instructions"
