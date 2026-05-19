import React, { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, Area, ComposedChart
} from 'recharts'
import { fetchBudget, fetchBurnRate, fetchTrips } from '../services/api'
import AlertBanner from './AlertBanner'

const cardStyle = {
  background: '#fff',
  borderRadius: '8px',
  padding: '1.5rem',
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  marginBottom: '1.5rem',
}

export default function BudgetDashboard({ tripId }) {
  const [trips, setTrips] = useState([])
  const [selectedTrip, setSelectedTrip] = useState(tripId)
  const [budget, setBudget] = useState([])
  const [burn, setBurn] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTrips().then(setTrips).catch(() => setTrips([]))
  }, [])

  useEffect(() => {
    if (selectedTrip) {
      fetchBudget(selectedTrip)
        .then((data) => setBudget(data || []))
        .catch((e) => setError(e.message))
      fetchBurnRate(selectedTrip)
        .then((data) => setBurn(data))
        .catch(() => setBurn(null))
    }
  }, [selectedTrip])

  const handleSelect = (e) => {
    const id = parseInt(e.target.value, 10)
    setSelectedTrip(id)
    setError('')
  }

  const budgetData = budget.map((b) => ({
    category: b.category,
    estimate: b.estimate,
    low: b.low,
    high: b.high,
  }))

  return (
    <div>
      <h2>Budget Dashboard</h2>
      <div style={cardStyle}>
        <label style={{ fontWeight: 600 }}>Select Trip:&nbsp;</label>
        <select onChange={handleSelect} value={selectedTrip || ''}>
          <option value="">-- choose a trip --</option>
          {trips.map((t) => (
            <option key={t.id} value={t.id}>
              {t.id} - {t.destination} ({t.start_date} to {t.end_date})
            </option>
          ))}
        </select>
        {error && <AlertBanner type="error" message={error} />}
      </div>

      {selectedTrip && budgetData.length > 0 && (
        <>
          <div style={cardStyle}>
            <h3>Budget Breakdown</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={budgetData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="estimate" fill="#3949ab" name="Estimate" />
                <Bar dataKey="low" fill="#66bb6a" name="Low" />
                <Bar dataKey="high" fill="#ef5350" name="High" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={cardStyle}>
            <h3>Confidence Intervals</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={budgetData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="high" fill="#ffcdd2" stroke="#ef5350" name="High" />
                <Area type="monotone" dataKey="estimate" fill="#c5cae9" stroke="#3949ab" name="Estimate" />
                <Line type="monotone" dataKey="low" stroke="#66bb6a" name="Low" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {burn && (
        <div style={cardStyle}>
          <h3>Burn Rate</h3>
          <p><strong>Total Budget:</strong> {burn.total_budget.toFixed(2)}</p>
          <p><strong>Total Spent:</strong> {burn.total_spent.toFixed(2)}</p>
          <p><strong>Remaining:</strong> {burn.remaining.toFixed(2)}</p>
          <p><strong>Daily Burn Rate:</strong> {burn.daily_burn_rate.toFixed(2)}</p>
          <p><strong>Days:</strong> {burn.days_elapsed} / {burn.days_total}</p>
          {burn.projected_overspend !== null && (
            <AlertBanner
              type="critical"
              message={`Projected overspend: ${burn.projected_overspend.toFixed(2)}`}
            />
          )}
        </div>
      )}
    </div>
  )
}
