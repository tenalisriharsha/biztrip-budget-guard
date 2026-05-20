import React, { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, ComposedChart, Line,
  ReferenceLine
} from 'recharts'
import { fetchBudget, fetchTransactions } from '../services/api'

const cardStyle = {
  background: '#fff',
  borderRadius: '8px',
  padding: '1.5rem',
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  marginBottom: '1.5rem',
}

const COLORS = {
  budgeted: '#3949ab',
  actual: '#66bb6a',
  over: '#ef5350',
  under: '#42a5f5',
  pie: ['#3949ab', '#66bb6a', '#ffa726', '#ef5350', '#ab47bc'],
}

export default function PostTripDashboard({ tripId, anomalies, reconcileResult }) {
  const [budget, setBudget] = useState([])
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!tripId) return
    Promise.all([
      fetchBudget(tripId).catch(() => []),
      fetchTransactions(tripId).catch(() => []),
    ]).then(([b, t]) => {
      setBudget(b || [])
      setTransactions(t || [])
      setLoading(false)
    })
  }, [tripId])

  if (loading) return <div style={cardStyle}>Loading post-trip dashboard...</div>

  // Aggregate actual spend by category
  const actualByCategory = {}
  transactions.forEach((tx) => {
    actualByCategory[tx.category] = (actualByCategory[tx.category] || 0) + tx.amount
  })

  // Build comparison data for bar chart
  const comparisonData = budget.map((b) => {
    const actual = actualByCategory[b.category] || 0
    const variance = actual - b.estimate
    return {
      category: b.category,
      budgeted: b.estimate,
      actual: actual,
      variance: variance,
      percentUsed: b.estimate > 0 ? Math.round((actual / b.estimate) * 100) : 0,
    }
  })

  // Pie chart data for spend distribution
  const pieData = comparisonData
    .filter((d) => d.actual > 0)
    .map((d) => ({
      name: d.category,
      value: d.actual,
    }))

  // Anomaly severity counts
  const severityCounts = { high: 0, medium: 0, low: 0 }
  anomalies.forEach((a) => {
    severityCounts[a.severity] = (severityCounts[a.severity] || 0) + 1
  })
  const anomalyData = [
    { severity: 'High', count: severityCounts.high },
    { severity: 'Medium', count: severityCounts.medium },
    { severity: 'Low', count: severityCounts.low },
  ]

  return (
    <div>
      <h3>Post-Trip Dashboard</h3>

      {/* Budgeted vs Actual */}
      <div style={cardStyle}>
        <h4>Budgeted vs Actual Spend</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip formatter={(value) => value.toFixed(2)} />
            <Legend />
            <Bar dataKey="budgeted" fill={COLORS.budgeted} name="Budgeted" />
            <Bar dataKey="actual" fill={COLORS.actual} name="Actual" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Variance Chart */}
      <div style={cardStyle}>
        <h4>Variance by Category</h4>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip formatter={(value) => value.toFixed(2)} />
            <ReferenceLine y={0} stroke="#000" />
            <Bar
              dataKey="variance"
              name="Variance"
              fill="#8884d8"
              shape={(props) => {
                const { fill, ...rest } = props
                const color = props.payload.variance > 0 ? COLORS.over : COLORS.under
                return <rect {...rest} fill={color} />
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
        <p style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
          🔴 Red = overspent &nbsp; 🔵 Blue = underspent
        </p>
      </div>

      {/* Spend Distribution Pie */}
      {pieData.length > 0 && (
        <div style={cardStyle}>
          <h4>Actual Spend Distribution</h4>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                nameKey="name"
                label
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS.pie[index % COLORS.pie.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => value.toFixed(2)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Category Usage % */}
      <div style={cardStyle}>
        <h4>Burn Rate by Category (%)</h4>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis unit="%" />
            <Tooltip formatter={(value) => `${value}%`} />
            <Bar dataKey="percentUsed" fill={COLORS.budgeted} name="% of Budget Used" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Anomaly Summary */}
      {anomalies.length > 0 && (
        <div style={cardStyle}>
          <h4>Anomaly Severity Breakdown</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={anomalyData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="severity" type="category" />
              <Tooltip />
              <Bar dataKey="count" fill={COLORS.over} name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Summary Cards */}
      <div style={{ ...cardStyle, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Budgeted</p>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.5rem', fontWeight: 700, color: COLORS.budgeted }}>
            {reconcileResult?.total_budgeted?.toFixed(2) || '0.00'}
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Spent</p>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.5rem', fontWeight: 700, color: COLORS.actual }}>
            {reconcileResult?.total_spent?.toFixed(2) || '0.00'}
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Variance</p>
          <p style={{
            margin: '0.25rem 0 0 0',
            fontSize: '1.5rem',
            fontWeight: 700,
            color: (reconcileResult?.variance || 0) > 0 ? COLORS.over : COLORS.under
          }}>
            {(reconcileResult?.variance || 0) > 0 ? '+' : ''}{reconcileResult?.variance?.toFixed(2) || '0.00'}
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Anomalies</p>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.5rem', fontWeight: 700, color: COLORS.over }}>
            {anomalies.length}
          </p>
        </div>
      </div>
    </div>
  )
}
