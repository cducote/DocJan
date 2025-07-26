#!/bin/bash

# DocJanitor Launch Script
# Usage: ./run.sh [dev|prod]

set -e  # Exit on any error

# Default to dev mode if no argument provided
MODE=${1:-dev}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[DocJanitor]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[DocJanitor]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[DocJanitor]${NC} $1"
}

print_error() {
    echo -e "${RED}[DocJanitor]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_error "Virtual environment not found! Please run: python -m venv .venv"
    exit 1
fi

# Detect operating system and activate virtual environment accordingly
print_status "Activating virtual environment..."

# Check if we're on Windows (Git Bash, WSL, etc.)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]] || command -v winpty >/dev/null 2>&1; then
    # Windows - use Scripts/activate
    if [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
        print_status "Windows virtual environment activated"
    else
        print_error "Windows virtual environment activation script not found at .venv/Scripts/activate"
        exit 1
    fi
else
    # Unix (macOS/Linux) - use bin/activate
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        print_status "Unix virtual environment activated"
    else
        print_error "Unix virtual environment activation script not found at .venv/bin/activate"
        exit 1
    fi
fi

# Check if requirements are installed
if ! python -c "import streamlit" 2>/dev/null; then
    print_warning "Dependencies not found. Installing requirements..."
    pip install -r requirements.txt
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    print_status "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set environment variables based on mode
case $MODE in
    "dev"|"development"|"--dev"|"--development")
        print_success "🚀 Starting DocJanitor in DEVELOPMENT mode"
        export DEV_MODE=true
        export SKIP_LOGIN=true
        export STREAMLIT_SERVER_PORT=8501
        export STREAMLIT_SERVER_HEADLESS=true
        export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
        
        print_status "Development features enabled:"
        echo "  ✓ Login bypass enabled"
        echo "  ✓ Auto-load last profile"
        echo "  ✓ Debug mode enabled"
        echo "  ✓ Running on port 8501"
        echo ""
        ;;
        
    "prod"|"production"|"--prod"|"--production")
        print_success "🔒 Starting DocJanitor in PRODUCTION mode"
        export DEV_MODE=false
        export SKIP_LOGIN=false
        export STREAMLIT_SERVER_PORT=8502
        export STREAMLIT_SERVER_HEADLESS=true
        export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
        
        print_status "Production features enabled:"
        echo "  ✓ Login required"
        echo "  ✓ Profile selection required"
        echo "  ✓ Security features enabled"
        echo "  ✓ Running on port 8502"
        echo ""
        ;;
        
    *)
        print_error "Invalid mode: $MODE"
        echo "Usage: $0 [dev|prod]"
        echo ""
        echo "Modes:"
        echo "  dev, development, --dev, --development  : Development mode"
        echo "  prod, production, --prod, --production  : Production mode"
        exit 1
        ;;
esac

# Kill any existing Streamlit processes on our ports
print_status "Checking for existing Streamlit processes..."
if lsof -ti:$STREAMLIT_SERVER_PORT >/dev/null 2>&1; then
    print_warning "Killing existing process on port $STREAMLIT_SERVER_PORT"
    kill -9 $(lsof -ti:$STREAMLIT_SERVER_PORT) 2>/dev/null || true
fi

# Start Streamlit
print_status "Starting Streamlit application..."
print_success "Application will be available at: http://localhost:$STREAMLIT_SERVER_PORT"
echo ""

# Trap Ctrl+C to clean exit
trap 'print_warning "Shutting down DocJanitor..."; exit 0' INT

# Start the application
streamlit run main.py --server.port=$STREAMLIT_SERVER_PORT --server.headless=true
