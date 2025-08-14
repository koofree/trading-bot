import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from .llm_providers import LLMProviderFactory

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
                "base_url": "http://localhost:11434",
            }

        self.llm_config = llm_config
        self.model = llm_config.get("model", "llama2")
        self.provider = LLMProviderFactory.create_provider(llm_config)

        if self.provider:
            is_connected = self.provider.validate_connection()
            if is_connected:
                logger.info(
                    f"LLM Provider initialized: {llm_config.get('provider')} with model {self.model}"
                )
            else:
                logger.warning(
                    f"LLM Provider connection failed: {llm_config.get('provider')}"
                )
                self.provider = None
        else:
            logger.warning("No LLM provider could be initialized")

        self.news_sources = [
            "https://cryptonews.com/",
            "https://www.coindesk.com/",
            "https://cointelegraph.com/",
        ]

    async def analyze_market_sentiment(
        self, news_data: List[Dict], market_data: Dict, uploaded_reports: List[str]
    ) -> MarketSentiment:
        """Comprehensive market analysis using LLM or rule-based fallback"""

        try:
            # Try LLM analysis first if provider is available
            if self.provider:
                # Prepare context from all sources
                context = await self._prepare_comprehensive_context(
                    news_data, market_data, uploaded_reports
                )

                prompt = self._create_analysis_prompt(context)
                response = await self._call_llm_async(prompt)
                sentiment = self._parse_sentiment_response(response)

                # Check if LLM gave meaningful results (not template values)
                if sentiment and sentiment.key_factors:
                    # Check if it's not just placeholder values
                    placeholder_factors = ["factor1", "factor2", "factor3"]
                    if not any(
                        factor in placeholder_factors
                        for factor in sentiment.key_factors[:3]
                    ):
                        logger.info("Using LLM-based sentiment analysis")
                        return sentiment

                logger.warning(
                    "LLM returned template values, falling back to rule-based analysis"
                )

            # Fallback to rule-based analysis
            logger.info("Using rule-based sentiment analysis")
            return self._create_rule_based_sentiment(market_data)

        except Exception as e:
            logger.error(f"Error in market sentiment analysis: {e}")
            # Try rule-based as last resort
            try:
                return self._create_rule_based_sentiment(market_data)
            except:
                return self._create_neutral_sentiment()

    async def _prepare_comprehensive_context(
        self, news_data: List[Dict], market_data: Dict, uploaded_reports: List[str]
    ) -> Dict:
        """Prepare comprehensive context for LLM analysis"""

        context = {
            "market_data": self._summarize_market_data(market_data),
            "news_summary": self._summarize_news(news_data),
            "report_insights": self._extract_report_insights(uploaded_reports),
            "timestamp": datetime.now().isoformat(),
        }

        return context

    def _summarize_market_data(self, market_data: Dict) -> Dict:
        """Summarize market data for LLM context"""
        if not market_data:
            return {}

        summary = {
            "price_change_24h": market_data.get("price_change_24h", 0),
            "volume_24h": market_data.get("volume_24h", 0),
            "high_24h": market_data.get("high_24h", 0),
            "low_24h": market_data.get("low_24h", 0),
            "current_price": market_data.get("current_price", 0),
            "market_cap": market_data.get("market_cap", 0),
        }

        # Add technical indicators if available
        if "indicators" in market_data:
            summary["technical_indicators"] = {
                "rsi": market_data["indicators"].get("rsi"),
                "macd": market_data["indicators"].get("macd"),
                "trend": market_data["indicators"].get("trend"),
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

        market_data = context.get("market_data", {})

        # Create actual analysis based on the data
        price_change = market_data.get("price_change_24h", 0)
        volume = market_data.get("volume_24h", 0)
        current_price = market_data.get("current_price", 0)

        # Create a simpler, more direct prompt for JSON output
        return f"""You are analyzing cryptocurrency market data. Based on the data below, provide your analysis.

Current price: ${current_price:.2f}
24h price change: {price_change:.2f}%
24h volume: ${volume:.2f}

NEWS: {context.get('news_summary', 'No recent news')[:100]}

Analyze this data and respond with ONLY a single JSON object (not an array).
Do not include the market data in your response.
Do not use markdown or code blocks.

Your response must be EXACTLY in this format (replace the placeholder values with your actual analysis):
{{
    "sentiment_score": -0.2,
    "confidence": 0.7,
    "key_factors": ["high volume indicates interest", "price stable", "no major news"],
    "risks": ["market volatility", "regulatory uncertainty"],
    "opportunities": ["potential breakout", "accumulation phase"],
    "recommendation": "HOLD",
    "reasoning": "Market shows stability with moderate volume, suggesting consolidation phase"
}}

JSON RESPONSE:"""

    async def _call_llm_async(self, prompt: str) -> str:
        """Call LLM API asynchronously using configured provider"""
        if not self.provider:
            logger.warning("LLM provider not initialized")
            return "{}"

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a cryptocurrency market analyst API. Analyze the provided market data and return your analysis as a JSON object. Important: 1) Output ONLY valid JSON, 2) Do not echo the input data, 3) Provide real analysis based on the data, not placeholder text, 4) Never use markdown formatting.",
                },
                {"role": "user", "content": prompt},
            ]

            logger.info(f"Calling LLM provider: {self.provider.__class__.__name__}")
            logger.debug(f"Prompt length: {len(prompt)} chars")

            response = await self.provider.chat_completion(
                messages=messages, temperature=0.7, max_tokens=1000
            )

            logger.info(
                f"LLM response received - Type: {type(response)}, Length: {len(str(response))}"
            )
            logger.debug(f"LLM response preview: {str(response)[:200]}")

            return response
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            logger.error(
                f"Provider: {self.provider.__class__.__name__ if self.provider else 'None'}"
            )
            raise

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Extract JSON from text that might contain extra content"""
        if not text:
            return None

        # Try different extraction methods
        extraction_methods = [
            # Method 1: Raw JSON parsing (handles both dict and array)
            lambda t: self._extract_dict_from_json(json.loads(t)),
            # Method 2: Find JSON between curly braces
            lambda t: json.loads(re.search(r"\{.*\}", t, re.DOTALL).group())
            if re.search(r"\{.*\}", t, re.DOTALL)
            else None,
            # Method 3: Remove common prefixes/suffixes
            lambda t: self._extract_dict_from_json(
                json.loads(
                    t.strip()
                    .removeprefix("```json")
                    .removeprefix("```")
                    .removesuffix("```")
                    .strip()
                )
            ),
            # Method 4: Find JSON after common phrases
            lambda t: self._extract_dict_from_json(
                json.loads(t.split("JSON:")[-1].strip())
            )
            if "JSON:" in t
            else None,
            lambda t: self._extract_dict_from_json(
                json.loads(t.split("json:")[-1].strip())
            )
            if "json:" in t
            else None,
            lambda t: self._extract_dict_from_json(
                json.loads(t.split("Output:")[-1].strip())
            )
            if "Output:" in t
            else None,
            # Method 5: Extract from markdown code block
            lambda t: json.loads(
                re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.DOTALL).group(1)
            )
            if re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.DOTALL)
            else None,
            # Method 6: Handle array with sentiment object
            lambda t: self._extract_dict_from_json(
                json.loads(re.search(r"\[.*\]", t, re.DOTALL).group())
            )
            if re.search(r"\[.*\]", t, re.DOTALL)
            else None,
        ]

        for method in extraction_methods:
            try:
                result = method(text)
                if result and isinstance(result, dict):
                    # Check if it has the expected sentiment keys
                    if any(
                        key in result
                        for key in ["sentiment_score", "confidence", "recommendation"]
                    ):
                        logger.debug(
                            f"Successfully extracted JSON using method: {method.__doc__ or 'lambda'}"
                        )
                        return result
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue

        return None

    def _extract_dict_from_json(self, json_data) -> Optional[Dict]:
        """Extract dictionary from JSON that might be an array or dict"""
        if isinstance(json_data, dict):
            return json_data
        elif isinstance(json_data, list):
            # Look for sentiment object in array
            for item in json_data:
                if isinstance(item, dict) and any(
                    key in item
                    for key in ["sentiment_score", "confidence", "recommendation"]
                ):
                    return item
            # If no sentiment object found, return the last dict in array
            for item in reversed(json_data):
                if isinstance(item, dict):
                    return item
        return None

    def _parse_sentiment_response(self, response: str) -> MarketSentiment:
        """Parse LLM response into MarketSentiment object"""
        try:
            # Check if response is empty or None
            if not response or response.strip() == "":
                logger.warning("Empty response from LLM")
                return self._create_neutral_sentiment()

            # Log the raw response for debugging
            logger.info(f"Raw LLM response (first 500 chars): {response[:500]}")
            logger.info(f"Response type: {type(response)}, Length: {len(response)}")

            # Try to extract JSON using our robust extraction method
            data = self._extract_json_from_text(response)

            if not data:
                logger.error(
                    f"Could not extract JSON from response: '{response[:500]}'"
                )
                return self._create_neutral_sentiment()

            logger.info(f"Successfully parsed JSON with keys: {data.keys()}")

            # Ensure we have the required fields with defaults
            return MarketSentiment(
                score=float(data.get("sentiment_score", 0)),
                confidence=float(data.get("confidence", 0.5)),
                key_factors=data.get("key_factors", ["Analysis unavailable"]),
                risks=data.get("risks", ["Unable to assess"]),
                opportunities=data.get("opportunities", ["Unable to identify"]),
                recommendation=data.get("recommendation", "HOLD"),
                reasoning=data.get("reasoning", "Automated analysis"),
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting values in parsed JSON: {e}")
            logger.error(f"Data was: {data if 'data' in locals() else 'Not parsed'}")
            return self._create_neutral_sentiment()
        except Exception as e:
            logger.error(f"Unexpected error parsing sentiment response: {e}")
            logger.error(f"Response was: '{response[:500] if response else 'None'}'")
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
            reasoning="Unable to perform analysis at this time",
        )

    def _create_rule_based_sentiment(self, market_data: Dict) -> MarketSentiment:
        """Create sentiment based on simple rules when LLM fails"""
        score = 0.0
        confidence = 0.5
        factors = []
        risks = []
        opportunities = []

        # Analyze price change
        price_change = market_data.get("price_change_24h", 0)
        if price_change > 5:
            score += 0.3
            factors.append(f"Strong price increase: {price_change:.1f}%")
            opportunities.append("Momentum trading opportunity")
            risks.append("Potential overbought conditions")
        elif price_change > 2:
            score += 0.1
            factors.append(f"Moderate price increase: {price_change:.1f}%")
        elif price_change < -5:
            score -= 0.3
            factors.append(f"Strong price decline: {price_change:.1f}%")
            risks.append("Continued selling pressure")
            opportunities.append("Potential bounce from oversold")
        elif price_change < -2:
            score -= 0.1
            factors.append(f"Moderate price decline: {price_change:.1f}%")
        else:
            factors.append(f"Stable price: {price_change:.1f}%")

        # Analyze volume
        volume = market_data.get("volume_24h", 0)
        if volume > 0:
            if (
                price_change > 0
                and volume > market_data.get("avg_volume", volume) * 1.5
            ):
                score += 0.2
                factors.append("High volume on price increase")
                confidence += 0.1
            elif (
                price_change < 0
                and volume > market_data.get("avg_volume", volume) * 1.5
            ):
                score -= 0.1
                factors.append("High volume on price decrease")
                risks.append("Strong selling volume")

        # Determine recommendation
        if score > 0.3:
            recommendation = "BUY"
            reasoning = f"Positive momentum with {price_change:.1f}% gain"
        elif score < -0.3:
            recommendation = "SELL"
            reasoning = f"Negative momentum with {price_change:.1f}% loss"
        else:
            recommendation = "HOLD"
            reasoning = f"Neutral market conditions with {price_change:.1f}% change"

        # Add default items if empty
        if not risks:
            risks = ["Market volatility", "Crypto regulatory risks"]
        if not opportunities:
            opportunities = ["Potential trend reversal", "Market stabilization"]

        return MarketSentiment(
            score=max(-1, min(1, score)),
            confidence=min(1, confidence),
            key_factors=factors if factors else ["Price action analysis"],
            risks=risks,
            opportunities=opportunities,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    async def analyze_uploaded_report(self, report_content: str) -> Dict:
        """Extract key insights from uploaded reports"""

        prompt = f"""Extract trading insights from this report and respond with ONLY JSON.

Report excerpt: {report_content[:2000]}

Output ONLY this JSON structure (no other text):
{{
    "price_targets": ["target1", "target2"],
    "trends": ["trend1", "trend2"],
    "risks": ["risk1", "risk2"],
    "recommendations": ["rec1", "rec2"],
    "timeframes": ["short-term", "long-term"],
    "summary": "Brief summary"
}}

JSON:"""

        if not self.provider:
            logger.warning("LLM provider not initialized")
            return {"error": "LLM provider not configured"}

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a JSON API. Output ONLY valid JSON with no additional text, explanations, or markdown formatting.",
                },
                {"role": "user", "content": prompt},
            ]

            content = await asyncio.to_thread(
                self.provider.chat_completion,
                messages=messages,
                temperature=0.2,
                max_tokens=800,
            )

            # Parse JSON response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            return {
                "summary": content,
                "price_targets": [],
                "trends": [],
                "risks": [],
                "recommendations": [],
                "timeframes": [],
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
            if isinstance(result, dict) and "error" not in result:
                valid_results.append(result)

        return valid_results

    async def _fetch_and_parse_url(
        self, session: aiohttp.ClientSession, url: str
    ) -> Dict:
        """Fetch and parse web content"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {"error": f"HTTP {response.status}", "url": url}

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Extract articles/content
                articles = self._extract_articles(soup, url)

                return {
                    "url": url,
                    "articles": articles,
                    "fetched_at": datetime.now().isoformat(),
                }

        except asyncio.TimeoutError:
            return {"error": "Timeout", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}

    def _extract_articles(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract article information from parsed HTML"""
        articles = []

        # Common article selectors
        article_selectors = ["article", ".article", ".post", ".news-item"]

        for selector in article_selectors:
            elements = soup.select(selector)[:5]  # Limit to 5 articles

            for element in elements:
                article = {}

                # Extract title
                title_elem = element.find(["h1", "h2", "h3", "h4"])
                if title_elem:
                    article["title"] = title_elem.get_text(strip=True)

                # Extract summary/content
                content_elem = element.find(["p", ".summary", ".excerpt"])
                if content_elem:
                    article["summary"] = content_elem.get_text(strip=True)[:200]

                # Extract link
                link_elem = element.find("a")
                if link_elem and link_elem.get("href"):
                    article["link"] = link_elem["href"]
                    if not article["link"].startswith("http"):
                        article["link"] = url + article["link"]

                if article:
                    articles.append(article)

        return articles

    async def analyze_price_action(self, candle_data: List[Dict]) -> Dict:
        """Analyze price action patterns using LLM"""

        # Prepare price action summary
        recent_candles = candle_data[-20:] if len(candle_data) > 20 else candle_data

        price_summary = {
            "recent_high": max(c["high"] for c in recent_candles),
            "recent_low": min(c["low"] for c in recent_candles),
            "avg_volume": sum(c["volume"] for c in recent_candles)
            / len(recent_candles),
            "price_changes": [c["close"] - c["open"] for c in recent_candles],
            "current_price": recent_candles[-1]["close"] if recent_candles else 0,
        }

        prompt = f"""Analyze price data and respond with ONLY JSON:

{json.dumps(price_summary, indent=2)[:500]}

Output ONLY this JSON (no explanations):
{{
    "patterns": ["pattern1", "pattern2"],
    "support_levels": [100, 200],
    "resistance_levels": [300, 400],
    "trend": "bullish/bearish/neutral",
    "volume_analysis": "increasing/decreasing/stable",
    "breakout_levels": [150, 250]
}}

JSON:"""

        response = await self._call_llm_async(prompt)

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"analysis": response}
        except:
            return {"analysis": response}
