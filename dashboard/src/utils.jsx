// Colores centralizados del dashboard
export const C = {
  rfPS:    '#63b3ed',
  svmPS:   '#f6ad55',
  rfLopo:  'rgba(99,179,237,0.5)',
  svmLopo: 'rgba(246,173,85,0.5)',
  green:   '#68d391',
  red:     '#fc8181',
  teal:    '#4fd1c5',
  grid:    'rgba(255,255,255,0.06)',
  tooltip: '#0d1117',
}

// Formatea un número a N decimales, devuelve '—' si es null/undefined
export const fmt = (v, d = 3) =>
  v == null ? '—' : Number(v).toFixed(d)

// Determina la clase CSS de color según el valor de una métrica
export const colorClass = (key, val) => {
  if (val == null) return ''
  if (key.includes('Sensibilidad'))   return val >= 0.8  ? 'best' : val >= 0.6 ? 'good' : 'warn'
  if (key.includes('AUC-ROC'))       return val >= 0.9  ? 'best' : val >= 0.75 ? 'good' : 'warn'
  if (key.includes('Falsas'))        return val <= 1.0  ? 'best' : val <= 2.5  ? 'good' : 'bad'
  if (key.includes('Latencia'))      return val <= 2.5  ? 'best' : val <= 5    ? 'good' : 'warn'
  return ''
}

// Tooltip personalizado para Recharts
export function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: C.tooltip,
      border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 8, padding: '10px 14px', fontSize: 13
    }}>
      <p style={{ color: '#e8edf5', fontWeight: 600, marginBottom: 6 }}>{label}</p>
      {payload.map((p, i) => (
        <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 3, alignItems: 'center' }}>
          <span style={{ color: p.color }}>●</span>
          <span style={{ color: '#8b9ab3' }}>{p.name}:</span>
          <span style={{ color: p.color, fontFamily: 'JetBrains Mono, monospace' }}>
            {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

// Calcula promedio de resúmenes de patient-specific por paciente
export function psGlobal(psResults) {
  if (!psResults || !Object.keys(psResults).length) return {}
  const vals = Object.values(psResults)
  const keys = Object.keys(vals[0])
  const out = {}
  for (const k of keys) {
    const nums = vals.map(v => v[k]).filter(v => v != null)
    out[k] = nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : null
  }
  return out
}
