# 🐳 Docker Deployment Guide

This guide covers running OptiMap using Docker and Docker Compose.

## Prerequisites

- **Docker** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ (included with Docker Desktop)

## Quick Start

### Production Mode

Start both frontend and backend services:

```bash
docker-compose up -d
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Stop services:

```bash
docker-compose down
```

### Development Mode

For development with hot-reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

This runs:
- Backend with `--reload` flag (auto-restart on code changes)
- Frontend with Vite dev server (HMR enabled)

## Building Images

### Build Backend Only

```bash
docker build -f backend/Dockerfile -t optimap-backend:latest .
```

### Build Frontend Only

```bash
docker build -f frontend/Dockerfile -t optimap-frontend:latest ./frontend
```

### Build All Services

```bash
docker-compose build
```

## Running Individual Services

### Backend Only

```bash
docker run -p 8000:8000 \
  -e OSRM_BASE_URL=http://router.project-osrm.org \
  -e ALLOWED_ORIGINS=http://localhost:3000 \
  optimap-backend:latest
```

### Frontend Only

```bash
docker run -p 3000:3000 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  optimap-frontend:latest
```

## Environment Variables

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_HOST` | Server bind address | `0.0.0.0` |
| `BACKEND_PORT` | Server port | `8000` |
| `OSRM_BASE_URL` | OSRM routing service URL | `http://router.project-osrm.org` |
| `SOLVER_TIME_LIMIT_SECONDS` | OR-Tools timeout | `30` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000,http://localhost:5173` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

You can set these in a `.env` file in the project root:

```bash
# .env
OSRM_BASE_URL=http://router.project-osrm.org
SOLVER_TIME_LIMIT_SECONDS=30
LOG_LEVEL=INFO
```

## Docker Compose Configuration

### Production (`docker-compose.yml`)

Features:
- Optimized production builds
- Multi-worker backend (4 uvicorn workers)
- Nginx serving frontend static files
- Health checks for both services
- Auto-restart on failure

### Development (`docker-compose.dev.yml`)

Features:
- Hot-reload for backend and frontend
- Volume mounts for live code changes
- Debug logging enabled
- Single worker for easier debugging

## Health Checks

Both services include health checks:

**Backend:**
```bash
curl http://localhost:8000/health
```

**Frontend:**
```bash
curl http://localhost:3000/health
```

Docker will automatically restart unhealthy containers.

## Troubleshooting

### Port Already in Use

If ports 3000 or 8000 are already in use, modify `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Use 8080 instead of 8000
  frontend:
    ports:
      - "3001:3000"  # Use 3001 instead of 3000
```

### Container Logs

View logs:

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Rebuild After Code Changes

If changes aren't reflecting (production mode):

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Network Issues

If services can't communicate:

```bash
# Inspect network
docker network inspect optimap-network

# Restart with fresh network
docker-compose down
docker network prune
docker-compose up -d
```

## Production Deployment

### Security Considerations

1. **Update CORS origins** in production:
   ```yaml
   environment:
     - ALLOWED_ORIGINS=https://yourdomain.com
   ```

2. **Use secrets** for sensitive data:
   ```yaml
   secrets:
     - db_password
   ```

3. **Enable HTTPS** with reverse proxy (nginx/traefik)

4. **Limit resources**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

### Recommended Production Stack

```
Client → Load Balancer/CDN → Frontend Container
                          ↓
                    Backend Container → OSRM Service
```

## Advanced Configuration

### Custom Nginx Configuration

Edit `frontend/nginx.conf` to customize:
- Caching policies
- Security headers
- Gzip compression
- Rate limiting

### Multi-Worker Backend

Adjust workers in `backend/Dockerfile`:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

Rule of thumb: `workers = (2 × CPU cores) + 1`

### Volume Mounts

For persistent data or shared configs:

```yaml
volumes:
  - ./config:/app/config:ro
  - optimap-data:/app/data
```

## Testing Docker Setup

Run tests inside containers:

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test
```

## Cleanup

Remove all containers, networks, and images:

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi optimap-backend optimap-frontend

# Remove volumes (if any)
docker volume prune

# Full cleanup
docker system prune -a
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build images
        run: docker-compose build
      - name: Run tests
        run: docker-compose up -d && docker-compose exec backend pytest
```

## Support

For issues related to Docker deployment, check:
- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Project Issues](https://github.com/yourusername/optimap/issues)
