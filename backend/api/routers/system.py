import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    from api.main import trading_system

    return {
        "name": "Trading Bot API",
        "version": "1.0.0",
        "status": "running" if trading_system.is_running else "stopped",
    }


@router.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    from api.main import trading_system

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_running": trading_system.is_running,
    }


@router.post("/api/config")
async def update_config(config_update: Dict[str, Any]) -> Dict[str, Any]:
    """Update trading configuration"""
    try:
        from api.main import trading_system

        # Update configuration
        trading_system.settings.update_config(config_update)
        trading_system.trading_engine.config.update(config_update)

        # Restart system with new config
        await trading_system.stop()
        await trading_system.start()

        return {
            "status": "updated",
            "config": trading_system.settings.get_config_dict(),
        }

    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
