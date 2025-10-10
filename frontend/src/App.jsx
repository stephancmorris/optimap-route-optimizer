import { useState } from 'react';
import StopInput from './components/StopInput';
import StopList from './components/StopList';
import RouteMap from './components/RouteMap';
import MetricsDisplay from './components/MetricsDisplay';
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
              <strong>⚠️ Error</strong>
              <div className="error-banner-message">{error}</div>
            </div>
          )}

          <MetricsDisplay optimizationResult={optimizationResult} />
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
