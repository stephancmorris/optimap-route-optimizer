import './MetricsDisplay.css';

export default function MetricsDisplay({ optimizationResult }) {
  if (!optimizationResult) {
    return null;
  }

  const {
    distance_saved_meters,
    time_saved_seconds,
    distance_saved_percentage,
    time_saved_percentage,
    optimized_metrics,
    baseline_metrics,
  } = optimizationResult;

  // Convert to human-readable units
  const distanceSavedKm = (distance_saved_meters / 1000).toFixed(2);
  const timeSavedMin = (time_saved_seconds / 60).toFixed(1);

  const optimizedDistanceKm = (optimized_metrics.total_distance_meters / 1000).toFixed(2);
  const optimizedTimeMin = (optimized_metrics.total_time_seconds / 60).toFixed(1);

  const baselineDistanceKm = (baseline_metrics.total_distance_meters / 1000).toFixed(2);
  const baselineTimeMin = (baseline_metrics.total_time_seconds / 60).toFixed(1);

  return (
    <div className="metrics-display">
      <h3>✨ Optimization Results</h3>

      <div className="savings-summary">
        <div className="savings-card distance">
          <div className="savings-icon">📏</div>
          <div className="savings-content">
            <div className="savings-label">Distance Saved</div>
            <div className="savings-value">{distanceSavedKm} km</div>
            <div className="savings-percentage">{distance_saved_percentage.toFixed(1)}% reduction</div>
          </div>
        </div>

        <div className="savings-card time">
          <div className="savings-icon">⏱️</div>
          <div className="savings-content">
            <div className="savings-label">Time Saved</div>
            <div className="savings-value">{timeSavedMin} min</div>
            <div className="savings-percentage">{time_saved_percentage.toFixed(1)}% reduction</div>
          </div>
        </div>
      </div>

      <div className="metrics-comparison">
        <h4>Route Comparison</h4>

        <div className="comparison-row optimized">
          <div className="route-label">
            <span className="route-badge optimized-badge">Optimized</span>
          </div>
          <div className="route-metrics">
            <span className="metric-item">
              <span className="metric-icon">📏</span> {optimizedDistanceKm} km
            </span>
            <span className="metric-item">
              <span className="metric-icon">⏱️</span> {optimizedTimeMin} min
            </span>
          </div>
        </div>

        <div className="comparison-row baseline">
          <div className="route-label">
            <span className="route-badge baseline-badge">Baseline</span>
          </div>
          <div className="route-metrics">
            <span className="metric-item">
              <span className="metric-icon">📏</span> {baselineDistanceKm} km
            </span>
            <span className="metric-item">
              <span className="metric-icon">⏱️</span> {baselineTimeMin} min
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
