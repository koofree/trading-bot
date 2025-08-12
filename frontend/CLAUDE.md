# Claude Code Context

## Project Overview
This is a TypeScript React frontend for a trading bot application using:
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS (Material-UI has been completely removed)
- **State Management**: React Context API with WebSocket integration
- **Routing**: React Router v6
- **Charts**: Chart.js with react-chartjs-2
- **Build Tool**: Create React App (react-scripts v5)

## Important Requirements

### ✅ Always Run Linting Before Completing Tasks
**CRITICAL**: Before marking any coding task as complete, you MUST run the following commands:

```bash
# Run all validation checks
npm run validate

# Or run individually:
npm run type-check  # TypeScript type checking
npm run lint        # Biome linting and formatting check
```

If any errors are found, fix them before considering the task complete.

### Linting Commands Available
- `npm run lint` - Check for issues with Biome
- `npm run lint:fix` - Auto-fix issues with Biome
- `npm run format` - Format code with Biome
- `npm run format:check` - Check if code is formatted with Biome
- `npm run type-check` - Run TypeScript type checking
- `npm run validate` - Run all checks (type-check, lint)

## Technology Stack

### Frontend Dependencies
- React 18.2.0
- TypeScript 5.9.2
- Tailwind CSS 3.4.17
- React Router DOM 6.20.0
- Chart.js 4.4.0
- React Chart.js 2 5.2.0
- Axios 1.6.2
- React Use WebSocket 4.13.0
- Socket.io Client 4.5.4
- React Hot Toast 2.5.2

### Development Tools
- Biome 2.1.4 (all-in-one linter and formatter)
- TypeScript 5.9.2
- PostCSS & Autoprefixer for Tailwind

## Key Technical Decisions

### TypeScript Configuration
- Strict mode enabled
- JSX preserved for React 17+ transform
- Module resolution: bundler
- Target: ES2020

### Biome Configuration
- Single tool for linting and formatting
- Replaces ESLint and Prettier
- Fast performance with Rust-based engine
- TypeScript-aware linting rules

### Styling Approach
- **Tailwind CSS only** - No Material-UI components
- Custom SVG icons instead of icon libraries
- Responsive design with Tailwind utilities
- Custom animations defined in tailwind.config.js

## Common Issues and Solutions

### Biome Simplicity
**Benefit**: Single tool replaces ESLint + Prettier
**Performance**: Much faster than ESLint
**Configuration**: Simple biome.json file

### TypeScript JSX.Element Errors
**Problem**: JSX namespace not found
**Solution**: Use `React.ReactElement` instead of `JSX.Element` in type definitions

### npm Install Issues
**Problem**: Peer dependency conflicts
**Solution**: Use `--legacy-peer-deps` flag when installing packages

## Project Structure
```
frontend/
├── src/
│   ├── components/      # React components (all .tsx)
│   ├── contexts/        # React contexts (WebSocket)
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── types/          # TypeScript type definitions
│   ├── App.tsx         # Main app component
│   ├── index.tsx       # Entry point
│   └── index.css       # Tailwind imports
├── public/             # Static assets
├── .eslintrc.json      # ESLint configuration
├── .prettierrc.json    # Prettier configuration
├── tailwind.config.js  # Tailwind configuration
├── tsconfig.json       # TypeScript configuration
└── package.json        # Dependencies and scripts
```

## Development Workflow

1. **Before starting any task**: Review this document
2. **During development**: Use TypeScript strictly, no JavaScript files
3. **After making changes**: Run `npm run validate`
4. **Before completing task**: Ensure all linting passes
5. **If errors occur**: Fix them before marking task complete

## Backend Integration
- Backend API runs on `http://localhost:8000`
- WebSocket connection for real-time updates
- Proxy configured in package.json for development

## Remember
- NO JavaScript files - TypeScript only
- NO Material-UI - Tailwind CSS only
- ALWAYS run linting before finishing tasks
- Use existing patterns and conventions in the codebase