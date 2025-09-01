#!/bin/bash

# Stealth Legal AI - Setup Script
echo "🚀 Setting up Stealth Legal AI..."

# Check if Python 3.10+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

node_version=$(node --version)
echo "✅ Node.js version: $node_version"

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Setup frontend
echo "📦 Setting up frontend..."
cd frontend
npm install
cd ..

# Create database
echo "🗄️ Creating database..."
python3 -c "
from app.database import create_tables
create_tables()
print('Database created successfully!')
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo ""
echo "1. Start the backend:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "2. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3. Open your browser to:"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "4. Run tests:"
echo "   pytest tests/"
echo "   pytest tests/test_performance.py"
echo ""
echo "Happy coding! 🚀"
