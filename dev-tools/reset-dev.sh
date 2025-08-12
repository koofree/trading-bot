#!/bin/bash

# Development environment reset script

echo "🔄 Resetting Development Environment"
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Confirmation
read -p "This will reset your development environment. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Kill running processes
echo -e "\n${YELLOW}Stopping running processes...${NC}"

# Kill backend process
if lsof -i:8000 > /dev/null 2>&1; then
    echo "Stopping backend server..."
    kill $(lsof -t -i:8000) 2>/dev/null
    echo -e "${GREEN}✓${NC} Backend stopped"
fi

# Kill frontend process
if lsof -i:3000 > /dev/null 2>&1; then
    echo "Stopping frontend server..."
    kill $(lsof -t -i:3000) 2>/dev/null
    echo -e "${GREEN}✓${NC} Frontend stopped"
fi

# Clean Python environment
echo -e "\n${YELLOW}Cleaning Python environment...${NC}"
cd backend
if [ -d "venv" ]; then
    rm -rf venv
    echo -e "${GREEN}✓${NC} Virtual environment removed"
fi
rm -rf __pycache__ .pytest_cache *.pyc
rm -rf **/__pycache__ **/*.pyc
echo -e "${GREEN}✓${NC} Python cache cleaned"

# Clean Node environment
echo -e "\n${YELLOW}Cleaning Node environment...${NC}"
cd ../frontend
if [ -d "node_modules" ]; then
    rm -rf node_modules
    echo -e "${GREEN}✓${NC} node_modules removed"
fi
if [ -f "package-lock.json" ]; then
    rm package-lock.json
    echo -e "${GREEN}✓${NC} package-lock.json removed"
fi
rm -rf build .cache
echo -e "${GREEN}✓${NC} Build artifacts cleaned"

# Clear Redis cache
echo -e "\n${YELLOW}Clearing Redis cache...${NC}"
if command -v redis-cli &> /dev/null; then
    redis-cli FLUSHALL > /dev/null 2>&1
    echo -e "${GREEN}✓${NC} Redis cache cleared"
else
    echo -e "${YELLOW}⚠${NC} Redis not found"
fi

# Reset database
echo -e "\n${YELLOW}Resetting database...${NC}"
read -p "Reset database? This will delete all data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ../backend
    
    # Drop and recreate database
    PGPASSWORD=trading_password psql -U trading_user -d postgres << EOF
DROP DATABASE IF EXISTS trading_bot;
CREATE DATABASE trading_bot;
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Database reset"
    else
        echo -e "${YELLOW}⚠${NC} Could not reset database. You may need to do this manually."
    fi
fi

# Clean logs and uploads
echo -e "\n${YELLOW}Cleaning temporary files...${NC}"
cd ..
if [ -d "logs" ]; then
    rm -rf logs/*
    echo -e "${GREEN}✓${NC} Logs cleaned"
fi
if [ -d "uploads" ]; then
    rm -rf uploads/*
    echo -e "${GREEN}✓${NC} Uploads cleaned"
fi

# Recreate environment
echo -e "\n${YELLOW}Recreating environment...${NC}"
read -p "Reinstall dependencies? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    # Backend setup
    echo "Setting up backend..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Backend dependencies installed"
    else
        echo -e "${RED}✗${NC} Failed to install backend dependencies"
    fi
    
    # Initialize database
    python models/database.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Database initialized"
    fi
    
    # Frontend setup
    echo "Setting up frontend..."
    cd ../frontend
    npm install
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Frontend dependencies installed"
    else
        echo -e "${RED}✗${NC} Failed to install frontend dependencies"
    fi
fi

cd ..

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Development environment reset complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Check your .env file is still configured"
echo "2. Start the backend: ./start-backend.sh"
echo "3. Start the frontend: ./start-frontend.sh"