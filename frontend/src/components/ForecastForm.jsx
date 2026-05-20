import React, { useState } from 'react'
import { createForecast } from '../services/api'

const cardStyle = {
  background: '#fff',
  borderRadius: '8px',
  padding: '1.5rem',
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  marginBottom: '1.5rem',
}

const inputStyle = {
  display: 'block',
  width: '100%',
  padding: '0.5rem',
  marginTop: '0.25rem',
  marginBottom: '1rem',
  borderRadius: '4px',
  border: '1px solid #ccc',
  fontSize: '1rem',
}

const btnStyle = {
  padding: '0.6rem 1.2rem',
  background: '#1a237e',
  color: '#fff',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '1rem',
}

export default function ForecastForm({ onTripCreated }) {
  const [form, setForm] = useState({
    destination: 'LON',
    origin: 'NYC',
    start_date: '',
    end_date: '',
    traveler_level: 'mid',
    currency: 'USD',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await createForecast(form)
      setResult(data)
      if (onTripCreated) onTripCreated(data.trip_id)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Pre-Trip Forecast</h2>
      <div style={cardStyle}>
        <form onSubmit={handleSubmit}>
          <label>
            Destination (IATA code)
            <input
              name="destination"
              value={form.destination}
              onChange={handleChange}
              style={inputStyle}
              placeholder="e.g. LON, PAR, TYO"
              required
            />
          </label>
          <label>
            Origin (IATA code)
            <input
              name="origin"
              value={form.origin}
              onChange={handleChange}
              style={inputStyle}
              placeholder="e.g. NYC"
              required
            />
          </label>
          <label>
            Start Date
            <input
              type="date"
              name="start_date"
              value={form.start_date}
              onChange={handleChange}
              style={inputStyle}
              required
            />
          </label>
          <label>
            End Date
            <input
              type="date"
              name="end_date"
              value={form.end_date}
              onChange={handleChange}
              style={inputStyle}
              required
            />
          </label>
          <label>
            Traveler Level
            <select
              name="traveler_level"
              value={form.traveler_level}
              onChange={handleChange}
              style={inputStyle}
            >
              <option value="junior">Junior</option>
              <option value="mid">Mid</option>
              <option value="senior">Senior</option>
              <option value="executive">Executive</option>
            </select>
          </label>
          <label>
            Currency
            <input
              name="currency"
              value={form.currency}
              onChange={handleChange}
              style={inputStyle}
              maxLength={3}
              required
            />
          </label>
          <button type="submit" style={btnStyle} disabled={loading}>
            {loading ? 'Generating...' : 'Generate Forecast'}
          </button>
        </form>
        {error && <p style={{ color: '#c62828', marginTop: '1rem' }}>{error}</p>}
      </div>

      {result && (
        <div style={cardStyle}>
          <h3>Forecast Result</h3>
          <p><strong>Trip ID:</strong> {result.trip_id}</p>
          <p><strong>Destination:</strong> {result.destination_name || result.destination}</p>
          <p><strong>Total Estimate:</strong> {result.total_estimate.toFixed(2)} {result.currency}</p>
          <p><strong>Range:</strong> {result.total_low.toFixed(2)} - {result.total_high.toFixed(2)} {result.currency}</p>
          <p><strong>Confidence:</strong> {(result.overall_confidence * 100).toFixed(0)}%</p>
          <p><strong>Summary:</strong> {result.natural_language_summary}</p>
          <h4>Line Items</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#e8eaf6' }}>
                <th style={{ padding: '0.5rem', textAlign: 'left' }}>Category</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Estimate</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Low</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>High</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {result.line_items.map((item) => (
                <tr key={item.category} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.5rem' }}>{item.category}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{item.estimate.toFixed(2)}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{item.low.toFixed(2)}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{item.high.toFixed(2)}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{(item.confidence * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
