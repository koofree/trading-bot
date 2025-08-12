#!/bin/bash

echo "🔧 Starting Trading Bot Development Environment"
echo "=============================================="

# Function to run commands in new terminal windows (macOS)
run_in_new_terminal() {
    local command="$1"
    local title="$2"
    
    osascript <<EOF
tell application "Terminal"
    do script "cd \"$(pwd)\" && $command"
    set custom title of front window to "$title"
end tell
EOF
}

# Check if PostgreSQL and Redis are running
echo "Ensuring database services are running..."
docker-compose up -d postgres redis

echo "Waiting for databases to be ready..."
sleep 5

echo ""
echo "🚀 Starting development servers in separate terminals..."
echo ""
echo "This will open:"
echo "  📦 Backend (FastAPI): http://localhost:8000"
echo "  ⚛️  Frontend (React): http://localhost:3000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo ""

# Start backend in new terminal
run_in_new_terminal "./start-backend-dev.sh" "Trading Bot - Backend"

# Wait a moment before starting frontend
sleep 2

# Start frontend in new terminal
run_in_new_terminal "./start-frontend-dev.sh" "Trading Bot - Frontend"

echo "✅ Development servers are starting in separate terminal windows"
echo ""
echo "To stop all services:"
echo "  - Close the terminal windows or press Ctrl+C in each"
echo "  - Run: docker-compose stop postgres redis"
echo ""
echo "Services:"
echo "  🐘 PostgreSQL: localhost:5432"
echo "  🔴 Redis: localhost:6379"