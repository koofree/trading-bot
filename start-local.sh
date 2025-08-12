#!/bin/bash

echo "Starting Trading Bot Application..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "   1. Open Docker Desktop from Applications"
    echo "   2. Wait for Docker to start (whale icon in menu bar)"
    echo "   3. Run this script again"
    exit 1
fi

echo "✅ Docker is running"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_bot
REDIS_URL=redis://localhost:6379

# Upbit API (optional for local run)
UPBIT_ACCESS_KEY=your_upbit_access_key_here
UPBIT_SECRET_KEY=your_upbit_secret_key_here

# OpenAI (optional for local run)
OPENAI_API_KEY=your_openai_api_key_here

# Trading Configuration
BASE_POSITION_SIZE=0.02
RISK_PER_TRADE=0.01
MAX_POSITIONS=5
DAILY_LOSS_LIMIT=0.05
STOP_LOSS_PERCENTAGE=0.03
TAKE_PROFIT_PERCENTAGE=0.06

# App
DEBUG=True
SECRET_KEY=dev-secret-key
EOF
    echo "✅ .env file created with default values"
fi

# Create necessary directories
mkdir -p uploads logs

# Stop any running containers
echo "Stopping any existing containers..."
docker-compose down 2>/dev/null

# Build and start services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "Service Status:"
echo "==============="
docker-compose ps

echo ""
echo "Application URLs:"
echo "================="
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Documentation: http://localhost:8000/docs"
echo ""
echo "Database Connections:"
echo "===================="
echo "📦 PostgreSQL: localhost:5432"
echo "💾 Redis: localhost:6379"
echo ""
echo "To view logs:"
echo "============="
echo "All services: docker-compose logs -f"
echo "Backend only: docker-compose logs -f backend"
echo "Frontend only: docker-compose logs -f frontend"
echo ""
echo "To stop the application:"
echo "========================"
echo "docker-compose down"