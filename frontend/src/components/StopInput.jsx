import { useState } from 'react';
import './StopInput.css';

export default function StopInput({ onAddStop }) {
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [address, setAddress] = useState('');
  const [errors, setErrors] = useState({});

  const validateInputs = () => {
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

    if (!validateInputs()) {
      return;
    }

    const stop = {
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      address: address.trim() || undefined,
    };

    onAddStop(stop);

    // Clear form
    setLatitude('');
    setLongitude('');
    setAddress('');
    setErrors({});
  };

  return (
    <div className="stop-input">
      <h3>Add Delivery Stop</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="latitude">
            Latitude <span className="required">*</span>
          </label>
          <input
            type="text"
            id="latitude"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            placeholder="37.7749"
            className={errors.latitude ? 'error' : ''}
          />
          {errors.latitude && <span className="error-message">{errors.latitude}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="longitude">
            Longitude <span className="required">*</span>
          </label>
          <input
            type="text"
            id="longitude"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            placeholder="-122.4194"
            className={errors.longitude ? 'error' : ''}
          />
          {errors.longitude && <span className="error-message">{errors.longitude}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="address">Address (Optional)</label>
          <input
            type="text"
            id="address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="San Francisco, CA"
          />
        </div>

        <button type="submit" className="btn-add">
          Add Stop
        </button>
      </form>
    </div>
  );
}
