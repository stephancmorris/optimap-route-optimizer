# Logging and Monitoring - OptiMap Backend

## Overview

The OptiMap backend implements comprehensive structured logging to provide visibility into system operations, performance, and errors. Logging is implemented at multiple levels to track:

- HTTP requests and responses
- External API calls (OSRM)
- VRP solver execution
- Error conditions and exceptions

## Logging Architecture

### Components

1. **Logging Configuration** ([app/config/logging_config.py](app/config/logging_config.py))
   - Structured and colored formatters
   - Console and file handlers
   - Log level configuration

2. **Request Logging Middleware** ([app/middleware/logging_middleware.py](app/middleware/logging_middleware.py))
   - Automatic request/response logging
   - Request correlation IDs
   - Request duration tracking
   - Sensitive data sanitization

3. **Service-Level Logging**
   - OSRM client API call logging with timing
   - VRP solver execution logging with performance metrics
   - Route optimization workflow logging

## Configuration

### Environment Variables

Configure logging behavior using these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| LOG_LEVEL | INFO | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| LOG_JSON_FORMAT | false | Use JSON structured logging (recommended for production) |
| LOG_FILE | None | Optional file path for log output |

### Example Configuration

**Development (.env):**
```bash
LOG_LEVEL=DEBUG
LOG_JSON_FORMAT=false
LOG_FILE=
```

**Production (.env):**
```bash
LOG_LEVEL=INFO
LOG_JSON_FORMAT=true
LOG_FILE=/var/log/optimap/app.log
```

## Log Levels

### DEBUG
Detailed diagnostic information for troubleshooting.

**Example:**
```
Creating routing index manager for 5 locations
Starting solver with strategy: PATH_CHEAPEST_ARC
```

**When to use:** Local development, debugging specific issues

### INFO
General informational messages about normal operations.

**Example:**
```
Starting VRP solver: 5 locations, 1 vehicle(s), depot=0, time_limit=30s
Successfully calculated 5x5 distance matrix: total_time=1250ms
VRP solver completed successfully: route_length=6, total_distance=8420m, solve_time=2.45s
```

**When to use:** Production monitoring, tracking request flow

### WARNING
Indication of unexpected events that don't prevent operation.

**Example:**
```
VRP solver failed to find solution: locations=50, time_elapsed=30.12s, time_limit=30s
```

**When to use:** Performance issues, timeouts, degraded functionality

### ERROR
Error events that affect specific operations.

**Example:**
```
OSRM API timeout after 30000ms: Request timeout
OSRM network error after 5000ms: Connection refused
```

**When to use:** API failures, external service errors

### CRITICAL
Severe errors causing system failure.

**Example:**
```
Failed to initialize FastAPI application: {exception details}
```

**When to use:** System-wide failures, startup errors

## Log Formats

### Development Format (Colored Console)

Human-readable colored output for development:

```
2025-10-12 15:30:45 | INFO     | app.main:80 | OptiMap API starting with configuration: OSRM=http://router.project-osrm.org, Solver timeout=30s, Log level=INFO
2025-10-12 15:30:46 | INFO     | app.middleware.logging_middleware:45 | Incoming request: POST /optimize
2025-10-12 15:30:46 | INFO     | app.services.osrm_client:186 | Calculating distance matrix for 4 locations via OSRM
2025-10-12 15:30:47 | INFO     | app.services.osrm_client:130 | OSRM API request successful: status=200, response_time=1234ms
2025-10-12 15:30:47 | INFO     | app.services.vrp_solver:76 | Starting VRP solver: 4 locations, 1 vehicle(s), depot=0, time_limit=30s
2025-10-12 15:30:49 | INFO     | app.services.vrp_solver:125 | VRP solver completed successfully: route_length=5, total_distance=8420m, solve_time=2.15s
2025-10-12 15:30:49 | INFO     | app.middleware.logging_middleware:60 | Request completed: POST /optimize - 200
```

### Production Format (JSON Structured)

Machine-readable JSON for log aggregation systems:

```json
{
  "timestamp": "2025-10-12T15:30:45.123456Z",
  "level": "INFO",
  "logger": "app.main",
  "message": "OptiMap API starting with configuration: OSRM=http://router.project-osrm.org, Solver timeout=30s, Log level=INFO",
  "source": {
    "file": "/app/app/main.py",
    "line": 80,
    "function": "<module>"
  }
}

{
  "timestamp": "2025-10-12T15:30:46.234567Z",
  "level": "INFO",
  "logger": "app.middleware.logging_middleware",
  "message": "Incoming request: POST /optimize",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "POST",
  "endpoint": "/optimize",
  "client_ip": "172.18.0.1",
  "source": {
    "file": "/app/app/middleware/logging_middleware.py",
    "line": 45,
    "function": "dispatch"
  }
}

{
  "timestamp": "2025-10-12T15:30:49.345678Z",
  "level": "INFO",
  "logger": "app.middleware.logging_middleware",
  "message": "Request completed: POST /optimize - 200",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "POST",
  "endpoint": "/optimize",
  "status_code": 200,
  "duration_ms": 3120.45,
  "source": {
    "file": "/app/app/middleware/logging_middleware.py",
    "line": 60,
    "function": "dispatch"
  }
}
```

## What Gets Logged

### 1. HTTP Requests

Every HTTP request is automatically logged with:

**Incoming Request:**
- Request ID (UUID for correlation)
- HTTP method
- Endpoint path
- Client IP address
- Query parameters (if any)
- Timestamp

**Outgoing Response:**
- Request ID (same as incoming)
- HTTP status code
- Processing duration (milliseconds)
- Timestamp

**Example:**
```
INFO | Incoming request: POST /optimize
INFO | Request completed: POST /optimize - 200 (duration=3120ms)
```

### 2. OSRM API Calls

External routing API calls are logged with:

**Request:**
- API URL
- Number of locations
- Start timestamp

**Response:**
- Status code
- Response time (milliseconds)
- Matrix dimensions
- Success/failure indication

**Example:**
```
INFO | Calculating distance matrix for 4 locations via OSRM
INFO | OSRM API request successful: status=200, response_time=1234ms
INFO | Successfully calculated 4x4 distance matrix: total_time=1250ms
```

**Errors:**
```
ERROR | OSRM API timeout after 30000ms: Request timeout
ERROR | OSRM HTTP error: status=503, response_time=5000ms
ERROR | OSRM network error after 2000ms: Connection refused
```

### 3. VRP Solver Execution

Optimization algorithm execution is logged with:

**Start:**
- Number of locations
- Number of vehicles
- Depot index
- Time limit configuration

**Progress:**
- Routing model initialization (DEBUG level)
- Solver strategy (DEBUG level)

**Completion:**
- Route length (number of stops)
- Total distance (meters)
- Solve time (seconds)
- Success/failure indication

**Example:**
```
INFO | Starting VRP solver: 4 locations, 1 vehicle(s), depot=0, time_limit=30s
DEBUG | Creating routing index manager for 4 locations
DEBUG | Initializing routing model
DEBUG | Starting solver with strategy: PATH_CHEAPEST_ARC
INFO | VRP solver completed successfully: route_length=5, total_distance=8420m, solve_time=2.15s
```

**Failures:**
```
WARNING | VRP solver failed to find solution: locations=50, time_elapsed=30.12s, time_limit=30s
```

### 4. Optimization Workflow

Complete optimization requests log the entire workflow:

**Example Complete Flow:**
```
INFO | Incoming request: POST /optimize
INFO | Optimizing route for 4 stops with depot at index 0
INFO | Calculating distance matrix for 4 locations via OSRM
INFO | OSRM API request successful: status=200, response_time=1234ms
INFO | Successfully calculated 4x4 distance matrix: total_time=1250ms
INFO | Starting VRP solver: 4 locations, 1 vehicle(s), depot=0, time_limit=30s
INFO | VRP solver completed successfully: route_length=5, total_distance=8420m, solve_time=2.15s
INFO | Optimization complete: 2429m saved (22.4%), 335s saved (21.2%)
INFO | Request completed: POST /optimize - 200 (duration=3650ms)
```

### 5. Error Conditions

Errors are logged with full context and stack traces:

**Validation Errors:**
```
WARNING | Invalid depot index: 10 out of bounds for 5 stops
WARNING | Invalid coordinates at stop 2: latitude=95.0 exceeds valid range
```

**External Service Errors:**
```
ERROR | OSRM API error: No route found between locations (response_time=800ms)
ERROR | OSRM API timeout after 30000ms: httpx.TimeoutException
```

**Solver Errors:**
```
WARNING | VRP solver failed to find solution: locations=100, time_elapsed=30.01s, time_limit=30s
ERROR | VRP solver error: OrToolsError - Invalid distance matrix
```

**Unexpected Errors:**
```
ERROR | Unexpected error during optimization: {error message}
{full stack trace}
```

## Request Correlation

Every request is assigned a unique UUID that appears in all related log entries. This allows tracing a single request through the entire system.

**Example:**
```json
{"timestamp": "...", "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "message": "Incoming request"}
{"timestamp": "...", "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "message": "OSRM request"}
{"timestamp": "...", "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "message": "VRP solver start"}
{"timestamp": "...", "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "message": "Request completed"}
```

The request ID is also returned in the `X-Request-ID` response header for client-side correlation.

## Sensitive Data Handling

The logging middleware automatically sanitizes sensitive information:

**Sanitized Fields:**
- password
- token
- api_key
- secret
- authorization

These fields are replaced with `***REDACTED***` in logs.

## Performance Metrics

Timing information is logged at key points:

| Metric | Where Logged | Format |
|--------|-------------|--------|
| Request duration | Request middleware | milliseconds |
| OSRM API call duration | OSRM client | milliseconds |
| Distance matrix calculation | OSRM client | milliseconds |
| VRP solver execution | VRP solver | seconds |
| Total optimization time | Optimize endpoint | milliseconds |

## Log Analysis

### Useful Log Queries

#### Find all requests by request ID:
```bash
grep "a1b2c3d4-e5f6-7890-abcd-ef1234567890" app.log
```

#### Find slow requests (>5 seconds):
```bash
grep "duration_ms" app.log | awk -F'"duration_ms": ' '{print $2}' | awk -F',' '{if ($1 > 5000) print $0}'
```

#### Count errors by type:
```bash
grep '"level": "ERROR"' app.log | grep -o '"logger": "[^"]*"' | sort | uniq -c
```

#### Find OSRM timeouts:
```bash
grep "OSRM API timeout" app.log
```

#### Find solver failures:
```bash
grep "VRP solver failed" app.log
```

### JSON Log Parsing (with jq)

```bash
# Get all ERROR level logs
cat app.log | jq 'select(.level == "ERROR")'

# Get requests longer than 5 seconds
cat app.log | jq 'select(.duration_ms > 5000)'

# Get all logs for a specific request
cat app.log | jq 'select(.request_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890")'

# Count errors by source file
cat app.log | jq -r 'select(.level == "ERROR") | .source.file' | sort | uniq -c
```

## Integration with Monitoring Systems

### Logging Aggregation

The JSON structured format is compatible with:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch Logs**
- **Loki + Grafana**

### Metrics Extraction

Key metrics that can be extracted for dashboards:

1. **Request Rate**
   - Total requests per minute
   - Requests by endpoint
   - Success vs. error rate

2. **Performance Metrics**
   - Average request duration
   - P50, P95, P99 response times
   - OSRM API response times
   - Solver execution times

3. **Error Metrics**
   - Error rate by type
   - OSRM timeout frequency
   - Solver failure rate
   - HTTP error codes

4. **Business Metrics**
   - Average optimization savings (distance, time)
   - Average number of stops per request
   - Most common depot locations

## Best Practices

### Development

- Use `LOG_LEVEL=DEBUG` for detailed troubleshooting
- Use colored console output (`LOG_JSON_FORMAT=false`)
- Review logs regularly to understand system behavior

### Production

- Use `LOG_LEVEL=INFO` for normal operations
- Use JSON structured format (`LOG_JSON_FORMAT=true`)
- Ship logs to a centralized logging system
- Set up alerts for ERROR and CRITICAL logs
- Monitor key performance metrics
- Rotate log files to prevent disk fill-up

### Troubleshooting

1. **Identify the request:** Find the request ID in the error log
2. **Trace the flow:** Search for all log entries with that request ID
3. **Check timing:** Look for slow operations (OSRM, solver)
4. **Review errors:** Check full stack traces for root cause
5. **Verify inputs:** Check request parameters in DEBUG logs

## Example: Complete Request Log Trace

```
2025-10-12 15:30:46.123 | INFO | app.middleware | Incoming request: POST /optimize [request_id=abc-123]
2025-10-12 15:30:46.125 | INFO | app.routers.optimize | Optimizing route for 4 stops with depot at index 0 [request_id=abc-123]
2025-10-12 15:30:46.126 | INFO | app.services.osrm_client | Calculating distance matrix for 4 locations via OSRM
2025-10-12 15:30:46.127 | INFO | app.services.osrm_client | Requesting OSRM API: http://router...
2025-10-12 15:30:47.350 | INFO | app.services.osrm_client | OSRM API request successful: status=200, response_time=1223ms
2025-10-12 15:30:47.351 | INFO | app.services.osrm_client | Successfully calculated 4x4 distance matrix: total_time=1225ms
2025-10-12 15:30:47.352 | INFO | app.services.vrp_solver | Starting VRP solver: 4 locations, 1 vehicle(s), depot=0, time_limit=30s
2025-10-12 15:30:49.503 | INFO | app.services.vrp_solver | VRP solver completed successfully: route_length=5, total_distance=8420m, solve_time=2.15s
2025-10-12 15:30:49.505 | INFO | app.routers.optimize | Optimization complete: 2429m saved (22.4%), 335s saved (21.2%)
2025-10-12 15:30:49.507 | INFO | app.middleware | Request completed: POST /optimize - 200 (duration=3384ms) [request_id=abc-123]
```

## Files Modified/Created

### Created Files
- `app/config/logging_config.py` - Logging configuration and formatters
- `app/middleware/logging_middleware.py` - Request/response logging middleware
- `app/middleware/__init__.py` - Middleware package initialization

### Modified Files
- `app/main.py` - Integrated logging setup and middleware
- `app/config/settings.py` - Added logging configuration options
- `app/services/vrp_solver.py` - Added solver execution logging
- `app/services/osrm_client.py` - Added API call logging with timing
- `app/routers/optimize.py` - Already had optimization logging

## Configuration Reference

### Complete .env Example

```bash
# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# OSRM Configuration
OSRM_BASE_URL=http://router.project-osrm.org
OSRM_TIMEOUT_SECONDS=30

# Solver Configuration
SOLVER_TIME_LIMIT_SECONDS=30

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging Configuration
LOG_LEVEL=INFO
LOG_JSON_FORMAT=false
LOG_FILE=
```

---

**OMAP-T10 Status:** ✅ COMPLETE - Comprehensive logging and monitoring implemented across all system components.
