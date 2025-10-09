#!/bin/bash

# OptiMap Development Script
# Runs both backend and frontend servers concurrently

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗺️  OptiMap Development Environment${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Check if backend dependencies are installed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo -e "${YELLOW}⚠️  Installing backend dependencies...${NC}"
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    source venv/bin/activate
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Installing frontend dependencies...${NC}"
    cd frontend
    npm install --cache /tmp/npm-cache
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

# Check if .env files exist
if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}⚠️  Creating frontend .env from example...${NC}"
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}✓ Frontend .env created${NC}"
fi

echo ""
echo -e "${GREEN}Starting development servers...${NC}"
echo ""
echo -e "${BLUE}📡 Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}🌐 Frontend:${NC} http://localhost:5173"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    echo -e "${GREEN}✓ All servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Give backend a moment to start
sleep 2

# Start frontend server
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
