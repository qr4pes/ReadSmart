#!/bin/bash

# Website Analyzer - Local Setup Script
# This script helps set up the local development environment

set -e

echo "=================================="
echo "Website Analyzer - Setup Script"
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OpenAI API key!"
    echo "   Get your API key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter after you've added your API key to .env file..."
else
    echo "✓ .env file already exists"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and run this script again"
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Ask user for setup method
echo "Choose setup method:"
echo "1) Docker Compose (Recommended - includes PostgreSQL)"
echo "2) Local Python (requires PostgreSQL already installed)"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "Setting up with Docker Compose..."
    echo ""

    # Build and start containers
    echo "Building Docker images..."
    docker-compose build

    echo ""
    echo "Starting services..."
    docker-compose up -d

    echo ""
    echo "Waiting for services to be ready..."
    sleep 10

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        echo ""
        echo "=================================="
        echo "✓ Setup Complete!"
        echo "=================================="
        echo ""
        echo "Access the application at:"
        echo "  Frontend: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo "  API:      http://localhost:8000/api"
        echo ""
        echo "View logs with:"
        echo "  docker-compose logs -f backend"
        echo ""
        echo "Stop the application with:"
        echo "  docker-compose down"
        echo ""
    else
        echo ""
        echo "❌ Error: Services failed to start"
        echo "Check logs with: docker-compose logs"
        exit 1
    fi

elif [ "$choice" = "2" ]; then
    echo ""
    echo "Setting up with Local Python..."
    echo ""

    # Check if PostgreSQL is running
    if ! pg_isready > /dev/null 2>&1; then
        echo "⚠️  Warning: PostgreSQL doesn't appear to be running"
        echo "   Please make sure PostgreSQL is installed and running"
        echo ""
        read -p "Continue anyway? (y/n): " continue
        if [ "$continue" != "y" ]; then
            exit 1
        fi
    fi

    # Check if Python 3.11+ is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: Python 3 is not installed"
        exit 1
    fi

    echo "✓ Python 3 found"
    echo ""

    # Create virtual environment
    cd backend
    echo "Creating Python virtual environment..."
    python3 -m venv venv

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    echo ""
    echo "=================================="
    echo "✓ Setup Complete!"
    echo "=================================="
    echo ""
    echo "To start the application:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "Then access at:"
    echo "  Frontend: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""

else
    echo "Invalid choice"
    exit 1
fi
