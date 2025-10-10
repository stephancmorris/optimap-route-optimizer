/**
 * API service for communicating with OptiMap backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Extract user-friendly error message from API error response
 * @param {Object} errorDetail - Error detail from API
 * @returns {string} User-friendly error message
 */
function extractErrorMessage(errorDetail) {
  // Handle structured error responses
  if (errorDetail && typeof errorDetail === 'object') {
    if (errorDetail.message) {
      let message = errorDetail.message;

      // Add suggestion if available
      if (errorDetail.suggestion) {
        message += `. ${errorDetail.suggestion}`;
      }

      return message;
    }

    // Handle legacy string detail
    if (typeof errorDetail === 'string') {
      return errorDetail;
    }
  }

  return 'An unexpected error occurred';
}

/**
 * Optimize route for given stops
 * @param {Array} stops - Array of location objects with latitude, longitude, and optional address
 * @param {number} depotIndex - Index of depot/starting location
 * @returns {Promise} Optimization response
 * @throws {Error} With user-friendly message from backend
 */
export async function optimizeRoute(stops, depotIndex = 0) {
  try {
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
      const errorData = await response.json();
      const errorMessage = extractErrorMessage(errorData.detail);

      const error = new Error(errorMessage);
      error.code = errorData.detail?.code;
      error.details = errorData.detail?.details;
      error.statusCode = response.status;

      throw error;
    }

    return response.json();
  } catch (error) {
    // Re-throw with better message if network error
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to the server. Please check your connection.');
    }
    throw error;
  }
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
