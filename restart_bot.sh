#!/bin/bash

echo "🔄 Restarting K2SO Bot with Gemini Integration..."

# Stop any existing bot processes
echo "Stopping existing bot processes..."
pkill -f "python.*main.py" || echo "No existing bot found"

# Wait a moment
sleep 2

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY is not set!"
    echo "Please set it with: export GEMINI_API_KEY='your_api_key_here'"
    echo "Then run this script again."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Verify Gemini integration
echo "Testing Gemini integration..."
python3 -c "
import gemini_integration
import os
print('API Key:', 'Available' if os.environ.get('GEMINI_API_KEY') else 'Missing')
print('Gemini:', 'Ready' if gemini_integration.is_gemini_available() else 'Not Ready')
"

# Start the bot
echo "Starting bot..."
python main.py &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo "Bot is now running with Gemini integration!"
echo ""
echo "📱 Try sending a direct message to your bot in Slack!"
echo "🔧 For kubectl commands, use '/kubectl' or 'kubectl' in DMs"
echo ""
echo "To stop the bot: kill $BOT_PID"