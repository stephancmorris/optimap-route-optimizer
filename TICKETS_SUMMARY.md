# OptiMap Tickets Summary

## Important Finding

### ✅ Real-world Routing Already Implemented!

Your concern about accounting for streets, one-ways, and navigating around buildings is **already solved**. The existing OSRM integration uses the `/table/v1/driving/` profile which:

- Calculates distances based on actual road networks
- Respects one-way streets and turn restrictions
- Routes around buildings using real OSM road data
- Provides accurate travel times based on road conditions

**No new ticket needed for this!** The system already uses real-world routing, not straight-line distances.

---

## New Tickets for Address-Based Input

### EPIC: OMAP-E6 - Address Management & Geocoding
Enhance location input by supporting address-based input with automatic geocoding.

---

### Stories (2)

**OMAP-S10: Support Address-Based Input with Geocoding**
- Allow users to input addresses instead of lat/lng
- Automatic geocoding before optimization
- Error handling and verification
- **Estimated:** 13 story points

**OMAP-S11: Display Geocoded Address Verification**
- Frontend UI to verify geocoded coordinates
- Table showing address → coordinate mapping
- Manual correction capability
- **Estimated:** 8 story points

---

### Backend Tasks (4 Required + 2 Optional)

#### Required for MVP

**OMAP-T13: Integrate Geocoding Service Client** 🔧
- Create geocoding client (Nominatim or Google Maps)
- Error handling and retry logic
- Rate limiting
- **Time:** 1-2 days
- **Dependencies:** None

**OMAP-T14: Update Location Model** 🔧
- Make lat/lng optional
- Require either address OR coordinates
- Add geocoding metadata fields
- **Time:** 4-6 hours
- **Dependencies:** None

**OMAP-T15: Implement Geocoding in Optimize Endpoint** 🔧
- Add geocoding logic to `/optimize`
- Parallel geocoding for performance
- Error handling and logging
- **Time:** 1-2 days
- **Dependencies:** T13, T14

**OMAP-T16: Implement Geocoding Caching** ⚡
- LRU cache for geocoded addresses
- Cache hit/miss metrics
- Address normalization
- **Time:** 1 day
- **Dependencies:** T13

#### Optional Enhancements

**OMAP-T17: Add Reverse Geocoding** ⭐
- Coordinate → address conversion
- Auto-populate addresses for coordinates-only input
- **Time:** 1 day
- **Dependencies:** T13

**OMAP-T18: Add Address Autocomplete** ⭐
- Address suggestions as user types
- Reduce geocoding errors
- Faster data entry
- **Time:** 2 days
- **Dependencies:** T13

---

## Implementation Order

### Phase 1: Core Geocoding (Sprint 1)
1. **OMAP-T13** - Geocoding Service Client
2. **OMAP-T14** - Location Model Updates
3. **OMAP-T15** - Optimize Endpoint Integration

**Goal:** Address input works end-to-end

### Phase 2: Performance & UX (Sprint 2)
4. **OMAP-T16** - Caching
5. **OMAP-S11** - Frontend Verification UI

**Goal:** Production-ready with good UX

### Phase 3: Enhancements (Optional)
6. **OMAP-T17** - Reverse Geocoding
7. **OMAP-T18** - Address Autocomplete

**Goal:** Premium features

---

## Time Estimates

| Phase | Backend | Frontend | Total |
|-------|---------|----------|-------|
| **MVP** (T13-T16) | 4-5 days | - | 4-5 days |
| **+ Frontend** (S11) | - | 2-3 days | 2-3 days |
| **+ Enhancements** (T17-T18) | 3 days | - | 3 days |
| **Total** | 7-8 days | 2-3 days | **9-11 days** |

---

## Current Tickets Status

### ✅ Completed Tickets

1. ✅ **OMAP-T1** - Setup FastAPI Backend Project Structure
2. ✅ **OMAP-T2** - Configure Google OR-Tools Dependencies
3. ✅ **OMAP-S1** - Submit Stops for Optimization
4. ✅ **OMAP-T3** - Integrate OSRM Routing API Client
5. ✅ **OMAP-S2** - Calculate Real-World Distance Matrix
6. ✅ **OMAP-S3** - Solve Vehicle Routing Problem
7. ✅ **OMAP-S4** - Return Optimized Route to Frontend
8. ✅ **OMAP-T4** - Setup React Frontend Project
9. ✅ **OMAP-S5** - Input Delivery Stops via UI
10. ✅ **OMAP-S6** - Visualize Optimal Route on Map
11. ✅ **OMAP-S7** - Display Route Optimization Metrics
12. ✅ **OMAP-T5** - Dockerize FastAPI Backend Service
13. ✅ **OMAP-T6** - Dockerize React Frontend Service
14. ✅ **OMAP-T7** - Setup Docker Compose Orchestration
15. ✅ **OMAP-T8** - Implement CORS Configuration
16. ✅ **OMAP-S8** - Handle Optimization Errors Gracefully
17. ✅ **OMAP-T9** - Create API Documentation
18. ✅ **OMAP-T10** - Implement Logging and Monitoring

### 🔄 Remaining Original Tickets

19. **OMAP-T11** - Implement Unit Testing Framework
20. **OMAP-S9** - Compare Optimized vs Baseline Routes
21. **OMAP-T12** - Create Project README and Setup Guide

### 🆕 New Tickets (Address/Geocoding)

22. **OMAP-E6** - Address Management & Geocoding (EPIC)
23. **OMAP-S10** - Support Address-Based Input with Geocoding
24. **OMAP-T13** - Integrate Geocoding Service Client
25. **OMAP-T14** - Update Location Model to Support Addresses
26. **OMAP-T15** - Implement Geocoding Logic in Optimize Endpoint
27. **OMAP-T16** - Implement Geocoding Results Caching
28. **OMAP-S11** - Display Geocoded Address Verification (Frontend)
29. **OMAP-T17** - Add Reverse Geocoding Support (Optional)
30. **OMAP-T18** - Add Address Autocomplete Support (Optional)

---

## Recommended Next Steps

### Option 1: Finish Original Tickets First
1. Complete OMAP-T11 (Unit Testing)
2. Complete OMAP-S9 (Baseline Comparison) - *Note: May already be done*
3. Complete OMAP-T12 (README)
4. Then start geocoding features

### Option 2: Start Geocoding Features Now
1. Complete OMAP-T13-T16 (Core geocoding)
2. Complete OMAP-S11 (Frontend verification)
3. Go back to OMAP-T11-T12 (Testing & docs)

### Option 3: Hybrid Approach
1. Complete OMAP-T11 (Unit Testing) - Validate existing code
2. Complete OMAP-T13-T16 (Core geocoding) - Add new features
3. Complete OMAP-T12 (README) - Document everything
4. Optional: T17-T18 (Enhancements)

**My Recommendation:** Option 3 (Hybrid) - Test what you have, add geocoding, then document everything.

---

## Configuration Changes Needed

### New Environment Variables
```bash
# Geocoding Service
GEOCODING_PROVIDER=nominatim
GEOCODING_API_KEY=
GEOCODING_API_URL=https://nominatim.openstreetmap.org
GEOCODING_TIMEOUT_SECONDS=10
GEOCODING_MAX_RETRIES=3

# Geocoding Cache
GEOCODING_CACHE_ENABLED=true
GEOCODING_CACHE_SIZE=10000
GEOCODING_CACHE_TTL_DAYS=30
```

---

## API Changes

### Before (Coordinates Only)
```json
{
  "stops": [
    {"latitude": 40.7128, "longitude": -74.0060},
    {"latitude": 40.7589, "longitude": -73.9851}
  ],
  "depot_index": 0
}
```

### After (Address Support)
```json
{
  "stops": [
    {"address": "123 Main St, New York, NY 10001"},
    {"address": "Times Square, New York, NY"},
    {"latitude": 40.7614, "longitude": -73.9776}
  ],
  "depot_index": 0
}
```

### Response Includes Geocoding
```json
{
  "optimized_route": [
    {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "123 Main St, New York, NY 10001",
      "geocoded": true,
      "geocoding_confidence": 0.95
    }
  ]
}
```

---

## Questions to Consider

1. **Geocoding Provider:** Start with free Nominatim or pay for Google Maps?
2. **Budget:** Monthly budget for geocoding API costs?
3. **International:** Support international addresses in MVP?
4. **Priority:** Finish testing/docs first, or add geocoding first?
5. **Scope:** MVP only, or include optional enhancements (T17-T18)?

---

## Key Documentation

📄 **[NEW_TICKETS_ADDRESS_GEOCODING.md](NEW_TICKETS_ADDRESS_GEOCODING.md)** - Full specification for all new tickets

📄 **[OMAP-T9_COMPLETION_SUMMARY.md](backend/OMAP-T9_COMPLETION_SUMMARY.md)** - API Documentation completion

📄 **[OMAP-T10_COMPLETION_SUMMARY.md](backend/OMAP-T10_COMPLETION_SUMMARY.md)** - Logging implementation completion

---

## Total Project Status

- **Completed:** 18 tickets (5 Epics, 8 Stories, 10 Tasks)
- **Remaining Original:** 3 tickets (1 Story, 2 Tasks)
- **New Tickets:** 9 tickets (1 Epic, 2 Stories, 6 Tasks)
- **Total Project:** 30 tickets

**Completion:** 60% (18/30) of expanded scope, 85% (18/21) of original scope

---

**Last Updated:** 2025-10-12
