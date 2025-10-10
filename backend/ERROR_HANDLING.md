# Error Handling Guide

## Overview

OptiMap implements comprehensive error handling with structured error responses, specific error codes, and user-friendly messages to help diagnose and resolve issues quickly.

## Error Response Format

All API errors return a consistent JSON structure:

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": [
    {
      "field": "field_name",
      "message": "Specific error detail",
      "value": "invalid_value"
    }
  ],
  "suggestion": "How to fix the error"
}
```

## HTTP Status Codes

| Status Code | Meaning | When Used |
|-------------|---------|-----------|
| `400` | Bad Request | Invalid input data, coordinates, depot index |
| `500` | Internal Server Error | Solver errors, unexpected failures |
| `503` | Service Unavailable | External routing service down or timeout |

## Error Codes

### Client Errors (400)

#### INVALID_INPUT
**Message:** "The request contains invalid input data"

**Causes:**
- Malformed JSON
- Missing required fields
- Invalid data types

**Solution:** Check request format and ensure all required fields are present

---

#### INVALID_COORDINATES
**Message:** "One or more coordinates are invalid"

**Causes:**
- Latitude outside range -90 to 90
- Longitude outside range -180 to 180
- Non-numeric coordinates

**Example:**
```json
{
  "error": true,
  "code": "INVALID_COORDINATES",
  "message": "Invalid latitude at stop 2: 95.5",
  "details": [{
    "field": "stops[2].latitude",
    "message": "Latitude must be between -90 and 90",
    "value": 95.5
  }],
  "suggestion": "Ensure latitude is between -90 and 90, longitude is between -180 and 180"
}
```

**Solution:** Verify all coordinates are valid before submitting

---

#### INVALID_DEPOT_INDEX
**Message:** "The specified depot index is out of bounds"

**Causes:**
- Depot index >= number of stops
- Negative depot index

**Example:**
```json
{
  "error": true,
  "code": "INVALID_DEPOT_INDEX",
  "message": "Depot index 5 is out of bounds for 3 stops",
  "details": [{
    "field": "depot_index",
    "message": "Index 5 is invalid for 3 stops (valid range: 0-2)",
    "value": 5
  }],
  "suggestion": "Ensure depot_index is between 0 and the number of stops minus 1"
}
```

**Solution:** Set `depot_index` to a valid index (0 to N-1 where N is number of stops)

---

#### INSUFFICIENT_STOPS
**Message:** "At least 2 stops are required for route optimization"

**Causes:**
- Less than 2 stops provided

**Solution:** Add at least 2 stops to the request

---

#### TOO_MANY_STOPS
**Message:** "Too many stops provided - maximum limit exceeded"

**Causes:**
- More than 100 stops provided (default limit)

**Solution:** Reduce number of stops or contact support for enterprise limits

### Server Errors (500)

#### SOLVER_FAILED
**Message:** "The optimization solver encountered an error"

**Causes:**
- Invalid distance matrix
- Solver internal error
- Memory issues

**Solution:** Try again with fewer stops or check coordinate validity

---

#### SOLVER_TIMEOUT
**Message:** "The optimization solver timed out before finding a solution"

**Causes:**
- Too many stops for given time limit
- Complex routing problem

**Configuration:**
```bash
# Increase timeout in .env
SOLVER_TIME_LIMIT_SECONDS=60
```

**Solution:** Reduce stops or increase solver timeout

---

#### SOLVER_NO_SOLUTION
**Message:** "The optimization solver could not find a valid solution"

**Causes:**
- Unreachable locations
- Invalid coordinates
- Disconnected road network

**Solution:** Verify all stops are accessible by road and coordinates are correct

---

#### INTERNAL_ERROR
**Message:** "An unexpected internal error occurred"

**Causes:**
- Unhandled exception
- System resource issue

**Solution:** Contact support if issue persists

### Service Errors (503)

#### ROUTING_SERVICE_UNAVAILABLE
**Message:** "The routing service is currently unavailable"

**Causes:**
- OSRM service down
- Network connectivity issues
- DNS resolution failure

**Solution:** Wait a few moments and retry. Check OSRM service status

---

#### ROUTING_SERVICE_TIMEOUT
**Message:** "The routing service request timed out"

**Causes:**
- OSRM service slow response
- Network latency
- Too many locations

**Configuration:**
```bash
# Increase timeout in .env
OSRM_TIMEOUT_SECONDS=60
```

**Solution:** Try with fewer stops or increase OSRM timeout

---

#### ROUTING_SERVICE_ERROR
**Message:** "The routing service returned an error"

**Causes:**
- Invalid coordinates for OSRM
- OSRM API error
- Rate limiting

**Solution:** Verify coordinates are valid and routable

## Configuration

### Timeout Settings

Control timeouts via environment variables:

```bash
# OSRM API timeout (default: 30s)
OSRM_TIMEOUT_SECONDS=30

# OR-Tools solver timeout (default: 30s)
SOLVER_TIME_LIMIT_SECONDS=30
```

### Validation Limits

```python
# Maximum stops allowed
MAX_STOPS = 100

# Coordinate ranges
LATITUDE_RANGE = (-90, 90)
LONGITUDE_RANGE = (-180, 180)
```

## Frontend Error Handling

The frontend automatically extracts error messages and suggestions:

```javascript
try {
  const result = await optimizeRoute(stops, 0);
} catch (error) {
  // error.message contains user-friendly message
  // error.code contains error code (e.g., "INVALID_COORDINATES")
  // error.details contains array of detailed errors
  // error.statusCode contains HTTP status code
  console.error(error.message);
}
```

## Testing Error Scenarios

### Test Invalid Coordinates

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"latitude": 95.0, "longitude": -122.0},
      {"latitude": 37.0, "longitude": -122.0}
    ],
    "depot_index": 0
  }'
```

Expected: `400 INVALID_COORDINATES`

### Test Invalid Depot Index

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"latitude": 37.7749, "longitude": -122.4194},
      {"latitude": 37.7849, "longitude": -122.4094}
    ],
    "depot_index": 5
  }'
```

Expected: `400 INVALID_DEPOT_INDEX`

### Test Too Many Stops

```bash
# Generate 101 stops
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d @large_request.json
```

Expected: `400 TOO_MANY_STOPS`

### Test Timeout

```bash
# Set very short timeout
export SOLVER_TIME_LIMIT_SECONDS=1

# Send request with many stops
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d @complex_route.json
```

Expected: `500 SOLVER_TIMEOUT` or `500 SOLVER_NO_SOLUTION`

## Logging

All errors are logged with appropriate severity:

- **Client errors (400)**: `logger.warning()`
- **Server errors (500)**: `logger.error()` with stack trace
- **Service errors (503)**: `logger.error()`

View logs:
```bash
# Development
tail -f logs/optimap.log

# Docker
docker-compose logs -f backend
```

## Best Practices

### For API Consumers

1. **Always check error codes** - Don't rely solely on HTTP status
2. **Display suggestions** - Show `suggestion` field to users
3. **Log details** - Include `details` array in error logs
4. **Implement retries** - Retry 503 errors with exponential backoff
5. **Validate client-side** - Catch 400 errors before sending

### For Developers

1. **Use structured errors** - Always use `create_error_response()`
2. **Provide context** - Include field names and values in details
3. **Write helpful suggestions** - Guide users to fix the issue
4. **Log appropriately** - Use correct log levels
5. **Test error paths** - Write tests for all error scenarios

## Common Issues

### "Routing service unavailable"

**Cause:** OSRM service is down or unreachable

**Solutions:**
1. Check OSRM service status: `curl http://router.project-osrm.org/health`
2. Verify network connectivity
3. Try alternative OSRM instance

### "Solver timeout"

**Cause:** Too many stops or complex routing problem

**Solutions:**
1. Reduce number of stops
2. Increase `SOLVER_TIME_LIMIT_SECONDS`
3. Check for unreachable locations

### "Invalid coordinates"

**Cause:** Coordinates outside valid range

**Solutions:**
1. Verify latitude is between -90 and 90
2. Verify longitude is between -180 and 180
3. Check for swapped lat/lon values

## Support

For persistent errors:

1. Check logs for detailed error messages
2. Verify configuration in `.env`
3. Review [API Documentation](http://localhost:8000/docs)
4. Contact support with error code and request ID
