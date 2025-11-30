#!/bin/bash

# ReqTrace Setup Script for macOS/Linux/Git Bash
# This script automates the backend setup process

set -e  # Exit on error

echo "================================"
echo "ReqTrace Backend Setup"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed"
    echo "Please install Python 3.11+ from https://python.org"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

echo "✓ Found Python: $($PYTHON_CMD --version)"
echo ""

# Navigate to backend directory
echo "📁 Navigating to backend directory..."
cd backend || { echo "❌ Error: backend directory not found"; exit 1; }

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment already exists, skipping creation"
else
    $PYTHON_CMD -m venv .venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Git Bash on Windows
    source .venv/Scripts/activate
else
    # macOS/Linux
    source .venv/bin/activate
fi
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install requirements
echo "📦 Installing Python dependencies..."
echo "⏳ This may take 5-10 minutes..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Install spacy if not in requirements
echo "🔍 Checking for spacy installation..."
if ! pip show spacy &> /dev/null; then
    echo "📦 Installing spacy..."
    pip install spacy coreferee spacy-transformers
    echo "✓ Spacy installed"
else
    echo "✓ Spacy already installed"
fi
echo ""

# Download spacy models
echo "📥 Downloading Spacy NLP models..."
echo "⏳ This may take a few minutes..."
$PYTHON_CMD -m spacy download en_core_web_sm
$PYTHON_CMD -m coreferee install en
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.4.1/en_core_web_lg-3.4.1-py3-none-any.whl
echo "✓ Spacy models downloaded"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# OpenAI API Key (required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Neo4j Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Google OAuth (optional, use placeholder for now)
GOOGLE_CLIENT_ID=placeholder
GOOGLE_CLIENT_SECRET=placeholder

# Application Secret Key
SECRET_KEY=mysecretkey12345
EOF
    echo "✓ .env template created"
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your actual credentials!"
else
    echo "✓ .env file exists"
fi
echo ""

echo "================================"
echo "✅ Backend Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Make sure Neo4j database is running"
echo "2. Edit backend/.env with your actual credentials"
echo "3. Start the backend server:"
echo "   cd backend/app"
echo "   uvicorn main:app --reload"
echo ""
echo "4. In a new terminal, set up the frontend:"
echo "   cd frontend"
echo "   npm install"
echo "   npm run dev"
echo ""