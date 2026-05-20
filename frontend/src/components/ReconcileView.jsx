import React, { useEffect, useState } from 'react'
import { postReconcile, fetchAnomalies, fetchTrips } from '../services/api'
import AlertBanner from './AlertBanner'
import PostTripDashboard from './PostTripDashboard'

const cardStyle = {
  background: '#fff',
  borderRadius: '8px',
  padding: '1.5rem',
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  marginBottom: '1.5rem',
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

export default function ReconcileView({ tripId }) {
  const [trips, setTrips] = useState([])
  const [selectedTrip, setSelectedTrip] = useState(tripId)
  const [result, setResult] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTrips().then(setTrips).catch(() => setTrips([]))
  }, [])

  useEffect(() => {
    if (selectedTrip) {
      loadAnomalies(selectedTrip)
    }
  }, [selectedTrip])

  const loadAnomalies = async (id) => {
    try {
      const data = await fetchAnomalies(id)
      setAnomalies(data || [])
    } catch {
      setAnomalies([])
    }
  }

  const handleReconcile = async () => {
    if (!selectedTrip) {
      setError('Please select a trip first.')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await postReconcile(selectedTrip)
      setResult(data)
      loadAnomalies(selectedTrip)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Post-Trip Reconciliation</h2>
      <div style={cardStyle}>
        <label style={{ fontWeight: 600 }}>Select Trip:&nbsp;</label>
        <select onChange={(e) => setSelectedTrip(parseInt(e.target.value, 10) || null)} value={selectedTrip || ''}>
          <option value="">-- choose a trip --</option>
          {trips.map((t) => (
            <option key={t.id} value={t.id}>
              {t.id} - {t.destination} ({t.start_date} to {t.end_date})
            </option>
          ))}
        </select>
        <div style={{ marginTop: '1rem' }}>
          <button onClick={handleReconcile} style={btnStyle} disabled={loading}>
            {loading ? 'Reconciling...' : 'Run Reconciliation'}
          </button>
        </div>
        {error && <AlertBanner type="error" message={error} />}
      </div>

      {result && (
        <div style={cardStyle}>
          <h3>Reconciliation Result</h3>
          <p><strong>Budgeted:</strong> {result.total_budgeted.toFixed(2)}</p>
          <p><strong>Spent:</strong> {result.total_spent.toFixed(2)}</p>
          <p><strong>Variance:</strong> {result.variance.toFixed(2)}</p>
          <p><strong>Summary:</strong> {result.natural_language_summary}</p>
        </div>
      )}

      {anomalies.length > 0 && (
        <div style={cardStyle}>
          <h3>Anomalies</h3>
          {anomalies.map((a) => (
            <div key={a.id} style={{ borderBottom: '1px solid #eee', padding: '0.75rem 0' }}>
              <p style={{ margin: 0, fontWeight: 600 }}>
                {a.category} — {a.amount.toFixed(2)} ({a.severity.toUpperCase()})
              </p>
              <p style={{ margin: '0.25rem 0 0 0', color: '#555' }}>
                Expected: {a.expected_range_low.toFixed(2)} - {a.expected_range_high.toFixed(2)}
              </p>
              <p style={{ margin: '0.25rem 0 0 0', color: '#333' }}>{a.explanation}</p>
            </div>
          ))}
        </div>
      )}

      {result && (
        <PostTripDashboard
          tripId={selectedTrip}
          anomalies={anomalies}
          reconcileResult={result}
        />
      )}
    </div>
  )
}
