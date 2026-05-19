import React from 'react'

const baseStyle = {
  padding: '0.75rem 1rem',
  borderRadius: '6px',
  marginBottom: '0.75rem',
  fontWeight: 500,
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
}

const typeStyles = {
  warning: { background: '#fff3cd', color: '#856404', border: '1px solid #ffeeba' },
  critical: { background: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb' },
  error: { background: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb' },
  success: { background: '#d4edda', color: '#155724', border: '1px solid #c3e6cb' },
}

export default function AlertBanner({ type = 'warning', message }) {
  const style = { ...baseStyle, ...(typeStyles[type] || typeStyles.warning) }
  return (
    <div style={style} role="alert">
      <span>{type === 'critical' ? '⚠️' : type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️'}</span>
      <span>{message}</span>
    </div>
  )
}
