#!/bin/bash
# ============================
# Brain System — Single Command Launcher
# ============================
# Usage: ./run.sh
# This starts the Flask server which serves both the API and web UI.

cd "$(dirname "$0")"

echo ""
echo "🧠 =================================================="
echo "   Brain System — Starting Web UI"
echo "🧠 =================================================="
echo ""

# Check for required packages
python3.11 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip3.11 install -r brain_system/requirements.txt
fi

# Start the server
echo "🚀 Launching at http://localhost:5000"
echo ""
python3.11 -m brain_system.app
