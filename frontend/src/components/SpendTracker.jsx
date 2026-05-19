import React, { useEffect, useState } from 'react'
import { postSpend, fetchAlerts, fetchTransactions, fetchTrips } from '../services/api'
import AlertBanner from './AlertBanner'

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

export default function SpendTracker({ tripId }) {
  const [trips, setTrips] = useState([])
  const [selectedTrip, setSelectedTrip] = useState(tripId)
  const [alerts, setAlerts] = useState([])
  const [transactions, setTransactions] = useState([])
  const [form, setForm] = useState({
    category: 'meals',
    amount: '',
    currency: 'USD',
    description: '',
    merchant: '',
  })
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchTrips().then(setTrips).catch(() => setTrips([]))
  }, [])

  useEffect(() => {
    if (selectedTrip) {
      loadData(selectedTrip)
    }
  }, [selectedTrip])

  const loadData = async (id) => {
    try {
      const a = await fetchAlerts(id)
      setAlerts(a || [])
    } catch {
      setAlerts([])
    }
    try {
      const t = await fetchTransactions(id)
      setTransactions(t || [])
    } catch {
      setTransactions([])
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedTrip) {
      setMessage('Please select a trip first.')
      return
    }
    try {
      const data = await postSpend({
        trip_id: selectedTrip,
        category: form.category,
        amount: parseFloat(form.amount),
        currency: form.currency,
        description: form.description,
        merchant: form.merchant,
      })
      setMessage('Transaction recorded.')
      if (data.alerts && data.alerts.length > 0) {
        setAlerts(data.alerts)
      }
      loadData(selectedTrip)
      setForm({ category: 'meals', amount: '', currency: 'USD', description: '', merchant: '' })
    } catch (err) {
      setMessage(err.response?.data?.detail || err.message)
    }
  }

  return (
    <div>
      <h2>Real-Time Spend Tracker</h2>
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
      </div>

      <div style={cardStyle}>
        <h3>Log Transaction</h3>
        <form onSubmit={handleSubmit}>
          <label>
            Category
            <select name="category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} style={inputStyle}>
              <option value="flight">Flight</option>
              <option value="hotel">Hotel</option>
              <option value="ground_transport">Ground Transport</option>
              <option value="meals">Meals</option>
              <option value="miscellaneous">Miscellaneous</option>
            </select>
          </label>
          <label>
            Amount
            <input type="number" step="0.01" name="amount" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} style={inputStyle} required />
          </label>
          <label>
            Currency
            <input name="currency" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} style={inputStyle} maxLength={3} required />
          </label>
          <label>
            Description
            <input name="description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} style={inputStyle} />
          </label>
          <label>
            Merchant
            <input name="merchant" value={form.merchant} onChange={(e) => setForm({ ...form, merchant: e.target.value })} style={inputStyle} />
          </label>
          <button type="submit" style={btnStyle}>Record Spend</button>
        </form>
        {message && <p style={{ marginTop: '1rem' }}>{message}</p>}
      </div>

      {alerts.length > 0 && (
        <div style={cardStyle}>
          <h3>Alerts</h3>
          {alerts.map((a, idx) => (
            <AlertBanner
              key={idx}
              type={a.alert_level}
              message={`${a.category}: ${a.percent_used}% used — ${a.message}`}
            />
          ))}
        </div>
      )}

      <div style={cardStyle}>
        <h3>Recent Transactions</h3>
        {transactions.length === 0 ? (
          <p>No transactions yet.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#e8eaf6' }}>
                <th style={{ padding: '0.5rem', textAlign: 'left' }}>ID</th>
                <th style={{ padding: '0.5rem', textAlign: 'left' }}>Category</th>
                <th style={{ padding: '0.5rem', textAlign: 'right' }}>Amount</th>
                <th style={{ padding: '0.5rem', textAlign: 'left' }}>Merchant</th>
                <th style={{ padding: '0.5rem', textAlign: 'left' }}>Time</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.5rem' }}>{tx.id}</td>
                  <td style={{ padding: '0.5rem' }}>{tx.category}</td>
                  <td style={{ padding: '0.5rem', textAlign: 'right' }}>{tx.amount.toFixed(2)} {tx.currency}</td>
                  <td style={{ padding: '0.5rem' }}>{tx.merchant}</td>
                  <td style={{ padding: '0.5rem' }}>{new Date(tx.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
