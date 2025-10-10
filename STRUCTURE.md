# OptiMap Project Structure

## Overview

OptiMap follows a **decoupled microservices architecture** with separate backend (FastAPI/Python) and frontend (React/JavaScript) services.

```
optimap-route-optimizer/
├── backend/              # FastAPI backend service
├── frontend/             # React frontend application
├── docker-compose.yml    # Production Docker orchestration
├── docker-compose.dev.yml # Development Docker orchestration
├── requirements.txt      # Python dependencies
└── dev.sh               # Development startup script
```

## 📁 Directory Structure

### Root Level

```
/
├── .env.example          # Environment variable template
├── .gitignore           # Git ignore rules
├── LICENSE              # MIT License
├── README.md            # Main project documentation
├── STRUCTURE.md         # This file
├── DOCKER.md            # Docker deployment guide
├── requirements.txt     # Python dependencies (backend)
├── dev.sh              # Start both services in development
├── docker.sh           # Docker helper script
├── docker-compose.yml   # Production Docker setup
├── docker-compose.dev.yml # Development Docker setup
├── backend/            # Backend service directory
├── frontend/           # Frontend service directory
└── venv/               # Python virtual environment (gitignored)
```

### Backend Structure

```
backend/
├── Dockerfile           # Backend Docker image
├── .dockerignore       # Docker build exclusions
├── README.md           # Backend-specific documentation
├── CORS.md             # CORS configuration guide
├── ERROR_HANDLING.md   # Error handling guide
├── test_cors.sh        # CORS testing script
└── app/                # Main application package
    ├── __init__.py
    ├── main.py         # FastAPI application entry point
    ├── config/         # Configuration management
    │   ├── __init__.py
    │   └── settings.py # Environment-based settings
    ├── models/         # Pydantic data models
    │   ├── __init__.py
    │   ├── route.py    # Route optimization models
    │   └── errors.py   # Error response models
    ├── routers/        # API route handlers
    │   ├── __init__.py
    │   ├── health.py   # Health check endpoints
    │   └── optimize.py # Route optimization endpoints
    └── services/       # Business logic & external services
        ├── __init__.py
        ├── vrp_solver.py    # OR-Tools VRP solver
        └── osrm_client.py   # OSRM API client
```

#### Backend Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app initialization, middleware setup, route registration |
| `settings.py` | Environment variable configuration (OSRM URL, timeouts, CORS) |
| `route.py` | Request/response models for optimization API |
| `errors.py` | Structured error response models and error codes |
| `optimize.py` | Main optimization endpoint with validation and error handling |
| `vrp_solver.py` | Google OR-Tools wrapper for solving VRP/TSP |
| `osrm_client.py` | Async HTTP client for OSRM routing service |

### Frontend Structure

```
frontend/
├── Dockerfile          # Production build (multi-stage)
├── Dockerfile.dev      # Development image
├── .dockerignore      # Docker build exclusions
├── nginx.conf         # Nginx configuration for production
├── README.md          # Frontend documentation
├── package.json       # NPM dependencies & scripts
├── package-lock.json  # NPM lockfile
├── vite.config.js     # Vite bundler configuration
├── eslint.config.js   # ESLint configuration
├── .prettierrc        # Prettier configuration
├── .env.example       # Frontend environment template
├── index.html         # HTML entry point
├── public/            # Static assets
│   └── vite.svg
└── src/               # Source code
    ├── main.jsx       # React entry point
    ├── App.jsx        # Main application component
    ├── App.css        # Application styles
    ├── index.css      # Global styles
    ├── assets/        # Images, fonts, etc.
    │   └── react.svg
    ├── components/    # React components
    │   ├── StopInput.jsx         # Input form for adding stops
    │   ├── StopInput.css
    │   ├── StopList.jsx          # List of delivery stops
    │   ├── StopList.css
    │   ├── RouteMap.jsx          # Leaflet map component
    │   ├── RouteMap.css
    │   ├── MetricsDisplay.jsx    # Optimization results display
    │   └── MetricsDisplay.css
    └── services/      # API clients
        └── api.js     # Backend API communication
```

#### Frontend Key Files

| File | Purpose |
|------|---------|
| `App.jsx` | Main app component, state management, error handling |
| `StopInput.jsx` | Form for entering lat/lon/address of delivery stops |
| `StopList.jsx` | Display list of stops with delete functionality |
| `RouteMap.jsx` | Interactive Leaflet map showing stops and optimized route |
| `MetricsDisplay.jsx` | Display savings metrics (distance, time, %) |
| `api.js` | Fetch API wrapper for communicating with backend |
| `nginx.conf` | Production server config (gzip, caching, SPA routing) |

## 🔧 Configuration Files

### Environment Variables

**Root `.env`** (backend):
```bash
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
OSRM_BASE_URL=http://router.project-osrm.org
OSRM_TIMEOUT_SECONDS=30
SOLVER_TIME_LIMIT_SECONDS=30
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
```

**Frontend `.env`**:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Docker Files

- **`docker-compose.yml`**: Production setup with nginx, health checks, auto-restart
- **`docker-compose.dev.yml`**: Development with volume mounts and hot-reload
- **`backend/Dockerfile`**: Python 3.13-slim, multi-worker uvicorn
- **`frontend/Dockerfile`**: Multi-stage (Node build → Nginx serve)
- **`frontend/Dockerfile.dev`**: Vite dev server for development

## 📦 Dependencies

### Backend (Python)

Managed via `requirements.txt`:
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **pydantic-settings** - Environment variable management
- **httpx** - Async HTTP client
- **ortools** - Optimization solver
- **tenacity** - Retry logic
- **python-dotenv** - Environment file loading

### Frontend (JavaScript)

Managed via `package.json`:
- **react** - UI library
- **react-dom** - React rendering
- **leaflet** - Mapping library
- **react-leaflet** - React bindings for Leaflet
- **vite** - Build tool
- **eslint** - Linting
- **prettier** - Code formatting

## 🚀 Running the Project

### Development (Local)

```bash
# Start both services
./dev.sh

# Or manually:
# Backend
source venv/bin/activate
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Development (Docker)

```bash
./docker.sh dev
# OR
docker-compose -f docker-compose.dev.yml up
```

### Production (Docker)

```bash
./docker.sh up
# OR
docker-compose up -d
```

## 📡 API Endpoints

### Backend (`http://localhost:8000`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info and status |
| `/health` | GET | Health check |
| `/optimize` | POST | Optimize route for given stops |
| `/docs` | GET | Swagger UI documentation |
| `/redoc` | GET | ReDoc documentation |

### Frontend (`http://localhost:5173` dev, `http://localhost:3000` prod)

Single-page application (SPA) - all routes serve `index.html`

## 🗂️ Data Flow

```
User Input (Frontend)
    ↓
StopInput Component → Add stops to state
    ↓
StopList Component → Display stops, trigger optimization
    ↓
api.js → POST /optimize
    ↓
Backend optimize.py → Validate input
    ↓
OSRMClient → Get distance matrix
    ↓
ORToolsVRPSolver → Optimize route
    ↓
Return OptimizationResponse
    ↓
MetricsDisplay → Show savings
RouteMap → Visualize route
```

## 🧹 Ignored Files & Directories

### Git (.gitignore)

- Python: `venv/`, `__pycache__/`, `*.pyc`
- Node: `node_modules/`, `dist/`, `build/`
- Environment: `.env`, `.env.local`
- IDE: `.vscode/`, `.idea/`
- OS: `.DS_Store`, `Thumbs.db`
- Logs: `*.log`, `logs/`

### Docker (.dockerignore)

Backend:
- `venv/`, `__pycache__/`, `.env`, `.pytest_cache/`

Frontend:
- `node_modules/`, `dist/`, `.env.local`

## 🏗️ Architecture Principles

### Separation of Concerns
- **Backend**: Pure API, no UI logic
- **Frontend**: Pure UI, no business logic
- **Services**: Isolated external integrations (OSRM, OR-Tools)

### Configuration
- All config via environment variables
- Sensible defaults for development
- Production requires explicit configuration

### Error Handling
- Structured error responses
- Specific error codes for client handling
- Human-readable messages with suggestions

### Documentation
- README in each major directory
- Inline code documentation
- API documentation via FastAPI auto-generation

## 📚 Additional Documentation

- [README.md](README.md) - Main project overview
- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [backend/README.md](backend/README.md) - Backend setup and configuration
- [backend/CORS.md](backend/CORS.md) - CORS configuration guide
- [backend/ERROR_HANDLING.md](backend/ERROR_HANDLING.md) - Error handling reference
- [frontend/README.md](frontend/README.md) - Frontend setup and development

## 🔍 Code Quality

### Python (Backend)
- Type hints where applicable
- Docstrings for all public functions
- Pydantic models for validation
- Structured logging

### JavaScript (Frontend)
- ESLint for linting
- Prettier for formatting
- JSDoc comments for functions
- Component-based architecture

## 🧪 Testing

### Backend
```bash
# Run tests (when implemented)
pytest

# Test CORS
cd backend && ./test_cors.sh
```

### Frontend
```bash
cd frontend
npm test
npm run lint
```

## 📈 Scalability Considerations

### Backend
- Stateless design (horizontally scalable)
- Async I/O for OSRM calls
- Configurable worker count
- Request timeout controls

### Frontend
- Static build (CDN-ready)
- Code splitting (if implemented)
- Asset caching via nginx
- Lazy loading potential

## 🔐 Security

### Backend
- CORS with specific origins
- Input validation via Pydantic
- Request timeout limits
- No hardcoded secrets

### Frontend
- Environment-based API URL
- XSS protection via React
- HTTPS in production (via reverse proxy)

## 🎯 Future Structure Improvements

- [ ] Add `tests/` directories (backend and frontend)
- [ ] Add `docs/` directory for generated API docs
- [ ] Add `scripts/` for utility scripts
- [ ] Add CI/CD configuration (`.github/workflows/`)
- [ ] Add `logs/` with rotating log files
- [ ] Add database migrations if persistence added
