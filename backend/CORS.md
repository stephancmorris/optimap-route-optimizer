# CORS Configuration Guide

## Overview

Cross-Origin Resource Sharing (CORS) is configured to allow the React frontend to communicate with the FastAPI backend from different origins (domains/ports).

## Current Configuration

### Allowed Origins

The backend accepts requests from origins specified in the `ALLOWED_ORIGINS` environment variable:

**Default (Development):**
- `http://localhost:3000` - Production build served by nginx/Docker
- `http://localhost:5173` - Vite development server

**Configuration Location:**
- Environment variable: `ALLOWED_ORIGINS` in `.env` file
- Settings class: `backend/app/config/settings.py`
- Applied in: `backend/app/main.py`

### Allowed Methods

The following HTTP methods are explicitly allowed:
- `GET` - Retrieve data (health checks, etc.)
- `POST` - Submit optimization requests
- `OPTIONS` - Preflight requests (automatic)

### Allowed Headers

- `Content-Type` - Required for JSON payloads
- `Authorization` - For future authentication implementation

### Additional Settings

- **Credentials**: `allow_credentials=True` - Allows cookies/auth headers
- **Max Age**: `600 seconds` - Browsers cache preflight requests for 10 minutes

## How It Works

### Preflight Requests

For cross-origin POST requests with JSON, browsers automatically send an OPTIONS request first:

```
OPTIONS /optimize HTTP/1.1
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
```

The backend responds with allowed origins, methods, and headers:

```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 600
```

### Actual Request

After a successful preflight, the browser sends the actual request:

```
POST /optimize HTTP/1.1
Origin: http://localhost:5173
Content-Type: application/json

{"stops": [...], "depot_index": 0}
```

## Configuration Examples

### Development (Local)

```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production (Single Domain)

```bash
# .env
ALLOWED_ORIGINS=https://optimap.yourdomain.com
```

### Production (Multiple Domains)

```bash
# .env
ALLOWED_ORIGINS=https://optimap.com,https://app.optimap.com,https://optimap.yourdomain.com
```

### Development + Staging

```bash
# .env
ALLOWED_ORIGINS=http://localhost:5173,https://staging.optimap.com
```

## Security Best Practices

### ✅ DO

1. **Specify exact origins** - Never use `"*"` in production
2. **Use HTTPS in production** - Always use `https://` for production domains
3. **List only necessary origins** - Don't add origins you don't control
4. **Use environment variables** - Keep configuration separate from code
5. **Specify exact methods** - Only allow methods your API uses

### ❌ DON'T

1. **Don't use wildcard (`"*"`)** in production - Security risk
2. **Don't allow all methods** - Limit to GET, POST, OPTIONS
3. **Don't allow all headers** - Specify only what you need
4. **Don't hardcode origins** - Use environment variables
5. **Don't mix HTTP/HTTPS** - Use HTTPS everywhere in production

## Testing CORS

### Test with curl

```bash
# Simulate preflight request
curl -X OPTIONS http://localhost:8000/optimize \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v

# Look for these headers in response:
# Access-Control-Allow-Origin: http://localhost:5173
# Access-Control-Allow-Methods: GET, POST, OPTIONS
# Access-Control-Allow-Headers: Content-Type, Authorization
```

### Test from Browser Console

```javascript
// Open frontend (http://localhost:5173) and run in console
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log('CORS working:', data))
  .catch(err => console.error('CORS error:', err));
```

### Check Browser DevTools

1. Open Network tab
2. Make a request from frontend to backend
3. Check the request headers include `Origin: http://localhost:5173`
4. Check the response headers include `Access-Control-Allow-Origin`

## Troubleshooting

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Cause:** Origin not in `ALLOWED_ORIGINS` list

**Solution:**
```bash
# Add your frontend URL to .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:YOUR_PORT
```

Restart backend after changing `.env`.

### Error: "Method POST is not allowed by Access-Control-Allow-Methods"

**Cause:** HTTP method not in allowed methods list

**Solution:** Verify POST is in the allowed methods (it should be by default)

### Error: "Request header field content-type is not allowed"

**Cause:** Header not in allowed headers list

**Solution:** Verify Content-Type is in allowed headers (it should be by default)

### CORS works locally but not in production

**Causes:**
1. Production origin not added to `ALLOWED_ORIGINS`
2. Using HTTP in production instead of HTTPS
3. Subdomain mismatch (www vs non-www)

**Solution:**
```bash
# Add production domain with correct protocol
ALLOWED_ORIGINS=https://optimap.yourdomain.com,https://www.optimap.yourdomain.com
```

## Code Reference

### Main Configuration (main.py)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,  # From ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)
```

### Settings Parser (settings.py)

```python
@property
def origins_list(self) -> list[str]:
    """Convert comma-separated origins string to list."""
    return [origin.strip() for origin in self.allowed_origins.split(",")]
```

## Additional Resources

- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [OWASP CORS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
