#!/bin/bash

echo "🚀 vLLM Setup for Trading Bot"
echo "=============================="
echo ""
echo "vLLM is a high-performance inference server optimized for LLMs"
echo "It provides OpenAI-compatible API with significant speed improvements"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required for vLLM (found $python_version)"
    exit 1
fi

echo "✅ Python version: $python_version"

# Option 1: Docker installation (recommended)
echo ""
echo "Choose installation method:"
echo "1) Docker (recommended, easier)"
echo "2) Pip (local installation)"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "📦 Docker Installation"
    echo "====================="
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
    
    echo "Select a model to run:"
    echo "1) Llama-2-7B (recommended, 7GB VRAM)"
    echo "2) Mistral-7B (faster, 7GB VRAM)"
    echo "3) CodeLlama-7B (for code, 7GB VRAM)"
    echo "4) Custom model"
    echo ""
    read -p "Enter choice (1-4): " model_choice
    
    case $model_choice in
        1)
            MODEL="meta-llama/Llama-2-7b-chat-hf"
            ;;
        2)
            MODEL="mistralai/Mistral-7B-Instruct-v0.1"
            ;;
        3)
            MODEL="codellama/CodeLlama-7b-Instruct-hf"
            ;;
        4)
            read -p "Enter HuggingFace model name: " MODEL
            ;;
        *)
            MODEL="meta-llama/Llama-2-7b-chat-hf"
            ;;
    esac
    
    echo ""
    echo "🐳 Starting vLLM Docker container with $MODEL..."
    echo ""
    
    # Stop any existing vLLM container
    docker stop vllm-server 2>/dev/null
    docker rm vllm-server 2>/dev/null
    
    # Run vLLM Docker container
    docker run -d \
        --name vllm-server \
        --gpus all \
        -p 8000:8000 \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        --ipc=host \
        vllm/vllm-openai:latest \
        --model "$MODEL" \
        --port 8000 \
        --max-model-len 4096
    
    echo "✅ vLLM Docker container started"
    echo ""
    echo "To check logs: docker logs -f vllm-server"
    echo "To stop: docker stop vllm-server"
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "📦 Pip Installation"
    echo "=================="
    
    # Check for CUDA
    if command -v nvidia-smi &> /dev/null; then
        echo "✅ NVIDIA GPU detected"
        nvidia-smi --query-gpu=name,memory.total --format=csv
    else
        echo "⚠️  No NVIDIA GPU detected. vLLM requires CUDA-capable GPU."
        echo "   You can still install for CPU inference (much slower)."
        read -p "Continue anyway? (y/n): " continue_cpu
        if [ "$continue_cpu" != "y" ]; then
            exit 1
        fi
    fi
    
    echo ""
    echo "Installing vLLM..."
    pip install vllm
    
    if [ $? -ne 0 ]; then
        echo "❌ vLLM installation failed"
        echo "Try: pip install vllm --upgrade"
        exit 1
    fi
    
    echo "✅ vLLM installed"
    
    echo ""
    echo "Select a model to download and run:"
    echo "1) Llama-2-7B (7GB VRAM required)"
    echo "2) Mistral-7B (7GB VRAM required)"
    echo "3) CodeLlama-7B (7GB VRAM required)"
    echo "4) Skip model download"
    echo ""
    read -p "Enter choice (1-4): " model_choice
    
    case $model_choice in
        1)
            MODEL="meta-llama/Llama-2-7b-chat-hf"
            ;;
        2)
            MODEL="mistralai/Mistral-7B-Instruct-v0.1"
            ;;
        3)
            MODEL="codellama/CodeLlama-7b-Instruct-hf"
            ;;
        4)
            echo "Skipping model download"
            MODEL=""
            ;;
        *)
            MODEL="meta-llama/Llama-2-7b-chat-hf"
            ;;
    esac
    
    if [ -n "$MODEL" ]; then
        echo ""
        echo "Starting vLLM server with $MODEL..."
        echo "This will download the model if not cached (may take time)..."
        echo ""
        
        # Create start script
        cat > start-vllm-server.sh << EOF
#!/bin/bash
python -m vllm.entrypoints.openai.api_server \\
    --model "$MODEL" \\
    --port 8000 \\
    --max-model-len 4096 \\
    --gpu-memory-utilization 0.9
EOF
        chmod +x start-vllm-server.sh
        
        echo "✅ Created start-vllm-server.sh"
        echo ""
        echo "To start vLLM server:"
        echo "  ./start-vllm-server.sh"
    fi
fi

# Test vLLM API
echo ""
echo "🧪 Testing vLLM API..."
sleep 5

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$response" = "200" ]; then
    echo "✅ vLLM API is working!"
else
    echo "⚠️  vLLM API not responding yet. It may still be loading the model."
    echo "   Check status with: curl http://localhost:8000/health"
fi

# Update .env file
echo ""
echo "📝 Configuring Trading Bot to use vLLM..."

if [ -f .env ]; then
    cp .env .env.backup
    echo "✅ Backed up existing .env to .env.backup"
fi

# Update or add LLM configuration
if [ -f .env ]; then
    sed -i.bak '/^LLM_PROVIDER=/d' .env
    sed -i.bak '/^LLM_MODEL=/d' .env
    sed -i.bak '/^LLM_BASE_URL=/d' .env
    
    echo "" >> .env
    echo "# LLM Configuration (vLLM)" >> .env
    echo "LLM_PROVIDER=vllm" >> .env
    echo "LLM_MODEL=${MODEL:-meta-llama/Llama-2-7b-chat-hf}" >> .env
    echo "LLM_BASE_URL=http://localhost:8000" >> .env
else
    cp llm-configs/vllm.env .env
fi

echo ""
echo "🎉 vLLM setup complete!"
echo ""
echo "Configuration:"
echo "============="
echo "Provider: vLLM"
echo "Model: ${MODEL:-[Select your model]}"
echo "API URL: http://localhost:8000"
echo ""
echo "vLLM Features:"
echo "- ⚡ 2-4x faster than standard inference"
echo "- 📊 Continuous batching for higher throughput"
echo "- 🔧 PagedAttention for efficient memory usage"
echo "- 🔌 OpenAI-compatible API"
echo ""
echo "To test the integration:"
echo "  python3 test-llm.py"
echo ""
echo "For more models, visit:"
echo "  https://huggingface.co/models?pipeline_tag=text-generation"