import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core import ConnectionManager, get_settings
from api.routers import market_router, system_router, trading_router, websocket_router
from api.services import TradingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize global instances
settings = get_settings()
manager = ConnectionManager()
trading_system: TradingSystem


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Handle application lifecycle"""
    global trading_system

    # Startup
    logger.info("Starting up Trading Bot API")
    trading_system = TradingSystem(settings, manager)
    await trading_system.start()

    yield

    # Shutdown
    logger.info("Shutting down Trading Bot API")
    await trading_system.stop()


# Initialize FastAPI app
app = FastAPI(title="Trading Bot API", version="1.0.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system_router)
app.include_router(trading_router)
app.include_router(market_router)
app.include_router(websocket_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
