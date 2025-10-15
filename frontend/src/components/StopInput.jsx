import { useState } from 'react';
import './StopInput.css';

export default function StopInput({ onAddStop }) {
  const [inputMode, setInputMode] = useState('address'); // 'address' or 'coordinates'
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [address, setAddress] = useState('');
  const [errors, setErrors] = useState({});

  const validateAddressInput = () => {
    const newErrors = {};

    if (!address || address.trim() === '') {
      newErrors.address = 'Address is required';
    } else if (address.trim().length < 5) {
      newErrors.address = 'Please provide a more specific address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateCoordinateInput = () => {
    const newErrors = {};

    if (!latitude || latitude.trim() === '') {
      newErrors.latitude = 'Latitude is required';
    } else {
      const lat = parseFloat(latitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        newErrors.latitude = 'Latitude must be between -90 and 90';
      }
    }

    if (!longitude || longitude.trim() === '') {
      newErrors.longitude = 'Longitude is required';
    } else {
      const lon = parseFloat(longitude);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        newErrors.longitude = 'Longitude must be between -180 and 180';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    let isValid = false;
    let stop = {};

    if (inputMode === 'address') {
      isValid = validateAddressInput();
      if (isValid) {
        stop = {
          address: address.trim(),
        };
      }
    } else {
      isValid = validateCoordinateInput();
      if (isValid) {
        stop = {
          latitude: parseFloat(latitude),
          longitude: parseFloat(longitude),
          address: address.trim() || undefined,
        };
      }
    }

    if (!isValid) {
      return;
    }

    onAddStop(stop);

    // Clear form
    setLatitude('');
    setLongitude('');
    setAddress('');
    setErrors({});
  };

  const switchMode = (mode) => {
    setInputMode(mode);
    setErrors({});
  };

  return (
    <div className="stop-input">
      <div className="stop-input-header">
        <h3>📍 Add Delivery Stop</h3>
        <div className="input-mode-toggle">
          <button
            type="button"
            className={`mode-btn ${inputMode === 'address' ? 'active' : ''}`}
            onClick={() => switchMode('address')}
            title="Enter address"
          >
            <span className="mode-icon">🏠</span>
            Address
          </button>
          <button
            type="button"
            className={`mode-btn ${inputMode === 'coordinates' ? 'active' : ''}`}
            onClick={() => switchMode('coordinates')}
            title="Enter coordinates"
          >
            <span className="mode-icon">🌐</span>
            Coordinates
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {inputMode === 'address' ? (
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="address">
                <span className="label-text">Street Address</span>
                <span className="required">*</span>
              </label>
              <div className="input-wrapper">
                <input
                  type="text"
                  id="address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="123 Main St, New York, NY 10001"
                  className={errors.address ? 'error' : ''}
                  autoComplete="street-address"
                />
              </div>
              {errors.address && (
                <span className="error-message">⚠️ {errors.address}</span>
              )}
            </div>
            <div className="help-text">
              💡 We'll automatically geocode your address!
            </div>
          </div>
        ) : (
          <div className="form-section">
            <div className="coordinate-inputs">
              <div className="form-group">
                <label htmlFor="latitude">
                  <span className="label-text">Latitude</span>
                  <span className="required">*</span>
                </label>
                <div className="input-wrapper">
                  <input
                    type="text"
                    id="latitude"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    placeholder="40.7128"
                    className={errors.latitude ? 'error' : ''}
                  />
                </div>
                {errors.latitude && (
                  <span className="error-message">⚠️ {errors.latitude}</span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="longitude">
                  <span className="label-text">Longitude</span>
                  <span className="required">*</span>
                </label>
                <div className="input-wrapper">
                  <input
                    type="text"
                    id="longitude"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    placeholder="-74.0060"
                    className={errors.longitude ? 'error' : ''}
                  />
                </div>
                {errors.longitude && (
                  <span className="error-message">⚠️ {errors.longitude}</span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="address-optional">
                <span className="label-text">Label (Optional)</span>
              </label>
              <div className="input-wrapper">
                <input
                  type="text"
                  id="address-optional"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Customer name or reference"
                />
              </div>
            </div>
          </div>
        )}

        <button type="submit" className="btn-add">
          <span className="btn-icon">➕</span>
          Add Stop
        </button>
      </form>
    </div>
  );
}
