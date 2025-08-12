# Trading Bot Local Development Setup Script for Windows

Write-Host "🚀 Trading Bot Local Development Setup (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check Python
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
if (Test-Command python) {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "✗ Python 3 not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "`nChecking Node.js installation..." -ForegroundColor Yellow
if (Test-Command node) {
    $nodeVersion = node --version
    Write-Host "✓ Node.js $nodeVersion found" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
Write-Host "`nChecking PostgreSQL..." -ForegroundColor Yellow
if (Test-Command psql) {
    Write-Host "✓ PostgreSQL found" -ForegroundColor Green
} else {
    Write-Host "⚠ PostgreSQL not found. You'll need to install it or use a remote database" -ForegroundColor Yellow
}

# Check Redis
Write-Host "`nChecking Redis..." -ForegroundColor Yellow
if (Test-Command redis-cli) {
    Write-Host "✓ Redis found" -ForegroundColor Green
} else {
    Write-Host "⚠ Redis not found. You'll need to install it or use a remote Redis server" -ForegroundColor Yellow
}

# Setup Backend
Write-Host "`nSetting up Backend..." -ForegroundColor Yellow
Set-Location backend

# Create virtual environment
Write-Host "Creating Python virtual environment..."
python -m venv venv
if ($?) {
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip | Out-Null
if ($?) {
    Write-Host "✓ Pip upgraded" -ForegroundColor Green
}

# Install Python dependencies
Write-Host "Installing Python dependencies..."
pip install -r requirements.txt
if ($?) {
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (!(Test-Path ..\.env)) {
    Write-Host "`nCreating .env file..." -ForegroundColor Yellow
    Copy-Item ..\.env.example ..\.env
    Write-Host "✓ .env file created from .env.example" -ForegroundColor Green
    Write-Host "⚠ Please edit .env file with your API keys" -ForegroundColor Yellow
}

# Setup Frontend
Write-Host "`nSetting up Frontend..." -ForegroundColor Yellow
Set-Location ..\frontend

# Install npm dependencies
Write-Host "Installing npm dependencies..."
npm install
if ($?) {
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}

# Create frontend .env if needed
if (!(Test-Path .env)) {
    @"
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
"@ | Out-File -FilePath .env -Encoding UTF8
    Write-Host "✓ Frontend .env file created" -ForegroundColor Green
}

Set-Location ..

# Create necessary directories
Write-Host "`nCreating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path uploads, logs | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

# Create start scripts
Write-Host "`nCreating start scripts..." -ForegroundColor Yellow

# Create backend start script
@"
@echo off
cd backend
call venv\Scripts\activate
set PYTHONPATH=%PYTHONPATH%;%cd%
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"@ | Out-File -FilePath start-backend.bat -Encoding ASCII
Write-Host "✓ Backend start script created (start-backend.bat)" -ForegroundColor Green

# Create frontend start script
@"
@echo off
cd frontend
npm start
"@ | Out-File -FilePath start-frontend.bat -Encoding ASCII
Write-Host "✓ Frontend start script created (start-frontend.bat)" -ForegroundColor Green

# Create database setup script
@"
@echo off
cd backend
call venv\Scripts\activate
python models\database.py
"@ | Out-File -FilePath setup-database.bat -Encoding ASCII
Write-Host "✓ Database setup script created (setup-database.bat)" -ForegroundColor Green

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your API keys:"
Write-Host "   - UPBIT_ACCESS_KEY"
Write-Host "   - UPBIT_SECRET_KEY"
Write-Host "   - OPENAI_API_KEY"
Write-Host "   - DATABASE_URL (if using remote database)"
Write-Host "   - REDIS_URL (if using remote Redis)"
Write-Host ""
Write-Host "2. Start PostgreSQL and Redis services"
Write-Host ""
Write-Host "3. Initialize the database:"
Write-Host "   .\setup-database.bat"
Write-Host ""
Write-Host "4. Start the application:"
Write-Host "   - Backend: .\start-backend.bat"
Write-Host "   - Frontend: .\start-frontend.bat (in new terminal)"
Write-Host ""
Write-Host "5. Access the application:"
Write-Host "   - Frontend: http://localhost:3000"
Write-Host "   - Backend API: http://localhost:8000"
Write-Host "   - API Docs: http://localhost:8000/docs"