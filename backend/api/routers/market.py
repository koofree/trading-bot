import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["market"])
logger = logging.getLogger(__name__)


@router.get("/markets")
async def get_markets() -> Dict[str, List[Dict[str, Any]]]:
    """Get available markets"""
    try:
        from api.main import trading_system

        markets = trading_system.upbit.get_markets()
        # Filter KRW markets
        krw_markets = [m for m in markets if m["market"].startswith("KRW-")]
        return {"markets": krw_markets}

    except Exception as e:
        logger.error(f"Error getting markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/{market}/candles")
async def get_market_candles(
    market: str, interval: str = "minutes", unit: int = 60, count: int = 200
) -> Dict[str, Any]:
    """Get candle data for a specific market"""
    try:
        from api.main import trading_system

        candles = trading_system.upbit.get_candles(market, interval, unit, count)
        return {"market": market, "candles": candles}

    except Exception as e:
        logger.error(f"Error getting candles: {e}")
        raise HTTPException(status_code=500, detail=str(e))
