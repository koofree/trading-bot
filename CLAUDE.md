# Claude Code Context - Trading Bot Project

## 🚨 CRITICAL: Always Check Linting Before Completing Tasks

**Before marking ANY coding task as complete, you MUST run linting checks:**

### Frontend (TypeScript/React)
```bash
cd frontend
npm run validate  # Runs all checks: type-check, lint (Biome)
```

### Backend (Python/FastAPI)
```bash
cd backend
black .          # Format code
ruff check .     # Lint code
mypy .           # Type check
```

**If any errors are found, fix them before considering the task complete.**

## Project Structure

```
trading-bot/
├── frontend/          # TypeScript React application
│   ├── src/          # Source code
│   ├── public/       # Static assets
│   └── CLAUDE.md     # Frontend-specific context
├── backend/          # Python FastAPI application
│   ├── app/          # Application code
│   ├── tests/        # Test files
│   └── CLAUDE.md     # Backend-specific context
└── CLAUDE.md         # This file - project overview
```

## Technology Stack

### Frontend
- **Language**: TypeScript (NO JavaScript files)
- **Framework**: React 18
- **Styling**: Tailwind CSS (NO Material-UI)
- **Build**: Create React App (react-scripts v5)
- **Linting**: Biome (replaces ESLint + Prettier), TypeScript

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: SQLAlchemy + SQLite
- **Linting**: Black, Ruff, mypy
- **API**: RESTful + WebSocket

## Quick Commands

### Frontend Development
```bash
cd frontend
npm start         # Start development server
npm run build     # Build for production
npm run validate  # Run all checks
npm run lint:fix  # Auto-fix linting issues with Biome
npm run format    # Format code with Biome
```

### Backend Development
```bash
cd backend
uvicorn app.main:app --reload  # Start development server
black .                         # Format code
ruff check --fix .             # Fix linting issues
mypy .                         # Type check
```

## Key Rules and Conventions

### Universal Rules
1. **ALWAYS run linting before completing any task**
2. **Follow existing code patterns and conventions**
3. **Use type hints/types everywhere**
4. **Handle errors appropriately**
5. **Write clean, readable code**

### Frontend Specific
- TypeScript only - NO JavaScript files
- Tailwind CSS only - NO Material-UI
- Use React.ReactElement instead of JSX.Element
- Functional components with hooks
- Proper TypeScript types for all props and state

### Backend Specific
- Type hints for all functions
- Async/await for I/O operations
- Pydantic for data validation
- SQLAlchemy for database operations
- Proper error handling and logging

## Common Issues and Solutions

### Frontend
- **Biome errors**: Run `npm run lint:fix` to auto-fix
- **TypeScript errors**: Run `npm run type-check` to identify
- **Build failures**: Check `npm run validate` output

### Backend
- **Import errors**: Ensure proper module structure
- **Type errors**: Run `mypy .` to identify
- **Format issues**: Run `black .` to auto-fix

## Workflow Checklist

When working on any task:

- [ ] Read relevant CLAUDE.md files
- [ ] Understand the existing code structure
- [ ] Make changes following conventions
- [ ] Run linting/formatting tools
- [ ] Fix any errors or warnings
- [ ] Test the changes
- [ ] Verify linting passes
- [ ] Mark task as complete

## Important Files

- `/frontend/CLAUDE.md` - Detailed frontend context
- `/backend/CLAUDE.md` - Detailed backend context
- `/frontend/biome.json` - Biome configuration (linting + formatting)
- `/backend/pyproject.toml` - Python project & linting config

## Remember

The most important rule: **NEVER mark a task as complete without running and passing all linting checks.** This ensures code quality and consistency across the entire project.