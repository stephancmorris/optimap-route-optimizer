/**
 * API service for communicating with OptiMap backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Optimize route for given stops
 * @param {Array} stops - Array of location objects with latitude, longitude, and optional address
 * @param {number} depotIndex - Index of depot/starting location
 * @returns {Promise} Optimization response
 */
export async function optimizeRoute(stops, depotIndex = 0) {
  const response = await fetch(`${API_BASE_URL}/optimize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      stops,
      depot_index: depotIndex,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Optimization failed');
  }

  return response.json();
}

/**
 * Check backend health status
 * @returns {Promise} Health status
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('Backend health check failed');
  }
  return response.json();
}
