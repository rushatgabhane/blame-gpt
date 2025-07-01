#!/bin/bash

# BlameGPT Development Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Copying from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your API keys before running the application."
    else
        print_status ".env file found."
    fi
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
}

# Install Node dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
}

# Format code
format_code() {
    print_status "Formatting Python code with Black..."
    black . --line-length=120
}

# Build frontend
build_frontend() {
    print_status "Building frontend..."
    cd frontend
    npm run build
    cd ..
}

# Run linting
run_lint() {
    print_status "Running frontend linting..."
    cd frontend
    npm run lint
    cd ..
}

# Start development servers
start_dev() {
    print_status "Starting development servers..."
    
    # Check if .env has required variables
    if ! grep -q "GITHUB_TOKEN=" .env || ! grep -q "OPENAI_API_KEY=" .env; then
        print_error "Please set GITHUB_TOKEN and OPENAI_API_KEY in your .env file"
        return 1
    fi
    
    print_status "Starting backend server..."
    print_status "Backend will be available at http://localhost:8000"
    print_status "API docs will be available at http://localhost:8000/docs"
    print_status ""
    print_status "To start frontend, run in another terminal:"
    print_status "cd frontend && npm run dev"
    print_status ""
    
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Show help
show_help() {
    echo "BlameGPT Development Helper"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup       - Full setup (install dependencies, format code)"
    echo "  install     - Install all dependencies"
    echo "  format      - Format code with Black"
    echo "  build       - Build frontend"
    echo "  lint        - Run linting"
    echo "  dev         - Start development server"
    echo "  help        - Show this help message"
    echo ""
}

# Main script logic
case "$1" in
    "setup")
        print_status "Running full setup..."
        check_env
        install_python_deps
        install_node_deps
        format_code
        build_frontend
        run_lint
        print_status "Setup complete! Run '$0 dev' to start development server."
        ;;
    "install")
        install_python_deps
        install_node_deps
        ;;
    "format")
        format_code
        ;;
    "build")
        build_frontend
        ;;
    "lint")
        run_lint
        ;;
    "dev")
        start_dev
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac