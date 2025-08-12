# Claude Code Context - Backend

## Project Overview
This is a Python FastAPI backend for a trading bot application using:
- **Framework**: FastAPI
- **Database**: SQLAlchemy with SQLite
- **WebSocket**: For real-time updates
- **Exchange API**: Upbit integration
- **LLM Integration**: Multiple providers (OpenAI, Anthropic, Ollama, LMStudio, vLLM)

## Important Requirements

### ✅ Always Run Linting Before Completing Tasks
**CRITICAL**: Before marking any coding task as complete, you MUST run the following commands:

```bash
# Format code with Black
black .

# Check with Ruff linter
ruff check .
ruff check --fix .  # Auto-fix issues

# Type checking with mypy
mypy .
```

If any errors are found, fix them before considering the task complete.

## Linting Configuration

### Black (Code Formatter)
- Line length: 88 characters
- Python 3.11 target
- Configured in `pyproject.toml`

### Ruff (Linter)
- Extensive rule sets enabled
- Line length: 88 characters
- Python 3.11 target
- Auto-fixes available for many issues

### mypy (Type Checker)
- Strict mode enabled
- Ignore missing imports
- Disallow untyped definitions

## Project Structure
```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # FastAPI application
├── tests/             # Test files
├── alembic/          # Database migrations
├── pyproject.toml    # Project configuration & linting
├── requirements.txt  # Python dependencies
└── .env             # Environment variables
```

## Key Services

### Exchange Service
- Upbit API integration
- Market data fetching
- Order execution
- Balance management

### Signal Service
- Trading signal generation
- Technical analysis
- Market analysis

### LLM Service
- Multiple provider support
- Market analysis using AI
- Signal reasoning generation

### WebSocket Manager
- Real-time data broadcasting
- Client connection management
- Market updates and signals

## Database Models
- Markets
- Signals
- Positions
- Orders
- Performance metrics

## Development Workflow

1. **Before starting any task**: Review this document
2. **During development**: Use type hints for all functions
3. **After making changes**: Run linting tools
4. **Before completing task**: Ensure all linting passes
5. **If errors occur**: Fix them before marking task complete

## API Endpoints

### Core Endpoints
- `/api/markets` - Market data
- `/api/signals` - Trading signals
- `/api/positions` - Position management
- `/api/performance` - Performance metrics
- `/api/config` - Configuration management
- `/ws` - WebSocket connection

## Environment Variables
Required in `.env`:
- `DATABASE_URL` - Database connection string
- `UPBIT_ACCESS_KEY` - Upbit API access key
- `UPBIT_SECRET_KEY` - Upbit API secret key
- `LLM_API_KEY` - LLM provider API key
- `LLM_PROVIDER` - LLM provider selection

## Remember
- ALWAYS use type hints
- ALWAYS run linting before finishing tasks
- Follow FastAPI best practices
- Use async/await for I/O operations
- Handle errors appropriately
- Log important operations