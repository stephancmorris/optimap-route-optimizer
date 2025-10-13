# Geocoding Feature - Quick Start Guide

## 🎯 Goal
Allow users to input addresses instead of manually looking up latitude/longitude coordinates.

## ✅ Good News
**Real-world routing already works!** Your OSRM integration already accounts for one-way streets, turn restrictions, and actual road networks. No changes needed there.

## 🆕 What We're Adding
Address-to-coordinate conversion (geocoding) to simplify user input.

---

## Quick Implementation Guide

### Phase 1: Backend Core (2-3 days)

#### Step 1: Add Geocoding Client (OMAP-T13)
**File:** `backend/app/services/geocoding_client.py`

```python
# Create new file with GeocodingClient class
# Use Nominatim (free) for MVP:
# https://nominatim.openstreetmap.org/search?q=ADDRESS&format=json

class GeocodingClient:
    async def geocode_address(self, address: str) -> Tuple[float, float]:
        """Convert address to (lat, lng)."""
        # Make API call to Nominatim
        # Return coordinates or raise exception
```

**Add to settings:**
```python
# backend/app/config/settings.py
geocoding_api_url: str = "https://nominatim.openstreetmap.org"
geocoding_timeout_seconds: int = 10
```

#### Step 2: Update Location Model (OMAP-T14)
**File:** `backend/app/models/route.py`

```python
class Location(BaseModel):
    latitude: Optional[float] = None  # Make optional
    longitude: Optional[float] = None  # Make optional
    address: Optional[str] = None
    geocoded: bool = False

    @model_validator(mode='after')
    def validate_location(self):
        # Require either address OR coordinates
        has_coords = self.latitude and self.longitude
        has_address = self.address and self.address.strip()

        if not has_coords and not has_address:
            raise ValueError("Provide address or coordinates")
        return self
```

#### Step 3: Add Geocoding to Endpoint (OMAP-T15)
**File:** `backend/app/routers/optimize.py`

```python
async def optimize_route(request: OptimizationRequest):
    # NEW: Geocode addresses
    geocoding_client = GeocodingClient(...)

    for stop in request.stops:
        if stop.address and not stop.latitude:
            # Geocode this stop
            lat, lng = await geocoding_client.geocode_address(stop.address)
            stop.latitude = lat
            stop.longitude = lng
            stop.geocoded = True

    # EXISTING: Continue with optimization
    distances, durations = await osrm_client.get_distance_matrix(...)
    # ... rest of existing code
```

#### Step 4: Add Simple Cache (OMAP-T16)
**File:** `backend/app/services/geocoding_client.py`

```python
from functools import lru_cache

class GeocodingClient:
    @lru_cache(maxsize=1000)
    def _normalize_address(self, address: str) -> str:
        return address.lower().strip()

    # Add caching to geocode method
```

---

### Phase 2: Frontend UI (2-3 days)

#### Update Input Form (OMAP-S11)
**File:** `frontend/src/components/StopInput.jsx`

```javascript
// Allow users to enter address instead of coordinates
<input
  type="text"
  placeholder="Address or click map"
  value={stop.address}
  onChange={(e) => setStop({...stop, address: e.target.value})}
/>

// Make lat/lng optional
<input
  type="number"
  placeholder="Latitude (optional)"
  value={stop.latitude}
/>
```

#### Show Geocoding Results
```javascript
// After optimization, show what was geocoded
{response.optimized_route.map(stop => (
  <div>
    <strong>{stop.address}</strong>
    {stop.geocoded && (
      <span className="badge">
        Geocoded: {stop.latitude}, {stop.longitude}
      </span>
    )}
  </div>
))}
```

---

## Testing

### Manual Test Script

```bash
# 1. Start services
docker compose up --build

# 2. Test with address
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"address": "Times Square, New York, NY"},
      {"address": "Central Park, New York, NY"},
      {"address": "Empire State Building, New York, NY"}
    ],
    "depot_index": 0
  }'

# 3. Test with mixed input
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"address": "Times Square, New York, NY"},
      {"latitude": 40.7484, "longitude": -73.9857}
    ],
    "depot_index": 0
  }'

# 4. Test error handling
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"address": "Invalid Address 123456"}
    ],
    "depot_index": 0
  }'
```

---

## Geocoding Service Options

### Option 1: Nominatim (Recommended for MVP)
- **Cost:** FREE
- **API Key:** Not required
- **Rate Limit:** 1 request/second
- **Accuracy:** Good
- **URL:** `https://nominatim.openstreetmap.org`

**Pros:** Free, no signup, works immediately
**Cons:** Rate limited, requires User-Agent header

**Usage:**
```bash
curl "https://nominatim.openstreetmap.org/search?q=Times+Square+New+York&format=json"
```

### Option 2: Google Maps Geocoding API
- **Cost:** $5 per 1,000 requests (first $200/month free)
- **API Key:** Required
- **Rate Limit:** 50 requests/second
- **Accuracy:** Excellent

**Pros:** Best accuracy, high rate limits
**Cons:** Requires credit card, costs money

### Option 3: Mapbox Geocoding API
- **Cost:** $0.50 per 1,000 requests (100k free/month)
- **API Key:** Required
- **Rate Limit:** 600 requests/minute
- **Accuracy:** Very good

**Pros:** Good accuracy, generous free tier
**Cons:** Requires signup

**Recommendation:** Start with Nominatim, upgrade to Google/Mapbox if needed.

---

## Example API Request/Response

### Before (Manual Coordinates)
```json
POST /optimize
{
  "stops": [
    {"latitude": 40.7128, "longitude": -74.0060},
    {"latitude": 40.7589, "longitude": -73.9851}
  ],
  "depot_index": 0
}
```

### After (Address-Based)
```json
POST /optimize
{
  "stops": [
    {"address": "123 Main St, New York, NY 10001"},
    {"address": "Times Square, New York, NY"}
  ],
  "depot_index": 0
}
```

### Response (With Geocoding Info)
```json
{
  "optimized_route": [
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "123 Main St, New York, NY 10001",
      "geocoded": true,
      "geocoding_confidence": 0.95
    },
    {
      "latitude": 40.7589,
      "longitude": -73.9851,
      "address": "Times Square, New York, NY",
      "geocoded": true,
      "geocoding_confidence": 0.98
    }
  ],
  "optimized_metrics": { ... },
  "baseline_metrics": { ... }
}
```

---

## Common Issues & Solutions

### Issue: Geocoding Takes Too Long
**Solution:** Implement caching (OMAP-T16) and parallel geocoding
```python
# Geocode all addresses in parallel
results = await asyncio.gather(*[
    geocode(stop.address) for stop in stops if stop.address
])
```

### Issue: Address Not Found
**Solution:** Return clear error with suggestions
```json
{
  "error": true,
  "code": "GEOCODING_FAILED",
  "message": "Could not find address: 'asdfasdf'",
  "suggestion": "Please provide a more specific address with city and state"
}
```

### Issue: Wrong Coordinates Returned
**Solution:** Return coordinates in response for user verification
```javascript
// Show on map for visual verification
<Marker position={[stop.latitude, stop.longitude]} />
<Tooltip>
  Geocoded: {stop.address} → {stop.latitude}, {stop.longitude}
</Tooltip>
```

### Issue: Rate Limited by Nominatim
**Solution:** Add delay between requests
```python
import asyncio

async def geocode_with_rate_limit(address):
    result = await geocode(address)
    await asyncio.sleep(1.1)  # Respect 1 req/sec limit
    return result
```

---

## Configuration

### Environment Variables
```bash
# .env file
GEOCODING_PROVIDER=nominatim
GEOCODING_API_URL=https://nominatim.openstreetmap.org
GEOCODING_API_KEY=  # Empty for Nominatim
GEOCODING_TIMEOUT_SECONDS=10
GEOCODING_CACHE_ENABLED=true
GEOCODING_CACHE_SIZE=1000
```

### Nominatim Usage Requirements
⚠️ **Important:** Nominatim requires a User-Agent header:
```python
headers = {
    "User-Agent": "OptiMap-RouteOptimizer/1.0 (contact@yourcompany.com)"
}
```

---

## Minimum Viable Implementation

If you want the absolute quickest implementation:

### 1. Add to requirements.txt
```
httpx  # Already have this
```

### 2. Create geocoding_client.py (Minimal)
```python
import httpx

async def geocode_address(address: str) -> tuple[float, float]:
    """Geocode using Nominatim."""
    url = f"https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "OptiMap/1.0"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        data = response.json()

        if not data:
            raise ValueError(f"Address not found: {address}")

        return float(data[0]["lat"]), float(data[0]["lon"])
```

### 3. Update optimize.py (Add 5 lines)
```python
from app.services.geocoding_client import geocode_address

async def optimize_route(request: OptimizationRequest):
    # Add geocoding
    for stop in request.stops:
        if stop.address and not stop.latitude:
            stop.latitude, stop.longitude = await geocode_address(stop.address)

    # Rest of existing code unchanged
```

**That's it!** Minimal working version in ~50 lines of code.

---

## Next Steps

1. ✅ Review [NEW_TICKETS_ADDRESS_GEOCODING.md](NEW_TICKETS_ADDRESS_GEOCODING.md) for full specifications
2. ✅ Decide on geocoding provider (Nominatim vs. Google Maps)
3. ✅ Implement OMAP-T13 (Geocoding Client)
4. ✅ Implement OMAP-T14 (Location Model)
5. ✅ Implement OMAP-T15 (Endpoint Integration)
6. ✅ Test end-to-end with addresses
7. ✅ Add caching (OMAP-T16) for performance
8. ✅ Update frontend (OMAP-S11) to show geocoding results

---

## Questions?

Refer to:
- **[NEW_TICKETS_ADDRESS_GEOCODING.md](NEW_TICKETS_ADDRESS_GEOCODING.md)** - Full ticket specifications
- **[TICKETS_SUMMARY.md](TICKETS_SUMMARY.md)** - Quick reference
- **Nominatim Docs:** https://nominatim.org/release-docs/latest/api/Search/
- **Google Geocoding Docs:** https://developers.google.com/maps/documentation/geocoding

---

**Quick Start Version:** 1.0
**Last Updated:** 2025-10-12
**Estimated Implementation Time:** 2-3 days backend + 1-2 days frontend = ~1 week total
