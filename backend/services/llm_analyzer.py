from typing import List, Dict, Optional
import asyncio
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import json
import logging
import re
from dataclasses import dataclass
from .llm_providers import LLMProviderFactory, LLMProvider

logger = logging.getLogger(__name__)

@dataclass
class MarketSentiment:
    score: float  # -1 to 1
    confidence: float  # 0 to 1
    key_factors: List[str]
    risks: List[str]
    opportunities: List[str]
    recommendation: str
    reasoning: str

class LLMAnalyzer:
    def __init__(self, llm_config: Optional[Dict] = None):
        """
        Initialize LLM Analyzer with configurable provider
        
        llm_config format:
        {
            "provider": "openai|ollama|localai|lmstudio",
            "model": "model-name",
            "api_key": "optional-api-key",
            "base_url": "optional-base-url"
        }
        """
        # Default config if none provided
        if llm_config is None:
            llm_config = {
                "provider": "ollama",
                "model": "llama2",
                "base_url": "http://localhost:11434"
            }
        
        self.llm_config = llm_config
        self.model = llm_config.get('model', 'llama2')
        self.provider = LLMProviderFactory.create_provider(llm_config)
        
        if self.provider:
            is_connected = self.provider.validate_connection()
            if is_connected:
                logger.info(f"LLM Provider initialized: {llm_config.get('provider')} with model {self.model}")
            else:
                logger.warning(f"LLM Provider connection failed: {llm_config.get('provider')}")
                self.provider = None
        else:
            logger.warning("No LLM provider could be initialized")
        
        self.news_sources = [
            "https://cryptonews.com/",
            "https://www.coindesk.com/",
            "https://cointelegraph.com/"
        ]
        
    async def analyze_market_sentiment(self, 
                                      news_data: List[Dict],
                                      market_data: Dict,
                                      uploaded_reports: List[str]) -> MarketSentiment:
        """Comprehensive market analysis using LLM"""
        
        try:
            # Prepare context from all sources
            context = await self._prepare_comprehensive_context(
                news_data, market_data, uploaded_reports
            )
            
            prompt = self._create_analysis_prompt(context)
            
            response = await self._call_llm_async(prompt)
            sentiment = self._parse_sentiment_response(response)
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error in market sentiment analysis: {e}")
            return self._create_neutral_sentiment()
    
    async def _prepare_comprehensive_context(self, 
                                           news_data: List[Dict],
                                           market_data: Dict,
                                           uploaded_reports: List[str]) -> Dict:
        """Prepare comprehensive context for LLM analysis"""
        
        context = {
            'market_data': self._summarize_market_data(market_data),
            'news_summary': self._summarize_news(news_data),
            'report_insights': self._extract_report_insights(uploaded_reports),
            'timestamp': datetime.now().isoformat()
        }
        
        return context
    
    def _summarize_market_data(self, market_data: Dict) -> Dict:
        """Summarize market data for LLM context"""
        if not market_data:
            return {}
            
        summary = {
            'price_change_24h': market_data.get('price_change_24h', 0),
            'volume_24h': market_data.get('volume_24h', 0),
            'high_24h': market_data.get('high_24h', 0),
            'low_24h': market_data.get('low_24h', 0),
            'current_price': market_data.get('current_price', 0),
            'market_cap': market_data.get('market_cap', 0)
        }
        
        # Add technical indicators if available
        if 'indicators' in market_data:
            summary['technical_indicators'] = {
                'rsi': market_data['indicators'].get('rsi'),
                'macd': market_data['indicators'].get('macd'),
                'trend': market_data['indicators'].get('trend')
            }
            
        return summary
    
    def _summarize_news(self, news_data: List[Dict]) -> str:
        """Summarize news articles for context"""
        if not news_data:
            return "No recent news available."
            
        summaries = []
        for article in news_data[:5]:  # Limit to 5 most recent
            summary = f"- {article.get('title', '')}: {article.get('summary', '')}"
            summaries.append(summary)
            
        return "\n".join(summaries)
    
    def _extract_report_insights(self, reports: List[str]) -> str:
        """Extract key insights from uploaded reports"""
        if not reports:
            return "No reports uploaded."
            
        insights = []
        for report in reports[:3]:  # Limit to 3 reports
            # Extract first 500 characters as preview
            preview = report[:500] if len(report) > 500 else report
            insights.append(preview)
            
        return "\n---\n".join(insights)
    
    def _create_analysis_prompt(self, context: Dict) -> str:
        """Create a structured prompt for LLM analysis"""
        
        return f"""You are a professional cryptocurrency market analyst. Analyze the following market data and provide trading insights.

MARKET DATA:
{json.dumps(context['market_data'], indent=2)}

RECENT NEWS:
{context['news_summary']}

ANALYST REPORTS:
{context['report_insights']}

Please provide a comprehensive analysis with the following structure:

1. Overall Market Sentiment Score: (provide a number from -1.0 to 1.0 where -1 is extremely bearish, 0 is neutral, 1 is extremely bullish)

2. Confidence Level: (provide a number from 0.0 to 1.0 indicating confidence in your analysis)

3. Key Factors: (list 3-5 key factors currently affecting the market)

4. Risks: (list 3-5 potential risks to consider)

5. Opportunities: (list 3-5 potential opportunities)

6. Trading Recommendation: (BUY/SELL/HOLD with specific entry/exit points if applicable)

7. Reasoning: (provide a detailed explanation of your analysis in 2-3 sentences)

Format your response as valid JSON with these exact keys: sentiment_score, confidence, key_factors, risks, opportunities, recommendation, reasoning"""
    
    async def _call_llm_async(self, prompt: str) -> str:
        """Call LLM API asynchronously using configured provider"""
        if not self.provider:
            logger.warning("LLM provider not initialized")
            return "{}"
            
        try:
            messages = [
                {"role": "system", "content": "You are a cryptocurrency market analyst with expertise in technical and fundamental analysis."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.provider.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            return response
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
    
    def _parse_sentiment_response(self, response: str) -> MarketSentiment:
        """Parse LLM response into MarketSentiment object"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            return MarketSentiment(
                score=float(data.get('sentiment_score', 0)),
                confidence=float(data.get('confidence', 0.5)),
                key_factors=data.get('key_factors', []),
                risks=data.get('risks', []),
                opportunities=data.get('opportunities', []),
                recommendation=data.get('recommendation', 'HOLD'),
                reasoning=data.get('reasoning', '')
            )
        except Exception as e:
            logger.error(f"Error parsing sentiment response: {e}")
            return self._create_neutral_sentiment()
    
    def _create_neutral_sentiment(self) -> MarketSentiment:
        """Create a neutral sentiment when analysis fails"""
        return MarketSentiment(
            score=0,
            confidence=0,
            key_factors=["Analysis unavailable"],
            risks=["Unable to assess risks"],
            opportunities=["Unable to identify opportunities"],
            recommendation="HOLD",
            reasoning="Unable to perform analysis at this time"
        )
    
    async def analyze_uploaded_report(self, report_content: str) -> Dict:
        """Extract key insights from uploaded reports"""
        
        prompt = f"""Extract key trading insights from the following report. Focus on:
1. Price predictions or targets
2. Market trends and patterns
3. Risk factors and warnings
4. Specific trading recommendations
5. Time horizons for predictions

Report content:
{report_content[:3000]}  # Limit to 3000 chars

Provide response as JSON with keys: price_targets, trends, risks, recommendations, timeframes, summary"""
        
        if not self.provider:
            logger.warning("LLM provider not initialized")
            return {"error": "LLM provider not configured"}
            
        try:
            messages = [
                {"role": "system", "content": "You are a financial analyst extracting key insights from market reports."},
                {"role": "user", "content": prompt}
            ]
            
            content = await asyncio.to_thread(
                self.provider.chat_completion,
                messages=messages,
                temperature=0.2,
                max_tokens=800
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {
                "summary": content,
                "price_targets": [],
                "trends": [],
                "risks": [],
                "recommendations": [],
                "timeframes": []
            }
            
        except Exception as e:
            logger.error(f"Error analyzing report: {e}")
            return {"error": str(e)}
    
    async def fetch_web_data(self, sources: Optional[List[str]] = None) -> List[Dict]:
        """Fetch and analyze web data from news sources"""
        
        sources = sources or self.news_sources
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_and_parse_url(session, url) for url in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Filter out errors
        valid_results = []
        for result in results:
            if isinstance(result, dict) and 'error' not in result:
                valid_results.append(result)
                
        return valid_results
    
    async def _fetch_and_parse_url(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Fetch and parse web content"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}", "url": url}
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract articles/content
                articles = self._extract_articles(soup, url)
                
                return {
                    "url": url,
                    "articles": articles,
                    "fetched_at": datetime.now().isoformat()
                }
                
        except asyncio.TimeoutError:
            return {"error": "Timeout", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def _extract_articles(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract article information from parsed HTML"""
        articles = []
        
        # Common article selectors
        article_selectors = ['article', '.article', '.post', '.news-item']
        
        for selector in article_selectors:
            elements = soup.select(selector)[:5]  # Limit to 5 articles
            
            for element in elements:
                article = {}
                
                # Extract title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                if title_elem:
                    article['title'] = title_elem.get_text(strip=True)
                
                # Extract summary/content
                content_elem = element.find(['p', '.summary', '.excerpt'])
                if content_elem:
                    article['summary'] = content_elem.get_text(strip=True)[:200]
                
                # Extract link
                link_elem = element.find('a')
                if link_elem and link_elem.get('href'):
                    article['link'] = link_elem['href']
                    if not article['link'].startswith('http'):
                        article['link'] = url + article['link']
                
                if article:
                    articles.append(article)
        
        return articles
    
    async def analyze_price_action(self, candle_data: List[Dict]) -> Dict:
        """Analyze price action patterns using LLM"""
        
        # Prepare price action summary
        recent_candles = candle_data[-20:] if len(candle_data) > 20 else candle_data
        
        price_summary = {
            'recent_high': max(c['high'] for c in recent_candles),
            'recent_low': min(c['low'] for c in recent_candles),
            'avg_volume': sum(c['volume'] for c in recent_candles) / len(recent_candles),
            'price_changes': [c['close'] - c['open'] for c in recent_candles],
            'current_price': recent_candles[-1]['close'] if recent_candles else 0
        }
        
        prompt = f"""Analyze the following price action data and identify patterns:

Price Summary:
{json.dumps(price_summary, indent=2)}

Identify:
1. Chart patterns (head and shoulders, triangles, flags, etc.)
2. Support and resistance levels
3. Trend direction and strength
4. Volume patterns
5. Potential breakout levels

Provide response as JSON with keys: patterns, support_levels, resistance_levels, trend, volume_analysis, breakout_levels"""
        
        response = await self._call_llm_async(prompt)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"analysis": response}
        except:
            return {"analysis": response}