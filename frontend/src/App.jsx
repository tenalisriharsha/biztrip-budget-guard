import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import ForecastForm from './components/ForecastForm'
import BudgetDashboard from './components/BudgetDashboard'
import SpendTracker from './components/SpendTracker'
import ReconcileView from './components/ReconcileView'

const navStyle = {
  display: 'flex',
  gap: '1rem',
  padding: '1rem 2rem',
  background: '#1a237e',
  color: '#fff',
  alignItems: 'center',
}

const linkStyle = {
  color: '#fff',
  textDecoration: 'none',
  fontWeight: 500,
}

const contentStyle = {
  padding: '1.5rem 2rem',
  maxWidth: '1200px',
  margin: '0 auto',
}

export default function App() {
  const [activeTripId, setActiveTripId] = useState(null)

  return (
    <BrowserRouter>
      <nav style={navStyle}>
        <h2 style={{ margin: 0, marginRight: 'auto' }}>BizTrip Budget Guard</h2>
        <Link to="/" style={linkStyle}>Forecast</Link>
        <Link to="/dashboard" style={linkStyle}>Dashboard</Link>
        <Link to="/spend" style={linkStyle}>Spend Tracker</Link>
        <Link to="/reconcile" style={linkStyle}>Reconcile</Link>
      </nav>
      <div style={contentStyle}>
        <Routes>
          <Route path="/" element={<ForecastForm onTripCreated={setActiveTripId} />} />
          <Route path="/dashboard" element={<BudgetDashboard tripId={activeTripId} />} />
          <Route path="/spend" element={<SpendTracker tripId={activeTripId} />} />
          <Route path="/reconcile" element={<ReconcileView tripId={activeTripId} />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
