import logging
import os
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["trading"])
logger = logging.getLogger(__name__)


@router.get("/signals")
async def get_signals(market: Optional[str] = None) -> Dict[str, Any]:
    """Get current trading signals"""
    try:
        from api.main import trading_system

        markets = [market] if market else None
        signals = trading_system.get_signals(markets)

        return {"signals": signals}

    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-trade")
async def execute_trade(trade_request: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a trading signal"""
    try:
        # Parse signal from request
        signal_data = trade_request.get("signal")

        if not signal_data:
            raise HTTPException(status_code=400, detail="Signal data required")

        # Execute trade
        # This would need proper signal parsing
        result = {"status": "not_implemented"}

        return result

    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions() -> Dict[str, Any]:
    """Get current positions"""
    try:
        from api.main import trading_system

        positions = [
            p.to_dict() for p in trading_system.trading_engine.positions.values()
        ]
        return {"positions": positions}

    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance() -> Dict[str, Any]:
    """Get performance metrics"""
    try:
        from api.main import trading_system

        metrics = trading_system.trading_engine.get_performance_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-report")
async def upload_report(file: UploadFile = File(...)) -> JSONResponse:
    """Handle report upload and processing"""
    try:
        from api.main import trading_system

        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename or "upload")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process document
        analysis = await trading_system.process_document(file_path)

        return JSONResponse(
            status_code=200, content={"status": "success", "analysis": analysis}
        )

    except Exception as e:
        logger.error(f"Error uploading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
async def run_backtest(backtest_request: Dict[str, Any]) -> Dict[str, Any]:
    """Run backtest on historical data"""
    # This would implement backtesting logic
    return {"status": "not_implemented"}


@router.get("/test-upbit")
async def test_upbit() -> Dict[str, Any]:
    """Test Upbit API connection and data"""
    try:
        from api.main import trading_system

        market = "KRW-BTC"  # Test with Bitcoin

        # Test getting candles
        candles = trading_system.upbit.get_candles(market, "minutes", 60, 10)

        result = {
            "market": market,
            "candles_count": len(candles) if candles else 0,
            "first_candle": candles[0] if candles else None,
            "columns": list(candles[0].keys()) if candles and len(candles) > 0 else [],
            "error": None,
        }

        # Try to get a signal
        if candles and len(candles) > 0:
            df = pd.DataFrame(candles)
            df = df.rename(
                columns={
                    "trade_price": "close",
                    "opening_price": "open",
                    "high_price": "high",
                    "low_price": "low",
                    "candle_acc_trade_volume": "volume",
                    "candle_date_time_kst": "timestamp",
                }
            )
            df["market"] = market

            # Check if we have enough data
            result["dataframe_shape"] = df.shape
            result["dataframe_columns"] = df.columns.tolist()
            result["has_required_columns"] = all(
                col in df.columns for col in ["close", "open", "high", "low", "volume"]
            )

        return result

    except Exception as e:
        logger.error(f"Error testing Upbit: {e}", exc_info=True)
        return {"error": str(e), "error_type": type(e).__name__}


@router.get("/test-llm")
async def test_llm() -> Dict[str, Any]:
    """Test LLM connection and response"""
    try:
        from api.main import trading_system

        # Test with a simple prompt
        test_prompt = """Bitcoin is currently at $50,000 with a 5% increase in 24 hours and high trading volume.

Based on this data, provide your market analysis as a JSON object.

Output ONLY this JSON structure with your actual analysis (not placeholder values):
{
    "sentiment_score": 0.3,
    "confidence": 0.6,
    "key_factors": ["5% daily gain shows bullish momentum", "high volume confirms trend", "psychological $50k level"],
    "risks": ["overbought conditions", "resistance at round number"],
    "opportunities": ["breakout potential", "trend continuation"],
    "recommendation": "BUY",
    "reasoning": "Positive momentum with strong volume support suggests continued upward movement"
}"""

        # Call the LLM directly
        llm_analyzer = trading_system.llm_analyzer
        response = await llm_analyzer._call_llm_async(test_prompt)

        # Try to parse the response
        parsed = llm_analyzer._parse_sentiment_response(response)

        return {
            "raw_response": response[:1000] if response else None,
            "parsed_sentiment": {
                "score": parsed.score,
                "confidence": parsed.confidence,
                "recommendation": parsed.recommendation,
                "reasoning": parsed.reasoning,
            },
            "llm_provider": llm_analyzer.provider.__class__.__name__
            if llm_analyzer.provider
            else "None",
            "llm_model": llm_analyzer.model,
        }

    except Exception as e:
        logger.error(f"Error testing LLM: {e}", exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "llm_configured": bool(
                trading_system.llm_analyzer.provider
                if hasattr(trading_system, "llm_analyzer")
                else False
            ),
        }
