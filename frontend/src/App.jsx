import { useState } from 'react';
import StopInput from './components/StopInput';
import StopList from './components/StopList';
import RouteMap from './components/RouteMap';
import { optimizeRoute } from './services/api';
import './App.css';

function App() {
  const [stops, setStops] = useState([]);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [error, setError] = useState(null);

  const handleAddStop = (stop) => {
    setStops([...stops, stop]);
    setError(null);
  };

  const handleRemoveStop = (index) => {
    setStops(stops.filter((_, i) => i !== index));
    setOptimizationResult(null);
    setError(null);
  };

  const handleOptimize = async () => {
    setIsOptimizing(true);
    setError(null);

    try {
      const result = await optimizeRoute(stops, 0);
      setOptimizationResult(result);
    } catch (err) {
      setError(err.message || 'Failed to optimize route');
      console.error('Optimization error:', err);
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🗺️ OptiMap</h1>
        <p>Last-Mile Route Optimization</p>
      </header>

      <main className="app-main">
        <div className="sidebar">
          <StopInput onAddStop={handleAddStop} />
          <StopList
            stops={stops}
            onRemoveStop={handleRemoveStop}
            onOptimize={handleOptimize}
            isOptimizing={isOptimizing}
          />

          {error && (
            <div className="error-banner">
              <strong>Error:</strong> {error}
            </div>
          )}

          {optimizationResult && (
            <div className="results">
              <h3>Optimization Results</h3>
              <div className="metric">
                <span className="label">Distance Saved:</span>
                <span className="value">
                  {(optimizationResult.distance_saved_meters / 1000).toFixed(2)} km (
                  {optimizationResult.distance_saved_percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="metric">
                <span className="label">Time Saved:</span>
                <span className="value">
                  {(optimizationResult.time_saved_seconds / 60).toFixed(1)} min (
                  {optimizationResult.time_saved_percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="metric-detail">
                <div>
                  <strong>Optimized:</strong> {(optimizationResult.optimized_metrics.total_distance_meters / 1000).toFixed(2)} km,{' '}
                  {(optimizationResult.optimized_metrics.total_time_seconds / 60).toFixed(1)} min
                </div>
                <div>
                  <strong>Baseline:</strong> {(optimizationResult.baseline_metrics.total_distance_meters / 1000).toFixed(2)} km,{' '}
                  {(optimizationResult.baseline_metrics.total_time_seconds / 60).toFixed(1)} min
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="map-container">
          <RouteMap
            stops={stops}
            optimizedRoute={optimizationResult?.optimized_route}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
