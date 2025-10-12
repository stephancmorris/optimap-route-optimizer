# New Tickets: Address Management & Geocoding

## Overview

This document outlines new tickets to enhance OptiMap with address-based input capabilities. These tickets address the need for easier location input by allowing users to provide street addresses instead of manually entering latitude/longitude coordinates.

## Important Note on Existing Features

**Real-world Routing:** ✅ Already Implemented!

The system already accounts for:
- One-way streets
- Turn restrictions
- Road networks and routing around buildings
- Real-world travel times

This is accomplished through the existing OSRM (Open Source Routing Machine) integration, which uses actual road data from OpenStreetMap. The `/table/v1/driving/` profile calculates distances based on drivable roads, not straight-line distance.

**What's Missing:** Address-to-Coordinate Conversion (Geocoding)

Currently, users must manually provide latitude/longitude. The new tickets below add geocoding to convert addresses to coordinates automatically.

---

## EPIC: <OMAP-E6> - Address Management & Geocoding

**Description:** Enhance location input capabilities by supporting address-based input with automatic geocoding, reducing manual coordinate entry and improving user experience.

**Business Value:**
- Dramatically improve user experience by eliminating manual coordinate lookup
- Reduce data entry errors
- Make the system accessible to non-technical users
- Speed up route creation workflow

**Dependencies:** None (new epic)

**Estimated Timeline:** 3-4 sprints

**Success Metrics:**
- 80%+ of users use address input instead of coordinates
- Average time to create route reduced by 50%
- Geocoding success rate >95%
- Geocoding API cost under budget

---

## STORY: <OMAP-S10> - Support Address-Based Input with Geocoding

**EPIC Link:** OMAP-E6

**Priority:** High

**Description:**
As a logistics manager, I want to input delivery stops using street addresses instead of coordinates, so that I can quickly create routes without looking up latitude/longitude values.

**User Story:**
```
GIVEN I am planning a delivery route
WHEN I enter stop addresses like "123 Main St, New York, NY 10001"
THEN the system automatically converts them to coordinates
AND I can see the geocoded coordinates for verification
AND the optimization proceeds with the correct locations
```

**Acceptance Criteria:**

1. **API accepts address input**
   - `Location` model accepts either (address) OR (latitude + longitude)
   - Users can provide mixed input (some addresses, some coordinates)
   - Backward compatible with existing coordinate-only requests

2. **Automatic geocoding**
   - System automatically geocodes addresses to coordinates
   - Geocoding happens before distance matrix calculation
   - Multiple addresses geocoded in parallel for performance
   - Geocoding errors don't crash the entire request

3. **Error handling**
   - Clear error messages for addresses that can't be geocoded
   - Suggest corrections for ambiguous addresses
   - Validation for missing/incomplete addresses
   - HTTP 400 with details for geocoding failures

4. **Response includes verification**
   - Response includes both original address and geocoded coordinates
   - Geocoded flag indicates which locations were auto-converted
   - Confidence score included where available

5. **Performance**
   - Geocoding doesn't add more than 2s to request time
   - Caching prevents redundant API calls
   - Timeout handling for slow geocoding services

6. **Configuration**
   - Geocoding service configurable via environment variables
   - Support multiple providers (Nominatim, Google Maps, etc.)
   - Rate limiting configurable per provider

**Technical Requirements:**
- Geocoding service integration
- Modified `Location` Pydantic model
- Updated `/optimize` endpoint logic
- Caching layer for geocoded addresses
- Logging for geocoding operations

**Definition of Done:**
- [ ] Address-based input works in API
- [ ] Geocoding integrated with chosen provider
- [ ] Error handling tested for all failure scenarios
- [ ] Caching implemented and tested
- [ ] API documentation updated with address examples
- [ ] Integration tests passing
- [ ] Performance meets requirements (<2s overhead)

**Dependencies:**
- OMAP-T13: Geocoding service client
- OMAP-T14: Updated Location model
- OMAP-T15: Endpoint implementation

**Estimated Story Points:** 13

---

## TASK: <OMAP-T13> - Integrate Geocoding Service Client

**EPIC Link:** OMAP-E6
**Story Link:** OMAP-S10

**Priority:** High

**Description:**
Create a geocoding client module to convert addresses to latitude/longitude coordinates using an external geocoding service.

**Steps:**

1. **Research and select geocoding service**
   - Compare Nominatim (free), Google Maps API, Mapbox
   - Consider: cost, accuracy, rate limits, reliability
   - **Recommendation:** Start with Nominatim, add Google as option
   - Document decision in ADR (Architecture Decision Record)

2. **Create geocoding client module**
   - File: `app/services/geocoding_client.py`
   - Class: `GeocodingClient`
   - Methods:
     - `geocode_address(address: str) -> Optional[Tuple[float, float]]`
     - `geocode_batch(addresses: List[str]) -> List[Optional[Tuple[float, float]]]`
     - `reverse_geocode(lat: float, lng: float) -> Optional[str]`

3. **Implement address-to-coordinates conversion**
   - Parse address string
   - Make HTTP request to geocoding API
   - Extract latitude/longitude from response
   - Return coordinates or None if not found

4. **Add error handling**
   - Custom exceptions: `GeocodingError`, `GeocodingTimeoutError`
   - Handle HTTP errors (4xx, 5xx)
   - Handle malformed responses
   - Handle rate limiting (429 errors)

5. **Add retry logic and rate limiting**
   - Use tenacity for retries (same as OSRM client)
   - Exponential backoff for rate limit errors
   - Configurable max retries
   - Request rate limiting to respect provider limits

6. **Add caching layer**
   - In-memory LRU cache using `functools.lru_cache` or `cachetools`
   - Cache key: normalized address string
   - TTL: 30 days (addresses don't change often)
   - Cache size: 10,000 addresses

7. **Configure via environment variables**
   - `GEOCODING_PROVIDER`: nominatim, google, mapbox
   - `GEOCODING_API_KEY`: API key (if required)
   - `GEOCODING_API_URL`: Base URL for service
   - `GEOCODING_TIMEOUT_SECONDS`: Request timeout
   - `GEOCODING_MAX_RETRIES`: Max retry attempts

8. **Add comprehensive logging**
   - Log geocoding requests with address
   - Log response time and success/failure
   - Log cache hits/misses
   - Log rate limit encounters

**Example Implementation:**

```python
class GeocodingClient:
    """Client for address geocoding."""

    def __init__(
        self,
        provider: str = "nominatim",
        api_key: Optional[str] = None,
        base_url: str = "https://nominatim.openstreetmap.org",
        timeout_seconds: float = 10.0
    ):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    @lru_cache(maxsize=10000)
    async def geocode_address(
        self,
        address: str
    ) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates."""
        # Implementation
        pass
```

**Testing Requirements:**
- Unit tests for successful geocoding
- Unit tests for error handling
- Unit tests for caching behavior
- Mock external API calls in tests
- Integration test with real geocoding service

**Files to Create:**
- `app/services/geocoding_client.py` (~300 lines)
- `app/services/tests/test_geocoding_client.py` (~200 lines)

**Files to Modify:**
- `app/config/settings.py` (add geocoding config)
- `backend/requirements.txt` (add cachetools if needed)

**Estimated Time:** 1-2 days

**Dependencies:** None

**Definition of Done:**
- [ ] Geocoding client created with Nominatim support
- [ ] Error handling implemented
- [ ] Retry logic implemented
- [ ] Caching implemented
- [ ] Configuration via environment variables
- [ ] Comprehensive logging
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration test with Nominatim passing
- [ ] Documentation in docstrings

---

## TASK: <OMAP-T14> - Update Location Model to Support Addresses

**EPIC Link:** OMAP-E6
**Story Link:** OMAP-S10

**Priority:** High

**Description:**
Update the `Location` Pydantic model to support address-based input, making latitude/longitude optional when an address is provided.

**Steps:**

1. **Update Location model fields**
   - Make `latitude` and `longitude` optional (use `Optional[float]`)
   - Keep `address` field but make it more prominent
   - Add `original_address` field to preserve user input
   - Add `geocoded` boolean flag (default: False)
   - Add `geocoding_confidence` optional float (0.0-1.0)

2. **Add custom validation**
   - Require either (address) OR (latitude + longitude)
   - Reject requests with neither
   - Reject requests with invalid combinations
   - Validate address is non-empty string if provided

3. **Update Pydantic validators**
   ```python
   @model_validator(mode='after')
   def validate_location(self) -> 'Location':
       """Ensure either address or coordinates are provided."""
       has_coords = self.latitude is not None and self.longitude is not None
       has_address = self.address is not None and self.address.strip()

       if not has_coords and not has_address:
           raise ValueError("Must provide either address or coordinates")

       return self
   ```

4. **Add helper methods**
   - `has_coordinates() -> bool`
   - `needs_geocoding() -> bool`
   - `set_geocoded_coordinates(lat: float, lng: float, confidence: float = None)`

5. **Update OpenAPI schema examples**
   - Add example with address only
   - Add example with coordinates only
   - Add example with both address and coordinates
   - Update API documentation

6. **Ensure backward compatibility**
   - Existing coordinate-only requests still work
   - No breaking changes to API contract
   - Add migration guide if needed

**Example Updated Model:**

```python
class Location(BaseModel):
    """Represents a geographical location with coordinates and/or address."""

    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Street address for geocoding")
    original_address: Optional[str] = Field(None, description="Original address before normalization")
    geocoded: bool = Field(False, description="Whether coordinates were auto-geocoded")
    geocoding_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Geocoding confidence score")

    @model_validator(mode='after')
    def validate_location(self) -> 'Location':
        """Ensure either address or coordinates are provided."""
        has_coords = self.latitude is not None and self.longitude is not None
        has_address = self.address is not None and len(self.address.strip()) > 0

        if not has_coords and not has_address:
            raise ValueError("Must provide either 'address' or both 'latitude' and 'longitude'")

        return self

    def has_coordinates(self) -> bool:
        """Check if location has coordinates."""
        return self.latitude is not None and self.longitude is not None

    def needs_geocoding(self) -> bool:
        """Check if location needs geocoding."""
        return not self.has_coordinates() and self.address is not None

    def set_geocoded_coordinates(self, lat: float, lng: float, confidence: float = None):
        """Set coordinates from geocoding result."""
        self.latitude = lat
        self.longitude = lng
        self.geocoded = True
        self.original_address = self.address
        if confidence is not None:
            self.geocoding_confidence = confidence

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "address": "1600 Amphitheatre Parkway, Mountain View, CA 94043",
                    "description": "Address-based input (will be geocoded)"
                },
                {
                    "latitude": 37.4224764,
                    "longitude": -122.0842499,
                    "address": "Google Headquarters",
                    "description": "Coordinate-based input with optional address"
                }
            ]
        }
```

**Testing Requirements:**
- Test address-only input validates successfully
- Test coordinates-only input validates successfully
- Test mixed input validates successfully
- Test missing both address and coordinates fails validation
- Test invalid combinations fail validation
- Test helper methods work correctly
- Test backward compatibility with existing API calls

**Files to Modify:**
- `app/models/route.py` (~50 lines changed)
- Update tests in `app/tests/test_models.py` (if exists)

**Estimated Time:** 4-6 hours

**Dependencies:** None

**Definition of Done:**
- [ ] Location model updated with optional lat/lng
- [ ] Custom validation implemented
- [ ] Helper methods added
- [ ] OpenAPI examples updated
- [ ] Unit tests passing
- [ ] Backward compatibility verified
- [ ] API documentation updated

---

## TASK: <OMAP-T15> - Implement Geocoding Logic in Optimize Endpoint

**EPIC Link:** OMAP-E6
**Story Link:** OMAP-S10

**Priority:** High

**Description:**
Update the `/optimize` endpoint to handle address-based input by geocoding addresses to coordinates before distance matrix calculation.

**Steps:**

1. **Update `/optimize` endpoint to handle addresses**
   - Import geocoding client
   - Check which locations need geocoding
   - Geocode addresses before OSRM call

2. **Add geocoding step before distance matrix**
   ```python
   # Geocode any addresses that don't have coordinates
   locations_to_geocode = [loc for loc in request.stops if loc.needs_geocoding()]

   if locations_to_geocode:
       logger.info(f"Geocoding {len(locations_to_geocode)} addresses")
       await geocode_locations(locations_to_geocode, geocoding_client)
   ```

3. **Geocode addresses in parallel for performance**
   - Use `asyncio.gather()` to geocode multiple addresses simultaneously
   - Don't block on serial geocoding
   - Maintain order of locations

4. **Handle geocoding failures gracefully**
   - Catch geocoding errors per location
   - Return 400 with details for failed geocoding
   - Include which addresses failed and why
   - Suggest corrections if available

5. **Return geocoded coordinates in response**
   - Include geocoded coordinates in response
   - Flag which locations were geocoded
   - Include confidence scores if available
   - Allow user verification

6. **Add logging for geocoding operations**
   - Log number of addresses to geocode
   - Log geocoding time
   - Log success/failure per address
   - Log cache hit rate

7. **Add validation to prevent ambiguous addresses**
   - Warn if geocoding confidence is low (<0.7)
   - Suggest more specific addresses
   - Log ambiguous geocoding results

**Example Implementation:**

```python
async def optimize_route(request: OptimizationRequest) -> OptimizationResponse:
    """Optimize route with address geocoding support."""

    try:
        # Geocode any addresses that don't have coordinates
        locations_to_geocode = [
            (i, stop) for i, stop in enumerate(request.stops)
            if stop.needs_geocoding()
        ]

        if locations_to_geocode:
            logger.info(f"Geocoding {len(locations_to_geocode)} addresses")

            geocoding_start = time.time()

            # Geocode in parallel
            geocoding_tasks = [
                geocode_single_location(stop, geocoding_client)
                for _, stop in locations_to_geocode
            ]

            geocoding_results = await asyncio.gather(
                *geocoding_tasks,
                return_exceptions=True
            )

            geocoding_time = (time.time() - geocoding_start) * 1000

            # Check for failures
            failed_geocodes = []
            for (idx, stop), result in zip(locations_to_geocode, geocoding_results):
                if isinstance(result, Exception) or result is None:
                    failed_geocodes.append({
                        "index": idx,
                        "address": stop.address,
                        "error": str(result) if isinstance(result, Exception) else "Address not found"
                    })

            if failed_geocodes:
                error = create_error_response(
                    code=ErrorCode.GEOCODING_FAILED,
                    message=f"Failed to geocode {len(failed_geocodes)} address(es)",
                    details=[ErrorDetail(
                        field=f"stops[{f['index']}].address",
                        message=f["error"],
                        value=f["address"]
                    ) for f in failed_geocodes]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump()
                )

            logger.info(
                f"Geocoding completed: {len(locations_to_geocode)} addresses, "
                f"time={geocoding_time:.0f}ms"
            )

        # Validate all stops now have coordinates
        for i, stop in enumerate(request.stops):
            if not stop.has_coordinates():
                raise ValueError(f"Stop {i} missing coordinates after geocoding")

        # Continue with existing optimization logic
        # ... rest of endpoint implementation
```

**Error Handling:**
- New error code: `GEOCODING_FAILED`
- New error code: `GEOCODING_TIMEOUT`
- New error code: `GEOCODING_AMBIGUOUS`
- Return 400 with details for geocoding failures
- Include suggestions in error response

**Testing Requirements:**
- Test address-only input end-to-end
- Test mixed address/coordinate input
- Test geocoding failure handling
- Test parallel geocoding performance
- Test error messages are helpful
- Integration test with real geocoding service

**Files to Modify:**
- `app/routers/optimize.py` (~100 lines added)
- `app/models/errors.py` (add new error codes)

**Files to Create:**
- Helper function file if needed

**Estimated Time:** 1-2 days

**Dependencies:**
- OMAP-T13 (Geocoding client must exist)
- OMAP-T14 (Location model must be updated)

**Definition of Done:**
- [ ] Geocoding logic integrated into `/optimize` endpoint
- [ ] Parallel geocoding implemented
- [ ] Error handling implemented
- [ ] Geocoded coordinates returned in response
- [ ] Logging implemented
- [ ] Integration tests passing
- [ ] Performance meets requirements (<2s overhead)
- [ ] API documentation updated with address examples

---

## TASK: <OMAP-T16> - Implement Geocoding Results Caching

**EPIC Link:** OMAP-E6

**Priority:** Medium

**Description:**
Implement a caching layer for geocoded addresses to minimize redundant API calls, reduce costs, and improve performance.

**Steps:**

1. **Design caching strategy**
   - In-memory LRU cache for simplicity (MVP)
   - Redis for production/distributed systems (future)
   - Cache key: normalized address string
   - Cache value: (latitude, longitude, confidence, timestamp)

2. **Implement cache key generation**
   - Normalize addresses for consistent caching:
     - Convert to lowercase
     - Remove extra whitespace
     - Standardize abbreviations (St → Street, etc.)
     - Remove punctuation variations
   - Hash for compact keys if needed

3. **Add cache lookup before geocoding**
   ```python
   def get_cached_coordinates(address: str) -> Optional[Tuple[float, float]]:
       """Check cache before geocoding."""
       cache_key = normalize_address(address)
       return geocoding_cache.get(cache_key)
   ```

4. **Store geocoding results with TTL**
   - TTL: 30 days (addresses rarely change)
   - Update cache after successful geocoding
   - Don't cache failed geocoding attempts

5. **Add cache hit/miss metrics**
   - Log cache hit rate
   - Track cache size
   - Monitor cache effectiveness
   - Include in `/metrics` endpoint (future)

6. **Configure cache via environment variables**
   - `GEOCODING_CACHE_ENABLED`: true/false
   - `GEOCODING_CACHE_SIZE`: max entries (default: 10000)
   - `GEOCODING_CACHE_TTL_DAYS`: TTL in days (default: 30)

7. **Add cache clearing mechanism**
   - Clear cache on server restart (in-memory)
   - Add admin endpoint to clear cache (future)
   - Useful for development/testing

8. **Implement cache warming (optional)**
   - Pre-populate cache with common addresses
   - Load from file on startup
   - Useful for production deployments

**Example Implementation:**

```python
from cachetools import TTLCache
from datetime import timedelta

class GeocodingCache:
    """Cache for geocoding results."""

    def __init__(self, maxsize: int = 10000, ttl_days: int = 30):
        ttl_seconds = timedelta(days=ttl_days).total_seconds()
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self.hits = 0
        self.misses = 0

    def get(self, address: str) -> Optional[Tuple[float, float]]:
        """Get cached coordinates."""
        key = self._normalize_address(address)
        result = self.cache.get(key)

        if result:
            self.hits += 1
            logger.debug(f"Cache hit for address: {address}")
        else:
            self.misses += 1
            logger.debug(f"Cache miss for address: {address}")

        return result

    def set(self, address: str, lat: float, lng: float):
        """Cache geocoding result."""
        key = self._normalize_address(address)
        self.cache[key] = (lat, lng)
        logger.debug(f"Cached coordinates for address: {address}")

    def _normalize_address(self, address: str) -> str:
        """Normalize address for consistent caching."""
        normalized = address.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)  # Remove extra spaces
        # Add more normalization as needed
        return normalized

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2)
        }
```

**Testing Requirements:**
- Test cache hit for previously geocoded address
- Test cache miss for new address
- Test cache expiration after TTL
- Test cache size limit (LRU eviction)
- Test address normalization consistency
- Test cache statistics accuracy

**Files to Create:**
- `app/utils/geocoding_cache.py` (~150 lines)

**Files to Modify:**
- `app/services/geocoding_client.py` (integrate cache)
- `app/config/settings.py` (add cache config)

**Dependencies:**
- `cachetools` Python package

**Estimated Time:** 1 day

**Definition of Done:**
- [ ] Caching layer implemented
- [ ] Address normalization working
- [ ] Cache hit/miss logging
- [ ] Configuration via environment variables
- [ ] Unit tests passing
- [ ] Cache statistics available
- [ ] Documentation updated

---

## STORY: <OMAP-S11> - Display Geocoded Address Verification (Frontend)

**EPIC Link:** OMAP-E6

**Priority:** Medium

**Description:**
As a logistics manager, I want to see the geocoded coordinates for my addresses, so that I can verify the system interpreted my addresses correctly before optimization.

**User Story:**
```
GIVEN I have entered addresses for my delivery stops
WHEN the optimization completes
THEN I see a table showing address → coordinate mappings
AND I can verify the geocoded locations are correct
AND I can see which addresses had low confidence scores
AND I can manually adjust coordinates if needed
```

**Acceptance Criteria:**

1. **Display geocoding results**
   - Show table with: Original Address, Geocoded Lat/Lng, Confidence Score
   - Highlight addresses with low confidence (<0.7)
   - Show geocoded vs. manually-entered stops differently

2. **Visual verification**
   - Show markers on map for geocoded locations
   - Different marker color for geocoded vs. manual
   - Click marker to see address details

3. **Manual correction capability**
   - Allow editing coordinates if geocoding is wrong
   - Save corrections for future use
   - Re-optimize with corrected coordinates

4. **Error handling**
   - Show clear messages for failed geocoding
   - Suggest more specific addresses
   - Allow retry with edited address

5. **UX polish**
   - Loading state while geocoding
   - Progress indicator for batch geocoding
   - Success/warning indicators

**Technical Requirements:**
- React component for geocoding verification table
- Integration with map component
- State management for coordinate corrections
- API integration for geocoding results

**Dependencies:**
- OMAP-T15 (Backend must return geocoding data)

**Estimated Story Points:** 8

---

## OPTIONAL ENHANCEMENT TASKS

### TASK: <OMAP-T17> - Add Reverse Geocoding Support

**EPIC Link:** OMAP-E6

**Priority:** Low

**Description:**
Implement coordinate-to-address conversion (reverse geocoding) to automatically populate address fields when only coordinates are provided.

**Steps:**
1. Add `reverse_geocode()` method to geocoding client
2. Update `/optimize` endpoint to reverse geocode coordinate-only locations
3. Create `/reverse-geocode` API endpoint for manual lookups
4. Update response to include reverse-geocoded addresses
5. Add tests for reverse geocoding

**Business Value:**
- Improve data completeness
- Better for reporting and exports
- Helps users identify locations

**Estimated Time:** 1 day

---

### TASK: <OMAP-T18> - Add Address Autocomplete Support

**EPIC Link:** OMAP-E6

**Priority:** Low

**Description:**
Create an address autocomplete endpoint to provide address suggestions as users type, improving UX and reducing geocoding errors.

**Steps:**
1. Implement geocoding autocomplete API integration
2. Create `/autocomplete` endpoint
3. Return suggestion list with metadata
4. Add rate limiting for autocomplete
5. Frontend integration with input field
6. Debounce user input

**Business Value:**
- Faster data entry
- Fewer geocoding errors
- Better UX
- Reduced geocoding API costs (correct first time)

**Estimated Time:** 2 days

---

## Implementation Roadmap

### Phase 1: Core Geocoding (Sprint 1)
- OMAP-T13: Integrate Geocoding Service Client
- OMAP-T14: Update Location Model
- OMAP-T15: Implement Geocoding in Optimize Endpoint

**Goal:** Basic address input working end-to-end

### Phase 2: Performance & UX (Sprint 2)
- OMAP-T16: Implement Caching
- OMAP-S11: Frontend Verification UI

**Goal:** Production-ready with good performance and UX

### Phase 3: Enhancements (Sprint 3 - Optional)
- OMAP-T17: Reverse Geocoding
- OMAP-T18: Address Autocomplete

**Goal:** Premium features for power users

---

## Testing Strategy

### Unit Tests
- Geocoding client with mocked API
- Location model validation
- Cache implementation
- Address normalization

### Integration Tests
- End-to-end geocoding flow
- Real geocoding API calls (limited)
- Error scenarios
- Performance benchmarks

### Manual Testing
- Test with common addresses
- Test with international addresses
- Test with ambiguous addresses
- Test with invalid addresses
- Test mixed coordinate/address input

---

## Configuration Reference

### New Environment Variables

```bash
# Geocoding Service Configuration
GEOCODING_PROVIDER=nominatim              # nominatim, google, mapbox
GEOCODING_API_KEY=                        # API key (if required)
GEOCODING_API_URL=https://nominatim.openstreetmap.org
GEOCODING_TIMEOUT_SECONDS=10
GEOCODING_MAX_RETRIES=3

# Geocoding Cache Configuration
GEOCODING_CACHE_ENABLED=true
GEOCODING_CACHE_SIZE=10000
GEOCODING_CACHE_TTL_DAYS=30
```

---

## Geocoding Provider Comparison

| Provider | Cost | Accuracy | Rate Limit | API Key | Recommendation |
|----------|------|----------|------------|---------|----------------|
| **Nominatim (OSM)** | Free | Good | 1 req/sec | No | ✅ Start here (MVP) |
| **Google Maps** | $5/1000 reqs | Excellent | 50 req/sec | Yes | Production upgrade |
| **Mapbox** | $0.50/1000 reqs | Very Good | 600 req/min | Yes | Good alternative |
| **Azure Maps** | $0.50/1000 reqs | Very Good | 50 req/sec | Yes | Enterprise option |

**MVP Recommendation:** Nominatim (free, no API key, good for development and low-volume production)

**Production Recommendation:** Google Maps or Mapbox (better accuracy, higher rate limits, worth the cost for production use)

---

## Success Metrics

### Technical Metrics
- Geocoding success rate: >95%
- Geocoding response time: <1s p95
- Cache hit rate: >70% after warm-up
- API error rate: <1%

### Business Metrics
- % of users using address input: >80%
- Average time to create route: -50%
- Data entry errors: -60%
- User satisfaction score: +20%

### Cost Metrics
- Geocoding API costs: <$50/month (assuming 10k requests)
- Cache savings: >50% reduction in API calls

---

## Risk Management

### Risk: Geocoding API Unreliable
**Mitigation:**
- Implement fallback to manual coordinate entry
- Add retry logic with exponential backoff
- Consider multiple provider support

### Risk: Geocoding Costs Exceed Budget
**Mitigation:**
- Implement aggressive caching
- Rate limit user requests
- Use free tier (Nominatim) for non-critical
- Monitor costs closely

### Risk: Geocoding Accuracy Issues
**Mitigation:**
- Always show geocoded coordinates for verification
- Allow manual correction
- Log low-confidence results for review
- Prompt user for more specific addresses

### Risk: Performance Impact
**Mitigation:**
- Parallel geocoding for multiple addresses
- Caching layer to minimize API calls
- Timeout protection (10s max)
- Async implementation

---

## Future Enhancements (Not in Current Scope)

- **Bulk Address Import:** CSV upload with batch geocoding
- **Address Validation:** Pre-validate before geocoding
- **International Support:** Better handling of international addresses
- **POI Search:** Search by point of interest (e.g., "Starbucks in Manhattan")
- **Address Suggestions:** Smart suggestions based on user history
- **Offline Geocoding:** Self-hosted Nominatim instance
- **Multi-Provider:** Automatic failover between geocoding providers

---

## Questions for Product Owner

1. **Geocoding Provider:** OK to start with free Nominatim, upgrade to Google Maps later?
2. **Cost Budget:** What's the monthly budget for geocoding API costs?
3. **International:** Do we need to support international addresses in MVP?
4. **Manual Override:** Should users be able to override geocoded coordinates?
5. **Batch Size:** What's the maximum number of addresses per request?
6. **Confidence Threshold:** What confidence score should trigger warnings?

---

## Summary

### New Epic: 1
- OMAP-E6: Address Management & Geocoding

### New Stories: 2
- OMAP-S10: Support Address-Based Input with Geocoding (Backend)
- OMAP-S11: Display Geocoded Address Verification (Frontend)

### New Tasks: 6
- OMAP-T13: Integrate Geocoding Service Client (1-2 days)
- OMAP-T14: Update Location Model (4-6 hours)
- OMAP-T15: Implement Geocoding in Optimize Endpoint (1-2 days)
- OMAP-T16: Implement Geocoding Caching (1 day)
- OMAP-T17: Add Reverse Geocoding (Optional, 1 day)
- OMAP-T18: Add Address Autocomplete (Optional, 2 days)

### Total Estimated Time
- **MVP (T13-T16):** 4-5 days backend + 2-3 days frontend = ~1-1.5 sprints
- **With Enhancements (T17-T18):** +3 days = ~2 sprints total

### Priority Order for Implementation
1. OMAP-T13 (Geocoding Client) - Foundation
2. OMAP-T14 (Location Model) - API Contract
3. OMAP-T15 (Endpoint Logic) - Core Feature
4. OMAP-T16 (Caching) - Performance
5. OMAP-S11 (Frontend UI) - UX
6. OMAP-T17/T18 (Enhancements) - Optional Polish

---

**Document Version:** 1.0
**Last Updated:** 2025-10-12
**Author:** Claude (AI Assistant)
**Status:** Ready for Review & Prioritization
