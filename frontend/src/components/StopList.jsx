import './StopList.css';

export default function StopList({ stops, onRemoveStop, onOptimize, isOptimizing }) {
  const canOptimize = stops.length >= 2;

  return (
    <div className="stop-list">
      <div className="stop-list-header">
        <h3>Delivery Stops ({stops.length})</h3>
        {stops.length >= 2 && (
          <span className="help-text">Ready to optimize!</span>
        )}
        {stops.length === 1 && (
          <span className="help-text warning">Add at least 1 more stop</span>
        )}
      </div>

      {stops.length === 0 ? (
        <div className="empty-state">
          <p>No stops added yet.</p>
          <p className="help-text">Add at least 2 stops to optimize your route.</p>
        </div>
      ) : (
        <>
          <ul className="stops">
            {stops.map((stop, index) => (
              <li key={index} className="stop-item">
                <div className="stop-info">
                  <div className="stop-number">{index + 1}</div>
                  <div className="stop-details">
                    {stop.address && <div className="stop-address">{stop.address}</div>}
                    <div className="stop-coords">
                      {stop.latitude.toFixed(4)}, {stop.longitude.toFixed(4)}
                    </div>
                  </div>
                </div>
                <button
                  className="btn-remove"
                  onClick={() => onRemoveStop(index)}
                  title="Remove stop"
                  disabled={isOptimizing}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>

          <button
            className="btn-optimize"
            onClick={onOptimize}
            disabled={!canOptimize || isOptimizing}
          >
            {isOptimizing ? 'Optimizing...' : 'Optimize Route'}
          </button>
        </>
      )}
    </div>
  );
}
