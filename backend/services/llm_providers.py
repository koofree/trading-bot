"""
LLM Provider abstraction layer for supporting multiple LLM backends
Supports: OpenAI, Ollama, and any OpenAI-compatible API
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import aiohttp
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request to LLM"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Test if the LLM service is accessible"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""

    def __init__(
        self, api_key: str, model: str = "gpt-4", base_url: Optional[str] = None
    ):
        self.api_key = api_key
        self.model = model
        self.client = (
            OpenAI(
                api_key=api_key,
                base_url=base_url,  # Allows using OpenAI-compatible APIs
            )
            if api_key and api_key != "your_openai_api_key_here"
            else None
        )

    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request to OpenAI"""
        if not self.client:
            logger.warning("OpenAI client not initialized")
            return "{}"

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 1000),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise

    def validate_connection(self) -> bool:
        """Test OpenAI API connection"""
        if not self.client:
            return False

        try:
            response = self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""

    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_endpoint = f"{self.base_url}/api/chat"

    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request to Ollama"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.3),
                "num_predict": kwargs.get("max_tokens", 1000),
            },
        }

        logger.info(f"Ollama request - Model: {self.model}, Endpoint: {self.api_endpoint}")
        logger.debug(f"Ollama payload: {json.dumps(payload, indent=2)[:500]}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoint,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(
                        total=180
                    ),  # Increased timeout to 3 minutes
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Ollama response keys: {data.keys()}")
                        
                        content = data.get("message", {}).get("content", "")
                        if not content:
                            logger.warning(f"Empty content in Ollama response. Full response: {json.dumps(data)[:500]}")
                            return "{}"
                        
                        logger.info(f"Ollama content received, length: {len(content)}")
                        logger.debug(f"Ollama content preview: {content[:200]}")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Ollama API error: {response.status} - {error_text[:500]}"
                        )
                        return "{}"
        except asyncio.TimeoutError:
            logger.error(
                f"Ollama request timed out after 180 seconds for model {self.model}"
            )
            logger.info("Consider using a smaller model or increasing system resources")
            return "{}"
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Ollama API: {e}")
            return "{}"
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama API: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return "{}"

    def validate_connection(self) -> bool:
        """Test Ollama API connection"""
        import requests

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection validation failed: {e}")
            return False


class LocalAIProvider(LLMProvider):
    """LocalAI or other OpenAI-compatible local API provider"""

    def __init__(self, model: str, base_url: str, api_key: Optional[str] = None):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "dummy"  # Some local APIs require a dummy key
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)

    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request to LocalAI"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 1000),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LocalAI API: {e}")
            return "{}"

    def validate_connection(self) -> bool:
        """Test LocalAI API connection"""
        try:
            response = self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"LocalAI connection validation failed: {e}")
            return False


class LMStudioProvider(LLMProvider):
    """LM Studio local server provider"""

    def __init__(
        self, model: str = "local-model", base_url: str = "http://localhost:1234/v1"
    ):
        self.model = model
        self.base_url = base_url
        self.client = OpenAI(
            api_key="lm-studio", base_url=base_url  # LM Studio doesn't need a real key
        )

    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request to LM Studio"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 1000),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LM Studio API: {e}")
            return "{}"

    def validate_connection(self) -> bool:
        """Test LM Studio API connection"""
        import requests

        try:
            response = requests.get(f"{self.base_url}/models", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"LM Studio connection validation failed: {e}")
            return False


class VLLMProvider(LLMProvider):
    """vLLM high-performance inference server provider"""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "dummy"  # vLLM doesn't require API key by default
        # vLLM is OpenAI-compatible
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=f"{self.base_url}/v1",  # vLLM serves at /v1 endpoint
        )

    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Send chat completion request to vLLM"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 1000),
                # vLLM specific parameters
                top_p=kwargs.get("top_p", 0.95),
                frequency_penalty=kwargs.get("frequency_penalty", 0),
                presence_penalty=kwargs.get("presence_penalty", 0),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling vLLM API: {e}")
            return "{}"

    def validate_connection(self) -> bool:
        """Test vLLM API connection"""
        import requests

        try:
            # vLLM health check endpoint
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return True
            # Try models endpoint as fallback
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"vLLM connection validation failed: {e}")
            return False


class MockProvider(LLMProvider):
    """Mock LLM provider for testing when real providers are unavailable"""

    def __init__(self, model: str = "mock-model", base_url: str = "http://localhost"):
        self.model = model
        self.base_url = base_url
        logger.info("Using Mock LLM Provider - no real LLM calls will be made")

    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """Return mock response for testing"""
        # Return a mock response based on the last message
        last_message = messages[-1].get("content", "") if messages else ""

        # Return appropriate mock JSON for different analysis types
        if "market analysis" in last_message.lower():
            return json.dumps(
                {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "recommendation": "HOLD",
                    "reasoning": "Mock analysis - no real LLM available",
                }
            )
        elif "extract key insights" in last_message.lower():
            return json.dumps(
                {
                    "price_targets": ["Mock target: $50,000"],
                    "trends": ["Mock trend: Neutral market"],
                    "risks": ["Mock risk: Testing mode"],
                    "recommendations": ["Mock: No real analysis"],
                    "timeframes": ["Mock: N/A"],
                    "summary": "Mock document analysis - no real LLM available",
                }
            )
        else:
            return json.dumps(
                {
                    "result": "Mock response",
                    "message": "This is a mock response for testing",
                }
            )

    def validate_connection(self) -> bool:
        """Mock provider is always available"""
        return True


class LLMProviderFactory:
    """Factory class to create appropriate LLM provider based on configuration"""

    @staticmethod
    def create_provider(config: Dict) -> Optional[LLMProvider]:
        """
        Create LLM provider based on configuration

        Config format:
        {
            "provider": "openai|ollama|localai|lmstudio|vllm",
            "model": "model-name",
            "api_key": "optional-api-key",
            "base_url": "optional-base-url"
        }
        """
        provider_type = config.get("provider", "openai").lower()
        model = config.get("model", "gpt-4")

        try:
            if provider_type == "openai":
                api_key = config.get("api_key", os.getenv("OPENAI_API_KEY"))
                base_url = config.get("base_url")
                return OpenAIProvider(api_key, model, base_url)

            elif provider_type == "ollama":
                base_url = config.get("base_url", "http://localhost:11434")
                return OllamaProvider(model, base_url)

            elif provider_type == "localai":
                base_url = config.get("base_url", "http://localhost:8080/v1")
                api_key = config.get("api_key")
                return LocalAIProvider(model, base_url, api_key)

            elif provider_type == "lmstudio":
                base_url = config.get("base_url", "http://localhost:1234/v1")
                return LMStudioProvider(model, base_url)

            elif provider_type == "vllm":
                base_url = config.get("base_url", "http://localhost:8000")
                api_key = config.get("api_key")
                return VLLMProvider(model, base_url, api_key)

            elif provider_type == "mock":
                base_url = config.get("base_url", "http://localhost")
                return MockProvider(model, base_url)

            else:
                logger.error(f"Unknown LLM provider type: {provider_type}")
                return None

        except Exception as e:
            logger.error(f"Error creating LLM provider: {e}")
            return None

    @staticmethod
    def list_available_providers() -> List[str]:
        """List all available provider types"""
        return ["openai", "ollama", "localai", "lmstudio", "vllm", "mock"]

    @staticmethod
    def get_provider_info(provider_type: str) -> Dict:
        """Get information about a specific provider"""
        info = {
            "openai": {
                "name": "OpenAI",
                "description": "OpenAI API (GPT-4, GPT-3.5, etc.)",
                "requires_api_key": True,
                "default_base_url": "https://api.openai.com/v1",
                "example_models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"],
            },
            "ollama": {
                "name": "Ollama",
                "description": "Local LLM runner with various models",
                "requires_api_key": False,
                "default_base_url": "http://localhost:11434",
                "example_models": [
                    "llama2",
                    "mistral",
                    "codellama",
                    "neural-chat",
                    "starling-lm",
                ],
            },
            "localai": {
                "name": "LocalAI",
                "description": "OpenAI-compatible local API",
                "requires_api_key": False,
                "default_base_url": "http://localhost:8080/v1",
                "example_models": ["ggml-gpt4all-j", "ggml-koala", "gpt-3.5-turbo"],
            },
            "lmstudio": {
                "name": "LM Studio",
                "description": "Local LLM server with GUI",
                "requires_api_key": False,
                "default_base_url": "http://localhost:1234/v1",
                "example_models": ["local-model"],
            },
            "vllm": {
                "name": "vLLM",
                "description": "High-performance inference server with PagedAttention",
                "requires_api_key": False,
                "default_base_url": "http://localhost:8000",
                "example_models": [
                    "meta-llama/Llama-2-7b-chat-hf",
                    "mistralai/Mistral-7B-Instruct-v0.1",
                    "NousResearch/Meta-Llama-3-8B-Instruct",
                ],
            },
            "mock": {
                "name": "Mock Provider",
                "description": "Mock LLM provider for testing when real providers are unavailable",
                "requires_api_key": False,
                "default_base_url": "http://localhost",
                "example_models": ["mock-model"],
            },
        }
        return info.get(provider_type.lower(), {})
