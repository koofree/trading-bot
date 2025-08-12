#!/bin/bash

# Health check script for development environment

echo "🏥 Trading Bot Health Check"
echo "==========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Score tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Function to check service
check_service() {
    local service_name=$1
    local check_command=$2
    local port=$3
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -n "Checking $service_name... "
    
    if eval $check_command > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        
        if [ ! -z "$port" ]; then
            if lsof -i:$port > /dev/null 2>&1; then
                echo "  Port $port: ${GREEN}Open${NC}"
            else
                echo "  Port $port: ${YELLOW}Not listening${NC}"
            fi
        fi
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Function to check file/directory
check_path() {
    local path_type=$1
    local path=$2
    local description=$3
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -n "Checking $description... "
    
    if [ "$path_type" == "file" ] && [ -f "$path" ]; then
        echo -e "${GREEN}✓ Exists${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    elif [ "$path_type" == "dir" ] && [ -d "$path" ]; then
        echo -e "${GREEN}✓ Exists${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗ Missing${NC}"
        return 1
    fi
}

# Function to check Python package
check_python_package() {
    local package=$1
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -n "  Python package '$package'... "
    
    cd backend
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        if pip show $package > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        fi
    fi
    
    echo -e "${RED}✗${NC}"
    return 1
}

# Function to check npm package
check_npm_package() {
    local package=$1
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -n "  NPM package '$package'... "
    
    cd frontend
    if [ -d "node_modules/$package" ]; then
        echo -e "${GREEN}✓${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        cd ..
        return 0
    fi
    
    echo -e "${RED}✗${NC}"
    cd ..
    return 1
}

# Function to test API endpoint
test_api() {
    local endpoint=$1
    local description=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo -n "Testing $description... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint)
    
    if [ "$response" == "200" ]; then
        echo -e "${GREEN}✓ OK${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗ HTTP $response${NC}"
        return 1
    fi
}

echo ""
echo "📋 System Requirements"
echo "----------------------"

# Check Python
check_service "Python 3.10+" "python3 --version"

# Check Node.js
check_service "Node.js" "node --version"

# Check PostgreSQL
check_service "PostgreSQL" "psql --version" 5432

# Check Redis
check_service "Redis" "redis-cli ping" 6379

echo ""
echo "📁 Project Structure"
echo "--------------------"

# Check directories
check_path "dir" "backend" "Backend directory"
check_path "dir" "frontend" "Frontend directory"
check_path "dir" "uploads" "Uploads directory"
check_path "dir" "logs" "Logs directory"

# Check configuration files
check_path "file" ".env" "Environment file"
check_path "file" "backend/requirements.txt" "Python requirements"
check_path "file" "frontend/package.json" "NPM package.json"

echo ""
echo "🐍 Python Environment"
echo "---------------------"

check_path "dir" "backend/venv" "Virtual environment"

if [ -d "backend/venv" ]; then
    echo "Key packages:"
    check_python_package "fastapi"
    check_python_package "uvicorn"
    check_python_package "pandas"
    check_python_package "sqlalchemy"
    check_python_package "redis"
    check_python_package "openai"
fi

echo ""
echo "📦 Node.js Environment"
echo "----------------------"

check_path "dir" "frontend/node_modules" "Node modules"

if [ -d "frontend/node_modules" ]; then
    echo "Key packages:"
    check_npm_package "react"
    check_npm_package "react-use-websocket"
    check_npm_package "@mui/material"
    check_npm_package "chart.js"
    check_npm_package "axios"
fi

echo ""
echo "🌐 Services Status"
echo "------------------"

# Check if backend is running
if lsof -i:8000 > /dev/null 2>&1; then
    echo -e "Backend API: ${GREEN}✓ Running${NC} (http://localhost:8000)"
    
    # Test API endpoints
    echo "API Endpoints:"
    test_api "/" "Root endpoint"
    test_api "/api/health" "Health check"
    test_api "/docs" "API documentation"
else
    echo -e "Backend API: ${YELLOW}⚠ Not running${NC}"
    echo "  Start with: ./start-backend.sh"
fi

# Check if frontend is running
if lsof -i:3000 > /dev/null 2>&1; then
    echo -e "Frontend: ${GREEN}✓ Running${NC} (http://localhost:3000)"
else
    echo -e "Frontend: ${YELLOW}⚠ Not running${NC}"
    echo "  Start with: ./start-frontend.sh"
fi

echo ""
echo "🔐 API Keys Status"
echo "------------------"

if [ -f ".env" ]; then
    source .env
    
    # Check Upbit keys
    if [ ! -z "$UPBIT_ACCESS_KEY" ] && [ "$UPBIT_ACCESS_KEY" != "your_upbit_access_key" ]; then
        echo -e "Upbit API Keys: ${GREEN}✓ Configured${NC}"
    else
        echo -e "Upbit API Keys: ${YELLOW}⚠ Not configured${NC}"
    fi
    
    # Check OpenAI key
    if [ ! -z "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your_openai_api_key" ]; then
        echo -e "OpenAI API Key: ${GREEN}✓ Configured${NC}"
    else
        echo -e "OpenAI API Key: ${YELLOW}⚠ Not configured${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
fi

echo ""
echo "💾 Database Status"
echo "------------------"

# Check database connection
if PGPASSWORD=trading_password psql -U trading_user -d trading_bot -h localhost -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "Database connection: ${GREEN}✓ OK${NC}"
    
    # Count tables
    table_count=$(PGPASSWORD=trading_password psql -U trading_user -d trading_bot -h localhost -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'" 2>/dev/null | tr -d ' ')
    echo "  Tables: $table_count"
else
    echo -e "Database connection: ${RED}✗ Failed${NC}"
    echo "  Check PostgreSQL is running and credentials are correct"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "Redis connection: ${GREEN}✓ OK${NC}"
    
    # Get Redis info
    keys_count=$(redis-cli DBSIZE | awk '{print $2}')
    echo "  Keys: $keys_count"
else
    echo -e "Redis connection: ${RED}✗ Failed${NC}"
fi

echo ""
echo "📊 Health Check Summary"
echo "-----------------------"

# Calculate percentage
if [ $TOTAL_CHECKS -gt 0 ]; then
    PERCENTAGE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
else
    PERCENTAGE=0
fi

echo "Passed: $PASSED_CHECKS / $TOTAL_CHECKS checks ($PERCENTAGE%)"

if [ $PERCENTAGE -eq 100 ]; then
    echo -e "${GREEN}✨ System is fully operational!${NC}"
elif [ $PERCENTAGE -ge 75 ]; then
    echo -e "${GREEN}✓ System is mostly operational${NC}"
elif [ $PERCENTAGE -ge 50 ]; then
    echo -e "${YELLOW}⚠ System has some issues${NC}"
else
    echo -e "${RED}✗ System needs attention${NC}"
fi

echo ""
echo "💡 Quick Commands"
echo "-----------------"
echo "Start backend:  ./start-backend.sh"
echo "Start frontend: ./start-frontend.sh"
echo "Setup project:  ./setup.sh"
echo "Reset dev env:  ./dev-tools/reset-dev.sh"