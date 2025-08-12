#!/bin/bash

echo "🚀 Starting Backend Development Server"
echo "====================================="

# Check if PostgreSQL and Redis are running
echo "Checking database services..."

if ! docker-compose ps postgres | grep -q "Up"; then
    echo "🟡 Starting PostgreSQL..."
    docker-compose up -d postgres
    sleep 3
fi

if ! docker-compose ps redis | grep -q "Up"; then
    echo "🟡 Starting Redis..."
    docker-compose up -d redis
    sleep 3
fi

echo "✅ Database services are running"

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "dev-venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv dev-venv
    source dev-venv/bin/activate
    pip install -r requirements.txt
else
    source dev-venv/bin/activate
fi

echo "🌐 Starting FastAPI server with hot reload on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server with hot reload
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload