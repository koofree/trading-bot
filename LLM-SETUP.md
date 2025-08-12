# LLM Configuration Guide

This trading bot supports multiple LLM providers for market analysis. You can use local models (recommended for privacy and cost) or cloud-based APIs.

## Quick Start with Ollama (Recommended)

Ollama is the easiest way to run local LLMs:

```bash
# Automatic setup
./setup-ollama.sh

# Manual setup
brew install ollama  # macOS
ollama serve        # Start server
ollama pull llama2  # Download model
```

## Supported Providers

### 1. Ollama (Local, Free)
**Best for**: Privacy, no API costs, offline usage

```bash
# Install and setup
./setup-ollama.sh

# Configuration in .env
LLM_PROVIDER=ollama
LLM_MODEL=llama2  # or mistral, codellama, etc.
LLM_BASE_URL=http://localhost:11434
```

**Available Models**:
- `llama2` - Balanced performance (7B)
- `mistral` - Faster, efficient (7B)
- `codellama` - Code-optimized
- `neural-chat` - Conversational
- `dolphin-mixtral` - Uncensored

### 2. OpenAI (Cloud, Paid)
**Best for**: Best quality, no local setup needed

```bash
# Configuration in .env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4  # or gpt-3.5-turbo
LLM_API_KEY=your_openai_api_key_here
```

### 3. LocalAI (Local, OpenAI-compatible)
**Best for**: Multiple model formats, Docker deployment

```bash
# Run LocalAI
docker run -p 8080:8080 -v $PWD/models:/models \
  quay.io/go-skynet/local-ai:latest

# Configuration in .env
LLM_PROVIDER=localai
LLM_MODEL=ggml-gpt4all-j
LLM_BASE_URL=http://localhost:8080/v1
```

### 4. LM Studio (Local, GUI)
**Best for**: Desktop users, easy model management

```bash
# Download from https://lmstudio.ai/
# Start server in app

# Configuration in .env
LLM_PROVIDER=lmstudio
LLM_MODEL=local-model
LLM_BASE_URL=http://localhost:1234/v1
```

### 5. vLLM (High-Performance, Local/Cloud)
**Best for**: Production workloads, maximum throughput, GPU optimization

```bash
# Automatic setup
./setup-vllm.sh

# Docker setup (recommended)
docker run -d --name vllm-server \
  --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-2-7b-chat-hf \
  --port 8000

# Configuration in .env
LLM_PROVIDER=vllm
LLM_MODEL=meta-llama/Llama-2-7b-chat-hf
LLM_BASE_URL=http://localhost:8000
```

**Key Features**:
- 2-4x faster inference than standard methods
- PagedAttention for efficient memory usage
- Continuous batching for higher throughput
- OpenAI-compatible API
- Supports HuggingFace models directly

**Available Models**:
- `meta-llama/Llama-2-7b-chat-hf` - Llama 2 7B
- `mistralai/Mistral-7B-Instruct-v0.1` - Mistral 7B
- `NousResearch/Meta-Llama-3-8B-Instruct` - Llama 3 8B
- `codellama/CodeLlama-7b-Instruct-hf` - CodeLlama 7B

## Testing Your Setup

```bash
# Test LLM integration
python3 test-llm.py

# Test with backend
./start-backend-dev.sh
./test-backend.sh
```

## Configuration Options

Edit `.env` to configure your LLM:

```env
# Provider: ollama, openai, localai, lmstudio, vllm
LLM_PROVIDER=ollama

# Model name (depends on provider)
LLM_MODEL=llama2

# API Key (only for OpenAI)
LLM_API_KEY=

# Base URL (for local services)
LLM_BASE_URL=http://localhost:11434
```

## Switching Providers

To switch between providers, use the pre-configured examples:

```bash
# Use Ollama
cp llm-configs/ollama.env .env

# Use OpenAI
cp llm-configs/openai.env .env
# Add your API key to .env

# Use LocalAI
cp llm-configs/localai.env .env

# Use LM Studio
cp llm-configs/lmstudio.env .env

# Use vLLM
cp llm-configs/vllm.env .env
./setup-vllm.sh  # Run setup script
```

## Model Recommendations

### For Trading Analysis:
- **Ollama**: `llama2` or `mistral` (good balance)
- **OpenAI**: `gpt-4` (best quality) or `gpt-3.5-turbo` (faster)
- **vLLM**: `meta-llama/Llama-2-7b-chat-hf` or `mistralai/Mistral-7B-Instruct-v0.1` (production-ready)

### For Speed:
- **vLLM**: Any model (2-4x faster than alternatives)
- **Ollama**: `mistral` (7B, optimized)
- **OpenAI**: `gpt-3.5-turbo`

### For High Throughput:
- **vLLM**: Best choice with continuous batching
- **OpenAI**: Good with concurrent requests

### For Privacy:
- Any local provider (Ollama, LocalAI, LM Studio, vLLM)

## Troubleshooting

### Ollama Issues:
```bash
# Check if running
curl http://localhost:11434/api/tags

# Restart service
pkill ollama
ollama serve &

# Pull model again
ollama pull llama2
```

### vLLM Issues:
```bash
# Check if running
curl http://localhost:8000/health

# Check Docker logs
docker logs vllm-server

# Restart container
docker restart vllm-server

# Check GPU availability
nvidia-smi
```

### Connection Errors:
1. Check the service is running
2. Verify the base URL in `.env`
3. Test with `curl` or `test-llm.py`

### Slow Performance:
- Use vLLM for maximum speed
- Use smaller models (mistral vs llama2)
- Reduce `max_tokens` in code
- Consider GPU acceleration

## API Compatibility

All providers implement the same interface:
- OpenAI-compatible chat completions
- Structured JSON responses
- Async support

The trading bot automatically handles differences between providers.

## Cost Comparison

| Provider | Cost | Speed | Quality | Privacy |
|----------|------|-------|---------|---------|
| Ollama | Free | Medium | Good | Excellent |
| OpenAI | Paid | Fast | Best | Limited |
| LocalAI | Free | Slow-Medium | Good | Excellent |
| LM Studio | Free | Medium | Good | Excellent |
| vLLM | Free | Fastest | Good | Excellent |

## Advanced Configuration

### Custom OpenAI-Compatible Endpoints

Any OpenAI-compatible API can be used:

```env
LLM_PROVIDER=openai
LLM_MODEL=your-model
LLM_API_KEY=your-key
LLM_BASE_URL=https://your-api.com/v1
```

### Multiple Models

You can run different models for different tasks by modifying the code:

```python
# In backend/api/main.py
llm_config_analysis = {
    'provider': 'ollama',
    'model': 'llama2'
}

llm_config_fast = {
    'provider': 'ollama', 
    'model': 'mistral'
}
```

## Performance Tips

1. **Pre-load models**: Start Ollama/vLLM before trading hours
2. **Use appropriate models**: Smaller for speed, larger for quality
3. **Cache responses**: The app caches recent analyses
4. **Batch requests**: Group multiple analyses together
5. **Use vLLM for production**: Best performance with GPU acceleration
6. **Configure GPU memory**: vLLM can use `--gpu-memory-utilization 0.9` for max performance

## Security Notes

- Local models keep your data private
- API keys should never be committed to git
- Use `.env` files for configuration
- Consider network isolation for production