# 🗺️ OptiMap: Last-Mile Route Optimization AI

**A high-performance, full-stack platform built to minimize time and distance in last-mile logistics by solving the Vehicle Routing Problem (VRP).**

OptiMap demonstrates a critical product engineering capability: translating a complex algorithmic problem into a tangible, user-friendly, and cost-saving solution. It is built on a modern **decoupled microservices architecture** using FastAPI and React.

## 🚀 Key Features

* **VRP Solver:** Implements the **Vehicle Routing Problem (VRP)** using **Google OR-Tools** to determine the optimal sequence of stops for a single vehicle.
* **Geospatial Integration:** Uses external Routing APIs (e.g., OSRM) to calculate **accurate, real-world road travel times and distances** (the Distance Matrix), a critical input for the VRP algorithm.
* **Intuitive Visualization:** The React frontend displays the input stops and draws the **optimal route line** on an interactive map (e.g., React-Leaflet/Mapbox).
* **Value Quantification:** Provides clear metrics for **Total Distance Saved** and **Total Time Saved** compared to a naive sequential route.
* **Decoupled Architecture:** Built as a scalable, two-part system: a high-speed Python backend and a dedicated JavaScript frontend.

## 🛠️ Technology Stack

| Component | Technology | Role in OptiMap |
| :--- | :--- | :--- |
| **Backend (Algorithm)** | **FastAPI, Python** | Microservice for running optimization and API orchestration. |
| **Optimization Library**| **Google OR-Tools** | Core engine for solving the Traveling Salesperson Problem (TSP/VRP). |
| **Frontend (UX/Viz)**| **React, JavaScript** | Component-based UI for stop input and map rendering. |
| **Mapping** | **React-Leaflet / React-Mapbox-GL**| Library used for displaying and interacting with geographical data. |
| **MLOps/Infra** | **Docker** | Containerization of the FastAPI service for robust, reproducible deployment. |

## 📐 Decoupled Architecture Diagram

The system operates as two independent, containerized services communicating via a REST API, showcasing true product-ready architecture.

```mermaid
graph TD
    A[React Frontend] -->|1. POST /optimize| B(FastAPI Backend);
    B -->|2. Request Distances| C(External Routing API);
    C -->|3. Return Distance Matrix| B;
    B -->|4. Run OR-Tools (VRP Solver)| B;
    B -->|5. Return Optimal Route JSON| A;
    A -- Visualize Route & Metrics --> D[User (Logistics Manager)];
