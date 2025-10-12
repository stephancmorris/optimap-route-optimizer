# Testing API Documentation - OptiMap

This guide provides step-by-step instructions for testing and verifying the API documentation implementation.

## Prerequisites

Before testing, ensure you have:
- Docker and Docker Compose installed
- Backend and OSRM services running
- Internet connection (for OSRM if using public instance)

## Starting the Services

### Option 1: Using Docker Compose (Recommended)

```bash
# From the project root directory
docker compose up --build
```

This will start:
- Backend API on http://localhost:8000
- Frontend on http://localhost:3000
- OSRM router service

### Option 2: Running Backend Standalone

```bash
# From the backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn ortools httpx python-dotenv

# Set environment variables
export OSRM_BASE_URL="http://router.project-osrm.org"
export ALLOWED_ORIGINS="http://localhost:3000"

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verifying Documentation Endpoints

### 1. Check Root Endpoint

**URL:** http://localhost:8000/

**Expected Response:**
```json
{
  "name": "OptiMap Route Optimizer API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc",
  "openapi": "/openapi.json",
  "status": "operational"
}
```

**Test with cURL:**
```bash
curl http://localhost:8000/
```

### 2. Access Swagger UI Documentation

**URL:** http://localhost:8000/docs

**What to Verify:**
- [ ] Page loads successfully
- [ ] API title shows "OptiMap Route Optimizer API"
- [ ] API description with features and workflow is visible
- [ ] Three endpoint groups are visible:
  - Root (GET /)
  - Health (GET /health)
  - Optimization (POST /optimize)
- [ ] Each endpoint shows detailed descriptions
- [ ] Request/response examples are present
- [ ] Error response examples (400, 500, 503) are documented
- [ ] "Try it out" functionality works

**Manual Test Steps:**
1. Open http://localhost:8000/docs in your browser
2. Click on "GET /" endpoint to expand it
3. Verify the description and example response
4. Click "Try it out" → "Execute"
5. Verify the response matches the documented example
6. Repeat for GET /health endpoint
7. For POST /optimize:
   - Expand the endpoint
   - Review the comprehensive description
   - Check request body schema
   - Check response examples (200, 400, 500, 503)
   - Click "Try it out"
   - Use the example request body
   - Click "Execute"
   - Verify optimization works and returns expected format

### 3. Access ReDoc Documentation

**URL:** http://localhost:8000/redoc

**What to Verify:**
- [ ] Page loads successfully with clean, professional design
- [ ] Left sidebar shows all endpoints
- [ ] API description is displayed at the top
- [ ] Contact and license information is visible
- [ ] Each endpoint shows:
  - Summary and description
  - Request parameters with types
  - Response schemas
  - Error responses
- [ ] Examples are properly formatted and readable
- [ ] Navigation between endpoints works smoothly

**Manual Test Steps:**
1. Open http://localhost:8000/redoc in your browser
2. Scroll through the documentation
3. Verify all sections are present and formatted correctly
4. Click on different endpoints in the sidebar
5. Verify smooth navigation

### 4. Check OpenAPI Schema

**URL:** http://localhost:8000/openapi.json

**What to Verify:**
- [ ] Returns valid JSON
- [ ] Contains OpenAPI version 3.x
- [ ] Has API info (title, description, version, contact, license)
- [ ] Contains all endpoint paths (/, /health, /optimize)
- [ ] Each endpoint has complete schema definition
- [ ] Request/response models are defined in components/schemas
- [ ] Error response schemas are included

**Test with cURL:**
```bash
curl http://localhost:8000/openapi.json | python3 -m json.tool
```

Or view in browser:
```bash
# Pretty print the schema
curl -s http://localhost:8000/openapi.json | python3 -m json.tool | less
```

## Testing API Endpoints

### Test 1: Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "OptiMap Backend",
  "timestamp": "2025-10-12T15:30:45.123456"
}
```

### Test 2: Successful Optimization

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"latitude": 40.7128, "longitude": -74.0060, "address": "New York, NY"},
      {"latitude": 40.7589, "longitude": -73.9851, "address": "Times Square, NY"},
      {"latitude": 40.7614, "longitude": -73.9776, "address": "Central Park, NY"},
      {"latitude": 40.7484, "longitude": -73.9857, "address": "Empire State Building, NY"}
    ],
    "depot_index": 0
  }'
```

**Expected Response Format:**
```json
{
  "optimized_route": [...],
  "optimized_metrics": {
    "total_distance_meters": <number>,
    "total_time_seconds": <number>
  },
  "baseline_metrics": {
    "total_distance_meters": <number>,
    "total_time_seconds": <number>
  },
  "distance_saved_meters": <number>,
  "time_saved_seconds": <number>,
  "distance_saved_percentage": <number>,
  "time_saved_percentage": <number>
}
```

### Test 3: Invalid Depot Index (400 Error)

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"latitude": 40.7128, "longitude": -74.0060},
      {"latitude": 40.7589, "longitude": -73.9851}
    ],
    "depot_index": 10
  }'
```

**Expected Response:**
```json
{
  "error": true,
  "code": "INVALID_DEPOT_INDEX",
  "message": "Depot index 10 is out of bounds for 2 stops",
  "details": [...],
  "suggestion": "Ensure depot_index is between 0 and the number of stops minus 1"
}
```

### Test 4: Invalid Coordinates (400 Error)

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"latitude": 95.0, "longitude": -74.0060},
      {"latitude": 40.7589, "longitude": -73.9851}
    ],
    "depot_index": 0
  }'
```

**Expected Response:**
```json
{
  "error": true,
  "code": "INVALID_COORDINATES",
  "message": "Invalid latitude at stop 0: 95.0",
  "details": [...],
  "suggestion": "Ensure latitude is between -90 and 90, longitude is between -180 and 180"
}
```

### Test 5: Too Many Stops (400 Error)

```bash
# Generate 101 stops
python3 << 'EOF'
import json

stops = [{"latitude": 40.0 + i * 0.01, "longitude": -74.0} for i in range(101)]
payload = {"stops": stops, "depot_index": 0}
print(json.dumps(payload))
EOF | curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d @-
```

**Expected Response:**
```json
{
  "error": true,
  "code": "TOO_MANY_STOPS",
  "message": "Too many stops: 101 provided, maximum is 100",
  "details": [...],
  "suggestion": "Reduce the number of stops or contact support for enterprise limits"
}
```

## Validation Checklist

Use this checklist to verify all documentation requirements are met:

### OMAP-T9 Requirements

- [x] **Step 1:** Ensure FastAPI auto-generates OpenAPI schema
  - OpenAPI schema is accessible at `/openapi.json`
  - Schema includes all endpoints and models
  - Schema is valid OpenAPI 3.x format

- [x] **Step 2:** Add detailed descriptions to endpoint docstrings
  - Root endpoint (/) has description and examples
  - Health endpoint (/health) has description and examples
  - Optimize endpoint (/optimize) has comprehensive description with workflow
  - All docstrings include parameter descriptions
  - All docstrings include return value descriptions

- [x] **Step 3:** Include request/response examples in documentation
  - OptimizationRequest model has example
  - OptimizationResponse model has example
  - Location model has example
  - RouteMetrics model has example
  - ErrorResponse model has example
  - Each endpoint shows example responses for all status codes

- [x] **Step 4:** Configure Swagger UI at /docs endpoint
  - Swagger UI is accessible at `/docs`
  - Shows comprehensive API description
  - Shows contact and license information
  - Displays all endpoints with detailed documentation
  - "Try it out" functionality works for all endpoints

- [x] **Step 5:** Add ReDoc alternative documentation at /redoc
  - ReDoc is accessible at `/redoc`
  - Shows same comprehensive information as Swagger UI
  - Professional, clean design
  - Easy navigation between endpoints

### Additional Features Implemented

- [x] Enhanced FastAPI app metadata (title, description, contact, license)
- [x] Added detailed API workflow documentation
- [x] Documented rate limits and constraints
- [x] Added error response examples for all error types (400, 500, 503)
- [x] Created comprehensive API_DOCUMENTATION.md reference file
- [x] Added usage examples in multiple languages (cURL, Python, JavaScript)
- [x] Documented all error codes with descriptions and suggestions

## Troubleshooting

### Issue: Documentation pages not loading

**Possible Causes:**
- Backend service not running
- Port 8000 is already in use
- CORS configuration blocking access

**Solutions:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if port is in use
lsof -i :8000  # On macOS/Linux
netstat -ano | findstr :8000  # On Windows

# Restart services
docker compose down
docker compose up --build
```

### Issue: "Try it out" not working in Swagger UI

**Possible Causes:**
- CORS not configured properly
- Network connectivity issues
- OSRM service unavailable

**Solutions:**
- Verify ALLOWED_ORIGINS environment variable includes http://localhost:8000
- Check backend logs for CORS errors
- Test endpoints with cURL to isolate frontend issues

### Issue: OpenAPI schema missing information

**Possible Causes:**
- Models missing Config class with examples
- Endpoint decorators missing response schemas
- FastAPI not detecting model fields

**Solutions:**
- Verify all Pydantic models have proper Field() definitions
- Ensure endpoint decorators include responses parameter
- Restart backend to regenerate schema

## Continuous Verification

To ensure documentation stays up-to-date:

1. **After code changes:**
   - Restart the backend service
   - Visit /docs to verify changes are reflected
   - Check /openapi.json for updated schema

2. **Before committing:**
   - Run through this testing guide
   - Verify all examples still work
   - Update API_DOCUMENTATION.md if endpoints changed

3. **In CI/CD:**
   - Add automated tests for /health endpoint
   - Validate OpenAPI schema format
   - Check that /docs and /redoc return 200 status

## Success Criteria

The API documentation is complete and working when:

- ✅ All endpoints are accessible and return expected responses
- ✅ Swagger UI (/docs) loads and displays all endpoints with examples
- ✅ ReDoc (/redoc) loads and displays formatted documentation
- ✅ OpenAPI schema (/openapi.json) is valid and complete
- ✅ All request/response examples match actual API behavior
- ✅ Error responses follow documented format with proper codes
- ✅ "Try it out" functionality works in Swagger UI
- ✅ Documentation is clear, comprehensive, and easy to understand

---

**Ticket Status:** OMAP-T9 - Create API Documentation ✅ COMPLETE

All requirements have been implemented and tested:
1. ✅ FastAPI auto-generates OpenAPI schema
2. ✅ Detailed descriptions added to endpoint docstrings
3. ✅ Request/response examples included in documentation
4. ✅ Swagger UI configured at /docs endpoint
5. ✅ ReDoc alternative documentation added at /redoc

Additional deliverables:
- Comprehensive API_DOCUMENTATION.md reference guide
- This testing guide for verification
- Enhanced error documentation with examples
- Usage examples in multiple languages
