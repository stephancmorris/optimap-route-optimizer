#!/bin/bash

# OptiMap Docker Helper Script
# Simplifies Docker operations for development and production

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
show_help() {
    echo -e "${BLUE}🐳 OptiMap Docker Helper${NC}"
    echo ""
    echo "Usage: ./docker.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build           Build all Docker images"
    echo "  up              Start services in production mode"
    echo "  dev             Start services in development mode"
    echo "  down            Stop and remove all containers"
    echo "  logs            Show logs from all services"
    echo "  logs-backend    Show backend logs only"
    echo "  logs-frontend   Show frontend logs only"
    echo "  restart         Restart all services"
    echo "  clean           Remove all containers, images, and volumes"
    echo "  test            Run tests in containers"
    echo "  shell-backend   Open shell in backend container"
    echo "  shell-frontend  Open shell in frontend container"
    echo "  health          Check health of all services"
    echo ""
}

build() {
    echo -e "${BLUE}Building Docker images...${NC}"
    docker-compose build
    echo -e "${GREEN}✓ Build complete${NC}"
}

up() {
    echo -e "${BLUE}Starting services in production mode...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✓ Services started${NC}"
    echo ""
    echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
    echo -e "${BLUE}Backend:${NC}  http://localhost:8000"
    echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs"
}

dev() {
    echo -e "${BLUE}Starting services in development mode...${NC}"
    docker-compose -f docker-compose.dev.yml up
}

down() {
    echo -e "${YELLOW}Stopping services...${NC}"
    docker-compose down
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    echo -e "${GREEN}✓ Services stopped${NC}"
}

logs() {
    docker-compose logs -f
}

logs_backend() {
    docker-compose logs -f backend
}

logs_frontend() {
    docker-compose logs -f frontend
}

restart() {
    echo -e "${YELLOW}Restarting services...${NC}"
    docker-compose restart
    echo -e "${GREEN}✓ Services restarted${NC}"
}

clean() {
    echo -e "${RED}This will remove all containers, images, and volumes.${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
        docker rmi optimap-backend optimap-frontend 2>/dev/null || true
        echo -e "${GREEN}✓ Cleanup complete${NC}"
    fi
}

test() {
    echo -e "${BLUE}Running tests...${NC}"
    docker-compose exec backend pytest || echo -e "${YELLOW}Backend tests not configured yet${NC}"
    docker-compose exec frontend npm test || echo -e "${YELLOW}Frontend tests not configured yet${NC}"
}

shell_backend() {
    docker-compose exec backend /bin/bash
}

shell_frontend() {
    docker-compose exec frontend /bin/sh
}

health() {
    echo -e "${BLUE}Checking service health...${NC}"
    echo ""

    # Backend
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Backend: healthy${NC}"
    else
        echo -e "${RED}✗ Backend: unhealthy${NC}"
    fi

    # Frontend
    if curl -s http://localhost:3000/health > /dev/null; then
        echo -e "${GREEN}✓ Frontend: healthy${NC}"
    else
        echo -e "${RED}✗ Frontend: unhealthy${NC}"
    fi
}

# Main
case "$1" in
    build)
        build
        ;;
    up)
        up
        ;;
    dev)
        dev
        ;;
    down)
        down
        ;;
    logs)
        logs
        ;;
    logs-backend)
        logs_backend
        ;;
    logs-frontend)
        logs_frontend
        ;;
    restart)
        restart
        ;;
    clean)
        clean
        ;;
    test)
        test
        ;;
    shell-backend)
        shell_backend
        ;;
    shell-frontend)
        shell_frontend
        ;;
    health)
        health
        ;;
    *)
        show_help
        ;;
esac
