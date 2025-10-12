# OptiMap API Documentation

## Overview

The OptiMap Route Optimizer API is a high-performance Vehicle Routing Problem (VRP) solver designed for last-mile logistics optimization. It uses Google OR-Tools and real-world routing data from OSRM to calculate optimal delivery routes.

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`

## Interactive Documentation

Once the backend is running, you can access interactive API documentation at:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Features

- **Real-world routing**: Uses OSRM for accurate road-based distance and time calculations
- **VRP optimization**: Powered by Google OR-Tools for optimal route sequencing
- **Baseline comparison**: Automatically compares optimized routes against sequential routes
- **Detailed metrics**: Provides distance and time savings with percentage improvements

## Authentication

Currently, the API does not require authentication. Future versions may include API key authentication.

## Rate Limits

- Maximum 100 stops per optimization request
- 30-second solver timeout (configurable)
- OSRM API timeout: 30 seconds (configurable)

## Endpoints

### Root Endpoint

**GET /** - API Information

Get basic information about the OptiMap API and links to documentation.

**Response 200 OK**
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

---

### Health Check

**GET /health** - Health Check

Check if the service is running and available. Use this endpoint to monitor service uptime.

**Response 200 OK**
```json
{
  "status": "healthy",
  "service": "OptiMap Backend",
  "timestamp": "2025-10-12T15:30:45.123456"
}
```

---

### Route Optimization

**POST /optimize** - Optimize Delivery Route

Calculate the optimal route for a list of delivery stops using VRP optimization.

#### Workflow

1. Validates the input stops (coordinates, depot index)
2. Calculates real-world distance matrix using OSRM
3. Solves VRP using OR-Tools to find optimal route sequence
4. Compares optimized route against baseline (sequential) route
5. Returns optimized route with detailed savings metrics

#### Request Body

```json
{
  "stops": [
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "New York, NY"
    },
    {
      "latitude": 40.7589,
      "longitude": -73.9851,
      "address": "Times Square, NY"
    },
    {
      "latitude": 40.7614,
      "longitude": -73.9776,
      "address": "Central Park, NY"
    },
    {
      "latitude": 40.7484,
      "longitude": -73.9857,
      "address": "Empire State Building, NY"
    }
  ],
  "depot_index": 0
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| stops | array | Yes | List of delivery stops (minimum 2, maximum 100) |
| stops[].latitude | float | Yes | Latitude coordinate (-90 to 90) |
| stops[].longitude | float | Yes | Longitude coordinate (-180 to 180) |
| stops[].address | string | No | Human-readable address (optional) |
| depot_index | integer | No | Index of starting/ending depot (default: 0) |

#### Response 200 OK

```json
{
  "optimized_route": [
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "New York, NY"
    },
    {
      "latitude": 40.7484,
      "longitude": -73.9857,
      "address": "Empire State Building, NY"
    },
    {
      "latitude": 40.7589,
      "longitude": -73.9851,
      "address": "Times Square, NY"
    },
    {
      "latitude": 40.7614,
      "longitude": -73.9776,
      "address": "Central Park, NY"
    },
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "New York, NY"
    }
  ],
  "optimized_metrics": {
    "total_distance_meters": 8420.5,
    "total_time_seconds": 1245.8
  },
  "baseline_metrics": {
    "total_distance_meters": 10850.2,
    "total_time_seconds": 1580.4
  },
  "distance_saved_meters": 2429.7,
  "time_saved_seconds": 334.6,
  "distance_saved_percentage": 22.4,
  "time_saved_percentage": 21.2
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| optimized_route | array | Stops in optimal visit order (includes return to depot) |
| optimized_metrics | object | Metrics for the optimized route |
| optimized_metrics.total_distance_meters | float | Total route distance in meters |
| optimized_metrics.total_time_seconds | float | Total route time in seconds |
| baseline_metrics | object | Metrics for the sequential (unoptimized) route |
| distance_saved_meters | float | Distance saved compared to baseline |
| time_saved_seconds | float | Time saved compared to baseline |
| distance_saved_percentage | float | Percentage of distance saved |
| time_saved_percentage | float | Percentage of time saved |

---

## Error Handling

All errors follow a consistent format with structured error responses.

### Error Response Format

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": [
    {
      "field": "field_name",
      "message": "Specific error details",
      "value": "invalid_value"
    }
  ],
  "suggestion": "Suggested action to fix the error"
}
```

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 500 | Internal Server Error - Solver or system failure |
| 503 | Service Unavailable - External service (OSRM) unavailable |

### Error Codes

#### Client Errors (400)

| Error Code | Description |
|------------|-------------|
| INVALID_INPUT | Request contains invalid input data |
| INVALID_COORDINATES | One or more coordinates are out of valid range |
| INVALID_DEPOT_INDEX | Depot index is out of bounds |
| INSUFFICIENT_STOPS | Less than 2 stops provided (minimum required) |
| TOO_MANY_STOPS | More than 100 stops provided (maximum limit) |

**Example - Invalid Depot Index:**
```json
{
  "error": true,
  "code": "INVALID_DEPOT_INDEX",
  "message": "Depot index 5 is out of bounds for 3 stops",
  "details": [
    {
      "field": "depot_index",
      "message": "Index 5 is invalid for 3 stops (valid range: 0-2)",
      "value": 5
    }
  ],
  "suggestion": "Ensure depot_index is between 0 and the number of stops minus 1"
}
```

**Example - Invalid Coordinates:**
```json
{
  "error": true,
  "code": "INVALID_COORDINATES",
  "message": "Invalid latitude at stop 2: 95.5",
  "details": [
    {
      "field": "stops[2].latitude",
      "message": "Latitude must be between -90 and 90",
      "value": 95.5
    }
  ],
  "suggestion": "Ensure latitude is between -90 and 90, longitude is between -180 and 180"
}
```

#### Server Errors (500)

| Error Code | Description |
|------------|-------------|
| SOLVER_FAILED | Optimization solver encountered an error |
| SOLVER_TIMEOUT | Solver exceeded time limit |
| SOLVER_NO_SOLUTION | Solver could not find a valid solution |
| INTERNAL_ERROR | Unexpected internal error occurred |

**Example - Solver Timeout:**
```json
{
  "error": true,
  "code": "SOLVER_NO_SOLUTION",
  "message": "Unable to find optimal route within time limit",
  "details": [
    {
      "field": "solver_timeout",
      "message": "Solver timed out after 30 seconds",
      "value": 30
    }
  ],
  "suggestion": "Try reducing the number of stops or increasing the solver timeout"
}
```

#### Service Errors (503)

| Error Code | Description |
|------------|-------------|
| ROUTING_SERVICE_UNAVAILABLE | OSRM routing service is unavailable |
| ROUTING_SERVICE_TIMEOUT | OSRM request exceeded timeout |
| ROUTING_SERVICE_ERROR | OSRM returned an error |

**Example - Routing Service Timeout:**
```json
{
  "error": true,
  "code": "ROUTING_SERVICE_TIMEOUT",
  "message": "Routing service request timed out after 30s",
  "details": [
    {
      "field": "osrm_timeout",
      "message": "OSRM API request exceeded timeout limit",
      "value": 30
    }
  ],
  "suggestion": "Try again with fewer stops or check your network connection"
}
```

---

## Example Usage

### Using cURL

#### Basic Optimization Request

```bash
curl -X POST "http://localhost:8000/optimize" \
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

#### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

### Using Python

```python
import requests

# API endpoint
url = "http://localhost:8000/optimize"

# Request payload
payload = {
    "stops": [
        {"latitude": 40.7128, "longitude": -74.0060, "address": "New York, NY"},
        {"latitude": 40.7589, "longitude": -73.9851, "address": "Times Square, NY"},
        {"latitude": 40.7614, "longitude": -73.9776, "address": "Central Park, NY"},
        {"latitude": 40.7484, "longitude": -73.9857, "address": "Empire State Building, NY"}
    ],
    "depot_index": 0
}

# Make request
response = requests.post(url, json=payload)

# Check response
if response.status_code == 200:
    result = response.json()
    print(f"Distance saved: {result['distance_saved_meters']:.0f}m")
    print(f"Time saved: {result['time_saved_seconds']:.0f}s")
    print(f"Improvement: {result['distance_saved_percentage']:.1f}%")
else:
    error = response.json()
    print(f"Error: {error['message']}")
```

### Using JavaScript (Fetch API)

```javascript
// API endpoint
const url = "http://localhost:8000/optimize";

// Request payload
const payload = {
  stops: [
    { latitude: 40.7128, longitude: -74.0060, address: "New York, NY" },
    { latitude: 40.7589, longitude: -73.9851, address: "Times Square, NY" },
    { latitude: 40.7614, longitude: -73.9776, address: "Central Park, NY" },
    { latitude: 40.7484, longitude: -73.9857, address: "Empire State Building, NY" }
  ],
  depot_index: 0
};

// Make request
fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(payload)
})
  .then(response => response.json())
  .then(result => {
    if (result.error) {
      console.error("Error:", result.message);
    } else {
      console.log(`Distance saved: ${result.distance_saved_meters.toFixed(0)}m`);
      console.log(`Time saved: ${result.time_saved_seconds.toFixed(0)}s`);
      console.log(`Improvement: ${result.distance_saved_percentage.toFixed(1)}%`);
    }
  })
  .catch(error => console.error("Request failed:", error));
```

---

## Performance Considerations

### Request Processing Time

Typical processing times for optimization requests:

| Number of Stops | Estimated Time |
|----------------|----------------|
| 2-10 stops | < 2 seconds |
| 10-20 stops | 2-5 seconds |
| 20-50 stops | 5-15 seconds |
| 50-100 stops | 15-30 seconds |

**Note:** Processing time depends on:
- Number of stops
- OSRM response time
- Geographic distribution of stops
- Available system resources

### Best Practices

1. **Batch Processing**: For multiple independent optimization requests, make parallel requests
2. **Error Handling**: Always implement retry logic for 503 errors (service unavailable)
3. **Timeout Handling**: Set appropriate client-side timeouts (60+ seconds recommended)
4. **Coordinate Validation**: Validate coordinates client-side before sending requests
5. **Caching**: Consider caching results for identical stop sets

---

## Configuration

The backend service can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| ALLOWED_ORIGINS | http://localhost:3000 | CORS allowed origins (comma-separated) |
| OSRM_BASE_URL | http://router.project-osrm.org | OSRM API base URL |
| OSRM_TIMEOUT_SECONDS | 30 | OSRM API request timeout |
| SOLVER_TIME_LIMIT_SECONDS | 30 | OR-Tools solver time limit |

---

## Support

For issues, questions, or contributions:

- **GitHub Issues**: [https://github.com/yourusername/optimap-route-optimizer/issues](https://github.com/yourusername/optimap-route-optimizer/issues)
- **Documentation**: See `/docs` endpoint for interactive documentation
- **Email**: support@optimap.example.com

---

## License

MIT License - See LICENSE file for details

---

## Changelog

### Version 1.0.0 (2025-10-12)

**Initial Release**
- POST /optimize endpoint for route optimization
- GET /health endpoint for health checks
- Comprehensive error handling with structured responses
- Interactive API documentation (Swagger UI and ReDoc)
- Support for up to 100 stops per request
- Real-world routing via OSRM integration
- VRP optimization via Google OR-Tools
- Baseline route comparison with savings metrics
