#!/usr/bin/env python3
"""
Test script for LLM provider integration
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.llm_providers import LLMProviderFactory
from services.llm_analyzer import LLMAnalyzer
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

async def test_provider(provider_config):
    """Test a specific LLM provider"""
    print(f"\n{'='*50}")
    print(f"Testing {provider_config['provider'].upper()} Provider")
    print('='*50)
    
    # Create provider
    provider = LLMProviderFactory.create_provider(provider_config)
    
    if not provider:
        print(f"❌ Failed to create {provider_config['provider']} provider")
        return False
    
    # Test connection
    print(f"Testing connection to {provider_config.get('base_url', 'default URL')}...")
    is_connected = provider.validate_connection()
    
    if not is_connected:
        print(f"❌ Connection failed for {provider_config['provider']}")
        return False
    
    print(f"✅ Connected to {provider_config['provider']}")
    
    # Test chat completion
    print(f"\nTesting chat completion with model: {provider_config['model']}...")
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Be very brief."},
            {"role": "user", "content": "What is Bitcoin in one sentence?"}
        ]
        
        response = await provider.chat_completion(messages, temperature=0.3, max_tokens=100)
        print(f"✅ Response received: {response[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
        return False

async def test_analyzer():
    """Test the LLM Analyzer with market analysis"""
    print(f"\n{'='*50}")
    print("Testing LLM Analyzer Integration")
    print('='*50)
    
    # Get config from environment
    llm_config = {
        'provider': os.getenv('LLM_PROVIDER', 'ollama'),
        'model': os.getenv('LLM_MODEL', 'llama2'),
        'api_key': os.getenv('LLM_API_KEY', os.getenv('OPENAI_API_KEY', '')),
        'base_url': os.getenv('LLM_BASE_URL', 'http://localhost:11434')
    }
    
    print(f"Configuration: {json.dumps(llm_config, indent=2)}")
    
    # Create analyzer
    analyzer = LLMAnalyzer(llm_config)
    
    if not analyzer.provider:
        print("❌ LLM Analyzer initialization failed")
        return False
    
    print("✅ LLM Analyzer initialized")
    
    # Test market sentiment analysis
    print("\nTesting market sentiment analysis...")
    
    market_data = {
        'current_price': 45000,
        'volume_24h': 25000000000,
        'price_change_24h': 2.5
    }
    
    try:
        sentiment = await analyzer.analyze_market_sentiment([], market_data, [])
        
        print(f"\n📊 Market Sentiment Results:")
        print(f"  Score: {sentiment.score}")
        print(f"  Confidence: {sentiment.confidence}")
        print(f"  Recommendation: {sentiment.recommendation}")
        print(f"  Reasoning: {sentiment.reasoning[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Market analysis failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 LLM Provider Integration Test")
    print("="*50)
    
    # Test current configuration
    current_config = {
        'provider': os.getenv('LLM_PROVIDER', 'ollama'),
        'model': os.getenv('LLM_MODEL', 'llama2'),
        'api_key': os.getenv('LLM_API_KEY', ''),
        'base_url': os.getenv('LLM_BASE_URL', 'http://localhost:11434')
    }
    
    print(f"Current configuration from .env:")
    print(f"  Provider: {current_config['provider']}")
    print(f"  Model: {current_config['model']}")
    print(f"  Base URL: {current_config['base_url']}")
    
    # Test the configured provider
    provider_success = await test_provider(current_config)
    
    if provider_success:
        # Test the analyzer
        analyzer_success = await test_analyzer()
        
        if analyzer_success:
            print("\n✅ All tests passed! LLM integration is working.")
        else:
            print("\n⚠️ LLM Analyzer test failed.")
    else:
        print(f"\n❌ Provider test failed. Please check your {current_config['provider']} setup.")
        
        if current_config['provider'] == 'ollama':
            print("\nTo set up Ollama:")
            print("  ./setup-ollama.sh")
        elif current_config['provider'] == 'openai':
            print("\nMake sure you have set your OpenAI API key:")
            print("  export OPENAI_API_KEY='your-key-here'")

if __name__ == "__main__":
    asyncio.run(main())