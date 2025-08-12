#!/bin/bash

echo "⚛️  Starting Frontend Development Server"
echo "======================================="

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "🌐 Starting React development server with hot reload on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the React development server
BROWSER=none npm start