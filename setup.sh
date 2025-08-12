#!/bin/bash

# Trading Bot Local Development Setup Script

echo "🚀 Trading Bot Local Development Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        exit 1
    fi
}

# Check Python
echo -e "\n${YELLOW}Checking Python installation...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node.js
echo -e "\n${YELLOW}Checking Node.js installation...${NC}"
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"
else
    echo -e "${RED}✗${NC} Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check PostgreSQL
echo -e "\n${YELLOW}Checking PostgreSQL...${NC}"
if command_exists psql; then
    echo -e "${GREEN}✓${NC} PostgreSQL found"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL not found. You'll need to install it or use a remote database"
fi

# Check Redis
echo -e "\n${YELLOW}Checking Redis...${NC}"
if command_exists redis-cli; then
    echo -e "${GREEN}✓${NC} Redis found"
else
    echo -e "${YELLOW}⚠${NC} Redis not found. You'll need to install it or use a remote Redis server"
fi

# Setup Backend
echo -e "\n${YELLOW}Setting up Backend...${NC}"
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
print_status $? "Virtual environment created"

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_status $? "Pip upgraded"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
print_status $? "Python dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ../.env ]; then
    echo -e "\n${YELLOW}Creating .env file...${NC}"
    cp ../.env.example ../.env
    echo -e "${GREEN}✓${NC} .env file created from .env.example"
    echo -e "${YELLOW}⚠${NC} Please edit .env file with your API keys"
fi

# Setup Frontend
echo -e "\n${YELLOW}Setting up Frontend...${NC}"
cd ../frontend

# Install npm dependencies
echo "Installing npm dependencies..."
npm install
print_status $? "Frontend dependencies installed"

# Create frontend .env if needed
if [ ! -f .env ]; then
    echo "REACT_APP_API_URL=http://localhost:8000" > .env
    echo "REACT_APP_WS_URL=ws://localhost:8000/ws" >> .env
    echo -e "${GREEN}✓${NC} Frontend .env file created"
fi

cd ..

# Create necessary directories
echo -e "\n${YELLOW}Creating necessary directories...${NC}"
mkdir -p uploads logs
print_status $? "Directories created"

# Create start scripts
echo -e "\n${YELLOW}Creating start scripts...${NC}"

# Create backend start script
cat > start-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
EOF
chmod +x start-backend.sh
print_status $? "Backend start script created"

# Create frontend start script
cat > start-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
npm start
EOF
chmod +x start-frontend.sh
print_status $? "Frontend start script created"

# Create database setup script
cat > setup-database.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
python models/database.py
EOF
chmod +x setup-database.sh
print_status $? "Database setup script created"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Edit .env file with your API keys:"
echo "   - UPBIT_ACCESS_KEY"
echo "   - UPBIT_SECRET_KEY"
echo "   - OPENAI_API_KEY"
echo "   - DATABASE_URL (if using remote database)"
echo "   - REDIS_URL (if using remote Redis)"
echo ""
echo "2. Start PostgreSQL and Redis services:"
echo "   - PostgreSQL: brew services start postgresql (macOS)"
echo "   - Redis: brew services start redis (macOS)"
echo ""
echo "3. Initialize the database:"
echo "   ./setup-database.sh"
echo ""
echo "4. Start the application:"
echo "   - Backend: ./start-backend.sh"
echo "   - Frontend: ./start-frontend.sh (in new terminal)"
echo ""
echo "5. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"