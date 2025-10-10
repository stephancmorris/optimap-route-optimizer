# OptiMap Backend - Route Optimization Service

FastAPI-based microservice for Vehicle Routing Problem (VRP) optimization using Google OR-Tools.

## 🔧 Technology Stack

- **FastAPI** 0.115.0 - Modern Python web framework
- **Google OR-Tools** 9.14.6206 - Optimization solver library
- **Uvicorn** 0.32.0 - ASGI server
- **Pydantic** 2.9.2 - Data validation
- **httpx** 0.27.2 - Async HTTP client for OSRM integration

## 📋 Prerequisites

- **Python 3.8+** (tested with Python 3.13.2)
- Virtual environment (venv)

## 🚀 Setup Instructions

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root (use `.env.example` as template):

```bash
cp .env.example .env
```

### 4. Run Development Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Environment configuration
│   ├── models/
│   │   └── __init__.py         # Pydantic data models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py           # Health check endpoints
│   └── services/
│       ├── __init__.py
│       └── vrp_solver.py       # OR-Tools VRP solver wrapper
└── README.md
```

## 🔍 OR-Tools Configuration

### Version Constraints

- **OR-Tools Version**: 9.14.6206
- **Python Compatibility**: Python 3.8 - 3.13
- **Solver Algorithm**: Constraint Programming (CP-SAT)
- **VRP Strategy**: PATH_CHEAPEST_ARC (First Solution Strategy)

### Dependencies

OR-Tools automatically installs these sub-dependencies:
- `absl-py>=2.0.0` - Abseil Python library
- `numpy>=1.13.3` - Numerical computing
- `pandas>=2.0.0` - Data manipulation
- `protobuf<6.32,>=6.31.1` - Protocol buffers
- `immutabledict>=3.0.0` - Immutable dictionary implementation

### Solver Configuration

Default solver settings (configurable via environment variables):

- **Time Limit**: 30 seconds (`SOLVER_TIME_LIMIT_SECONDS`)
- **Search Strategy**: Path Cheapest Arc
- **Vehicles**: 1 (TSP mode)

## 🧪 Testing OR-Tools Installation

Test the VRP solver installation:

```bash
cd backend
python3 -c "from app.services.vrp_solver import get_solver_info; import json; print(json.dumps(get_solver_info(), indent=2))"
```

Expected output:
```json
{
  "library": "Google OR-Tools",
  "version": "9.14.6206",
  "solver_type": "Constraint Programming (CP-SAT)",
  "algorithm": "Vehicle Routing Problem (VRP)",
  "python_compatible": true
}
```

## 📡 API Endpoints

### Health Check
```
GET /health
```

Returns service health status and timestamp.

### Root
```
GET /
```

Returns API information and documentation links.

## 🔒 Environment Variables

See [.env.example](../.env.example) for full configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_HOST` | Server host address | `0.0.0.0` |
| `BACKEND_PORT` | Server port | `8000` |
| `OSRM_BASE_URL` | OSRM routing API URL | `http://router.project-osrm.org` |
| `SOLVER_TIME_LIMIT_SECONDS` | OR-Tools solver timeout | `30` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000,http://localhost:5173` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🔐 CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured to allow the frontend to communicate with the backend.

**Quick reference:**
- Configure allowed origins via `ALLOWED_ORIGINS` environment variable
- Default: `http://localhost:3000,http://localhost:5173`
- Production: Set to your actual domain(s), never use `"*"`

**Test CORS:**
```bash
./test_cors.sh
```

📖 **See [CORS.md](CORS.md) for detailed CORS configuration guide**

## 📚 Additional Resources

- [Google OR-Tools Documentation](https://developers.google.com/optimization)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Vehicle Routing Problem Guide](https://developers.google.com/optimization/routing)
- [CORS Configuration Guide](CORS.md)
