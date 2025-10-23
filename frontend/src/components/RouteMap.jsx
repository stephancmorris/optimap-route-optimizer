import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './RouteMap.css';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icon for depot/starting point
const depotIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Custom icon for regular stops
const stopIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Component to fit bounds when stops change
function MapBoundsSetter({ stops }) {
  const map = useMap();

  useEffect(() => {
    if (stops && stops.length > 0) {
      const bounds = L.latLngBounds(stops.map((stop) => [stop.latitude, stop.longitude]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [stops, map]);

  return null;
}

export default function RouteMap({ stops, optimizedRoute, routeGeometry }) {
  const mapRef = useRef(null);

  // Default center (San Francisco)
  const defaultCenter = [37.7749, -122.4194];
  const defaultZoom = 10;

  // Force map to refresh size when container changes
  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current.invalidateSize();
      }, 100);
    }
  }, [stops, optimizedRoute]);

  // Determine which stops to display - only include stops with valid coordinates
  const displayStops = (optimizedRoute || stops || []).filter(
    (stop) => stop && typeof stop.latitude === 'number' && typeof stop.longitude === 'number'
  );

  // Calculate center based on stops
  const mapCenter =
    displayStops.length > 0
      ? [displayStops[0].latitude, displayStops[0].longitude]
      : defaultCenter;

  // Create polyline coordinates for the route
  // Use OSRM route geometry if available (road-following), otherwise draw straight lines
  const routeCoordinates = (() => {
    // If we have route geometry from OSRM, use it (follows roads)
    if (routeGeometry && routeGeometry.coordinates && routeGeometry.coordinates.length > 0) {
      // GeoJSON format is [longitude, latitude], Leaflet uses [latitude, longitude]
      return routeGeometry.coordinates.map(coord => [coord[1], coord[0]]);
    }

    // Fallback: draw straight lines between stops
    if (optimizedRoute && optimizedRoute.length > 0) {
      return optimizedRoute.map((stop) => [stop.latitude, stop.longitude]);
    }

    return [];
  })();

  return (
    <div className="route-map">
      <MapContainer
        center={mapCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
        whenReady={(map) => {
          setTimeout(() => {
            map.target.invalidateSize();
          }, 100);
        }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {/* Render stops as markers */}
        {displayStops.map((stop, index) => {
          const isDepot = index === 0;
          const isLastInRoute = optimizedRoute && index === optimizedRoute.length - 1;

          // Don't show the last marker if it's the same as depot (return to start)
          if (isLastInRoute && optimizedRoute.length > 1) {
            const firstStop = optimizedRoute[0];
            if (
              stop.latitude === firstStop.latitude &&
              stop.longitude === firstStop.longitude
            ) {
              return null;
            }
          }

          return (
            <Marker
              key={`${stop.latitude}-${stop.longitude}-${index}`}
              position={[stop.latitude, stop.longitude]}
              icon={isDepot ? depotIcon : stopIcon}
            >
              <Popup>
                <div className="marker-popup">
                  <strong>
                    {isDepot ? '🏁 Starting Point' : `📍 Stop ${index + 1}`}
                  </strong>
                  {stop.address && (
                    <div className="popup-address">{stop.address}</div>
                  )}
                  {typeof stop.latitude === 'number' && typeof stop.longitude === 'number' && (
                    <div className="popup-coords">
                      {stop.latitude.toFixed(4)}, {stop.longitude.toFixed(4)}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Draw route line if optimized route exists */}
        {routeCoordinates.length > 1 && (
          <Polyline
            positions={routeCoordinates}
            color="#667eea"
            weight={4}
            opacity={0.8}
            dashArray="0"
          />
        )}

        {/* Auto-fit bounds to show all stops */}
        <MapBoundsSetter stops={displayStops} />
      </MapContainer>

      {displayStops.length === 0 && (
        <div className="map-overlay">
          <p>🗺️ Add stops to see them on the map</p>
        </div>
      )}
    </div>
  );
}
