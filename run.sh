#!/bin/bash

# Healthcare SOAP Note Taking Bot - Run Script
# This script activates the virtual environment and runs the application

echo "🏥 Starting Healthcare SOAP Note Taking Bot..."
echo "📁 Working directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'python3 -m venv venv' first."
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
if ! pip show flask > /dev/null 2>&1; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Validate configuration
echo "⚙️ Checking configuration..."
if [ ! -f "config.py" ]; then
    echo "❌ config.py not found. Please create it with your API keys."
    exit 1
fi

# Run the application
echo "🚀 Starting application on http://localhost:5002"
echo "📱 Frontend: Modular structure in frontend/ folder"
echo "🔧 Backend: Handlers and services properly separated"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

python app.py 