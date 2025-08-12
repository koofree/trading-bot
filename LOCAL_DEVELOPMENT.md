# Local Development Guide

This guide explains how to set up and run the Trading Bot in local development mode without Docker.

## Prerequisites

### Required Software

1. **Python 3.10+**
   - macOS: `brew install python@3.10`
   - Ubuntu/Debian: `sudo apt install python3.10 python3.10-venv`
   - Windows: Download from [python.org](https://www.python.org/)

2. **Node.js 18+**
   - macOS: `brew install node`
   - Ubuntu/Debian: `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs`
   - Windows: Download from [nodejs.org](https://nodejs.org/)

3. **PostgreSQL 15+**
   - macOS: `brew install postgresql@15 && brew services start postgresql@15`
   - Ubuntu/Debian: `sudo apt install postgresql-15`
   - Windows: Download from [postgresql.org](https://www.postgresql.org/download/windows/)

4. **Redis 7+**
   - macOS: `brew install redis && brew services start redis`
   - Ubuntu/Debian: `sudo apt install redis-server`
   - Windows: Download from [redis.io](https://redis.io/download/) or use WSL

## Quick Setup

### macOS/Linux

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup script
./setup.sh

# This will:
# 1. Check all prerequisites
# 2. Create Python virtual environment
# 3. Install all dependencies
# 4. Create necessary directories
# 5. Generate start scripts
```

### Windows

```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup script
.\setup-windows.ps1
```

## Manual Setup

### 1. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE trading_bot;
CREATE USER trading_user WITH PASSWORD 'trading_password';
GRANT ALL PRIVILEGES ON DATABASE trading_bot TO trading_user;
\q

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or create .env file)
export DATABASE_URL="postgresql://trading_user:trading_password@localhost:5432/trading_bot"
export REDIS_URL="redis://localhost:6379"
export UPBIT_ACCESS_KEY="your_upbit_access_key"
export UPBIT_SECRET_KEY="your_upbit_secret_key"
export OPENAI_API_KEY="your_openai_api_key"

# Initialize database
python models/database.py

# Start backend server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000" > .env
echo "REACT_APP_WS_URL=ws://localhost:8000/ws" >> .env

# Start development server
npm start
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_bot
REDIS_URL=redis://localhost:6379

# Upbit API
UPBIT_ACCESS_KEY=your_upbit_access_key_here
UPBIT_SECRET_KEY=your_upbit_secret_key_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Trading Configuration
BASE_POSITION_SIZE=0.02
RISK_PER_TRADE=0.01
MAX_POSITIONS=5
DAILY_LOSS_LIMIT=0.05
STOP_LOSS_PERCENTAGE=0.03
TAKE_PROFIT_PERCENTAGE=0.06

# Application
DEBUG=True
SECRET_KEY=your-secret-key-here
```

## Development Workflow

### Starting Services

1. **Start Database Services**
   ```bash
   # macOS
   brew services start postgresql@15
   brew services start redis
   
   # Ubuntu/Debian
   sudo systemctl start postgresql
   sudo systemctl start redis-server
   
   # Windows (use separate terminals)
   pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start
   redis-server
   ```

2. **Start Backend** (Terminal 1)
   ```bash
   ./start-backend.sh
   # Or manually:
   cd backend
   source venv/bin/activate
   uvicorn api.main:app --reload --port 8000
   ```

3. **Start Frontend** (Terminal 2)
   ```bash
   ./start-frontend.sh
   # Or manually:
   cd frontend
   npm start
   ```

### Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## Common Development Tasks

### Installing New Python Packages

```bash
cd backend
source venv/bin/activate
pip install package-name
pip freeze > requirements.txt
```

### Installing New NPM Packages

```bash
cd frontend
npm install package-name
# or
npm install --save-dev package-name
```

### Database Migrations

```bash
cd backend
source venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Tests

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Frontend tests with coverage
npm test -- --coverage
```

### Debugging

#### Backend Debugging

1. **VS Code**: Add this to `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: FastAPI",
         "type": "python",
         "request": "launch",
         "module": "uvicorn",
         "args": ["api.main:app", "--reload", "--port", "8000"],
         "cwd": "${workspaceFolder}/backend",
         "env": {
           "PYTHONPATH": "${workspaceFolder}/backend"
         }
       }
     ]
   }
   ```

2. **PyCharm**: 
   - Set up a Python interpreter with the virtual environment
   - Create a FastAPI run configuration

#### Frontend Debugging

1. **Chrome DevTools**: Press F12 in browser
2. **React Developer Tools**: Install browser extension
3. **VS Code**: Debug with Chrome extension

### Logs and Monitoring

```bash
# View backend logs
tail -f logs/trading_bot.log

# Monitor Redis
redis-cli monitor

# PostgreSQL logs
# macOS
tail -f /usr/local/var/log/postgresql@15.log
# Linux
tail -f /var/log/postgresql/postgresql-15-main.log
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Check connection
psql -U trading_user -d trading_bot -h localhost

# Reset database
cd backend
source venv/bin/activate
python -c "from models.database import drop_db, init_db; drop_db(); init_db()"
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Clear Redis cache
redis-cli FLUSHALL
```

### Frontend Build Issues

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Performance Optimization

### Backend

1. **Use connection pooling** (already configured)
2. **Enable query caching** in Redis
3. **Use async operations** where possible
4. **Profile with `cProfile`**:
   ```python
   python -m cProfile -o profile.stats api/main.py
   ```

### Frontend

1. **Use React.memo** for expensive components
2. **Implement virtual scrolling** for long lists
3. **Optimize bundle size**:
   ```bash
   npm run build
   npm run analyze
   ```

## VS Code Extensions

Recommended extensions for development:

- Python
- Pylance
- Black Formatter
- ESLint
- Prettier
- Thunder Client (API testing)
- SQLTools
- Redis

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Upbit API Documentation](https://docs.upbit.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

## Support

If you encounter issues:

1. Check the logs in `logs/` directory
2. Verify all services are running
3. Ensure environment variables are set correctly
4. Check API keys are valid
5. Review error messages in browser console