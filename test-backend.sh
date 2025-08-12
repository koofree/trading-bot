#!/bin/bash

echo "Testing Backend API Endpoints"
echo "=============================="

# Wait for backend to be ready
sleep 2

# Test root endpoint
echo ""
echo "1. Testing root endpoint:"
curl -s http://localhost:8000 | python3 -m json.tool

# Test API docs
echo ""
echo "2. Testing API documentation:"
curl -s -o /dev/null -w "API Docs: %{http_code}\n" http://localhost:8000/docs

# Test health endpoint
echo ""
echo "3. Testing health endpoint:"
curl -s http://localhost:8000/health | python3 -m json.tool

# Test trading status
echo ""
echo "4. Testing trading status:"
curl -s http://localhost:8000/api/trading/status | python3 -m json.tool

echo ""
echo "✅ Backend API tests complete!"