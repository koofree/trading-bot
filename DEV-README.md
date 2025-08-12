# Trading Bot - Development Setup

This document explains how to run the trading bot in local development mode with hot reloading.

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop (for PostgreSQL and Redis)

## Quick Start

### Option 1: Start Everything at Once
```bash
./start-dev.sh
```
This will open separate terminal windows for backend and frontend with hot reload enabled.

### Option 2: Start Services Separately

#### Start Backend Only
```bash
./start-backend-dev.sh
```

#### Start Frontend Only  
```bash
./start-frontend-dev.sh
```

## Development Servers

Once running, you can access:

- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Hot Reload Features

### Backend (FastAPI)
- ✅ Automatic reload on Python file changes
- ✅ Uses virtual environment (`backend/dev-venv/`)
- ✅ Uvicorn with `--reload` flag
- ✅ Environment variables loaded from `.env`

### Frontend (React)
- ✅ Automatic reload on JS/JSX file changes
- ✅ Fast refresh for React components
- ✅ Error overlay for debugging
- ✅ CSS hot reload

## Database Services

The development setup uses Docker containers for:
- **PostgreSQL 15** - Main database
- **Redis 7** - Caching and session storage

These run separately from your application code to persist data between restarts.

## File Structure

```
trading-bot/
├── backend/                 # FastAPI backend
│   ├── dev-venv/           # Python virtual environment
│   ├── api/                # API routes
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/               # Source code
│   ├── public/            # Static assets  
│   └── package.json       # Node.js dependencies
├── .env                   # Environment variables
├── docker-compose.yml     # Database services
└── start-*.sh            # Development scripts
```

## Environment Variables

The `.env` file contains:
- Database connection strings (already configured)
- API keys (add your own for external services)
- Trading parameters
- Debug settings

## Stopping Services

### Stop Development Servers
- Press `Ctrl+C` in each terminal window
- Or close the terminal windows

### Stop Database Services
```bash
docker-compose stop postgres redis
```

### Stop Everything
```bash
docker-compose down
pkill -f "uvicorn api.main:app"
pkill -f "npm start"
```

## Troubleshooting

### Backend Issues
1. **Import errors**: Check if virtual environment is activated
2. **Database connection**: Ensure PostgreSQL container is running
3. **Port conflicts**: Make sure port 8000 is free

### Frontend Issues  
1. **Dependencies missing**: Run `npm install` in frontend directory
2. **Port conflicts**: Make sure port 3000 is free
3. **Build errors**: Check console for specific error messages

### Database Issues
1. **Connection refused**: Ensure Docker Desktop is running
2. **Data persistence**: Data is stored in Docker volumes
3. **Reset database**: `docker-compose down -v` (⚠️ destroys data)

## Development Tips

- Backend changes are reflected immediately (no restart needed)
- Frontend changes trigger automatic browser refresh
- API changes are documented at `/docs` endpoint
- Database changes require migration scripts
- Use browser dev tools for frontend debugging
- Check terminal output for backend errors

## Next Steps

1. Configure your API keys in `.env`
2. Set up your IDE for Python and JavaScript development  
3. Familiarize yourself with the API documentation
4. Start building your trading strategies!