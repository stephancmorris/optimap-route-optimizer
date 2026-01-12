# 🗺️ OptiMap: Last-Mile Route Optimization Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-85%2B%20passing-success.svg)](backend/tests/)
[![Coverage](https://img.shields.io/badge/Coverage-90%25+-brightgreen.svg)](backend/htmlcov/)

**A high-performance, full-stack platform that minimizes time and distance in last-mile logistics by solving the Vehicle Routing Problem (VRP).**

OptiMap demonstrates critical product engineering capabilities: translating complex algorithmic problems into tangible, user-friendly, and cost-saving solutions. Built on a modern **decoupled microservices architecture** using FastAPI and React.


## Key Features

### Optimap Core Capabilities

* **🎯 VRP Solver** - Implements the **Vehicle Routing Problem (VRP)** using **Google OR-Tools** to determine the optimal sequence of stops for delivery vehicles
* **🌍 Real-World Routing** - Integrates with **OSRM** (Open Source Routing Machine) for accurate, road-based travel times and distances (respects one-way streets, turn restrictions)
* **📍 Address Geocoding** - Enter street addresses instead of coordinates with automatic geocoding via **Nominatim** (OpenStreetMap), including smart caching and parallel processing
* **📊 Quantified Savings** - Clear metrics showing **distance saved**, **time saved**, and **percentage improvements** compared to sequential routes
* **🗺️ Interactive Visualization** - Modern React frontend with **Leaflet/Mapbox** displaying optimized routes on interactive maps
* **⚡ High Performance** - Optimizes routes for up to 100 stops in under 5 seconds
* **🔒 Production Ready** - Comprehensive error handling, logging, monitoring, and 90%+ test coverage
* **🏠 Address-First Input** - Modern UI with toggle between address and coordinate input modes
* **✨ Modern Design System** - Gradients, animations, shadows, and micro-interactions throughout
* **🎨 Geocoding Indicators** - Visual badges showing which locations were auto-geocoded vs. manual
* **⚡ Smart Caching** - 30-day TTL cache for geocoding results with address normalization
* **🔄 Parallel Geocoding** - Multiple addresses geocoded simultaneously using async/await
* **📝 Comprehensive API Documentation** - Auto-generated OpenAPI docs with Swagger UI and ReDoc
* **📊 Structured Logging** - Request tracing, performance metrics, and error tracking
* **✅ Robust Testing** - 85+ unit and integration tests with pytest
* **🐳 Docker Support** - Containerized deployment with Docker Compose
* **🛡️ Error Handling** - Graceful handling of timeouts, invalid inputs, and service failures
* **🔍 CORS Configuration** - Secure cross-origin resource sharing for frontend/backend communication

## 📐 Architecture

The system operates as two independent, containerized services communicating via REST API.

```mermaid
graph TD
    A[React Frontend<br/>Port 3000] -->|HTTP Request| B(FastAPI Backend<br/>Port 8000)
    B -->|1. Geocode Addresses| G[Nominatim API<br/>Address → Coordinates]
    G -->|2. Return coordinates| B
    B -->|3. Calculate Distance Matrix| C[OSRM API<br/>Real-world routing]
    C -->|4. Return distances/durations| B
    B -->|5. Solve VRP| D[OR-Tools Solver]
    D -->|6. Return optimal route| B
    B -->|7. Compare with baseline| B
    B -->|8. JSON Response| A
    A -->|9. Visualize route| E[Interactive Map]
    A -->|10. Display metrics| F[Savings Dashboard]

    style A fill:#61DAFB
    style B fill:#009688
    style C fill:#FF6B6B
    style D fill:#4CAF50
    style E fill:#FFB300
    style F fill:#9C27B0
    style G fill:#34A853
```

### Request Flow

1. **User Input** - User enters delivery stops (addresses or coordinates) via React frontend
2. **API Request** - Frontend sends POST request to `/optimize` endpoint
3. **Geocoding** - Backend geocodes any address-only stops using Nominatim (with caching)
4. **Distance Calculation** - Backend calls OSRM to get real-world distance matrix
5. **VRP Solving** - OR-Tools finds optimal visit sequence
6. **Baseline Comparison** - System calculates naive sequential route for comparison
7. **Response** - Backend returns optimized route with savings metrics and geocoded coordinates
8. **Visualization** - Frontend displays route on map with metrics dashboard

[⬆ Back to Top](#-optimap-last-mile-route-optimization-platform)

</div>
