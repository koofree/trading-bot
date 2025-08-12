#!/bin/bash

echo "🤖 Ollama Setup for Trading Bot"
echo "================================"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📦 Ollama not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "Installing Ollama for macOS..."
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Installing Ollama for Linux..."
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "❌ Unsupported OS. Please install Ollama manually from https://ollama.ai"
        exit 1
    fi
else
    echo "✅ Ollama is already installed"
fi

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &
    sleep 3
else
    echo "✅ Ollama is already running"
fi

# List available models
echo ""
echo "📚 Available models:"
ollama list

# Pull recommended model if not present
echo ""
echo "🔍 Checking for recommended model (llama2)..."
if ! ollama list | grep -q "llama2"; then
    echo "📥 Pulling llama2 model (this may take a while)..."
    ollama pull llama2
else
    echo "✅ llama2 model is already available"
fi

# Pull additional lightweight model
echo ""
echo "🔍 Checking for fast model (mistral)..."
if ! ollama list | grep -q "mistral"; then
    echo "📥 Pulling mistral model (faster alternative)..."
    ollama pull mistral
else
    echo "✅ mistral model is already available"
fi

# Test Ollama API
echo ""
echo "🧪 Testing Ollama API..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags)

if [ "$response" = "200" ]; then
    echo "✅ Ollama API is working!"
else
    echo "❌ Ollama API test failed. Please check the service."
    exit 1
fi

# Update .env file to use Ollama
echo ""
echo "📝 Configuring Trading Bot to use Ollama..."

if [ -f .env ]; then
    # Backup existing .env
    cp .env .env.backup
    echo "✅ Backed up existing .env to .env.backup"
fi

# Update or add LLM configuration
if [ -f .env ]; then
    # Update existing .env
    sed -i.bak '/^LLM_PROVIDER=/d' .env
    sed -i.bak '/^LLM_MODEL=/d' .env
    sed -i.bak '/^LLM_BASE_URL=/d' .env
    
    echo "" >> .env
    echo "# LLM Configuration (Ollama)" >> .env
    echo "LLM_PROVIDER=ollama" >> .env
    echo "LLM_MODEL=llama2" >> .env
    echo "LLM_BASE_URL=http://localhost:11434" >> .env
else
    # Create new .env from example
    cp llm-configs/ollama.env .env
    cat >> .env << 'EOF'

# Database
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_bot
REDIS_URL=redis://localhost:6379

# Upbit API (optional for local run)
UPBIT_ACCESS_KEY=your_upbit_access_key_here
UPBIT_SECRET_KEY=your_upbit_secret_key_here

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
fi

echo ""
echo "🎉 Ollama setup complete!"
echo ""
echo "Configuration:"
echo "=============="
echo "Provider: Ollama"
echo "Model: llama2"
echo "API URL: http://localhost:11434"
echo ""
echo "Available models to try:"
echo "- llama2 (default, balanced)"
echo "- mistral (faster, lighter)"
echo ""
echo "To change model, edit .env and set:"
echo "  LLM_MODEL=mistral"
echo ""
echo "To test the integration:"
echo "  ./start-backend-dev.sh"
echo ""
echo "To pull more models:"
echo "  ollama pull codellama    # For code analysis"
echo "  ollama pull neural-chat  # For conversational AI"
echo "  ollama pull dolphin-mixtral  # Uncensored model"