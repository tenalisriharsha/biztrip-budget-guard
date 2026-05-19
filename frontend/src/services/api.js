import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

export async function createForecast(payload) {
  const { data } = await client.post('/forecast', payload)
  return data
}

export async function postSpend(payload) {
  const { data } = await client.post('/spend', payload)
  return data
}

export async function postReconcile(tripId) {
  const { data } = await client.post('/reconcile', null, { params: { trip_id: tripId } })
  return data
}

export async function fetchTrips() {
  const { data } = await client.get('/trips')
  return data
}

export async function fetchBudget(tripId) {
  const { data } = await client.get(`/trips/${tripId}/budget`)
  return data
}

export async function fetchBurnRate(tripId) {
  const { data } = await client.get(`/trips/${tripId}/burn`)
  return data
}

export async function fetchAlerts(tripId) {
  const { data } = await client.get(`/trips/${tripId}/alerts`)
  return data
}

export async function fetchTransactions(tripId) {
  const { data } = await client.get(`/trips/${tripId}/transactions`)
  return data
}

export async function fetchAnomalies(tripId) {
  const { data } = await client.get(`/trips/${tripId}/anomalies`)
  return data
}
