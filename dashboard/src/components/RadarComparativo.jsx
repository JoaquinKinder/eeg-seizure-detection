import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { C, CustomTooltip } from '../utils'
import styles from './ChartCard.module.css'

const METRICS = [
  { subject: 'Sensibilidad', key: 'Sensibilidad (TPR)' },
  { subject: 'Especificidad', key: 'Especificidad (TNR)' },
  { subject: 'AUC-ROC', key: 'AUC-ROC' },
  { subject: 'AUC-PR', key: 'AUC-PR' },
  // Invertimos FA/h para que "mejor" sea "más lejos del centro"
  { subject: '1−FA/h×0.1', key: 'Tasa de Falsas Alarmas (FA/h)', transform: v => Math.max(0, 1 - v * 0.1) },
]

function get(src, key, transform) {
  const v = src?.global?.[key]
  if (v == null) return 0
  const val = transform ? transform(v) : v
  return Math.max(0, Math.min(1, val))
}

export default function RadarComparativo({ data }) {
  const { patient_specific, lopo } = data

  const radarData = METRICS.map(m => ({
    subject: m.subject,
    'RF PS':    get(patient_specific.random_forest, m.key, m.transform),
    'SVM PS':   get(patient_specific.svm,           m.key, m.transform),
    'RF LOPO':  get(lopo.random_forest,             m.key, m.transform),
    'SVM LOPO': get(lopo.svm,                       m.key, m.transform),
  }))

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>🕸️ Perfil Global Comparativo</h2>
      <p className={styles.sectionDesc}>
        Radar de métricas normalizadas. Mayor área = mejor desempeño general.
        La dimensión <em>1−FA/h×0.1</em> invierte la tasa de falsas alarmas para que mayor = mejor.
      </p>
      <div className={styles.card} style={{ maxWidth: 620, margin: '0 auto' }}>
        <ResponsiveContainer width="100%" height={360}>
          <RadarChart data={radarData}>
            <PolarGrid stroke={C.grid} />
            <PolarAngleAxis dataKey="subject" tick={{ fill: '#8b9ab3', fontSize: 12 }} />
            <PolarRadiusAxis domain={[0, 1]} tick={{ fill: '#4a5568', fontSize: 9 }} />
            <Radar name="RF Patient-Specific" dataKey="RF PS"   stroke={C.rfPS}             fill={C.rfPS}             fillOpacity={0.18} strokeWidth={2} />
            <Radar name="SVM Patient-Specific" dataKey="SVM PS" stroke={C.svmPS}            fill={C.svmPS}            fillOpacity={0.12} strokeWidth={2} />
            <Radar name="RF LOPO"  dataKey="RF LOPO"  stroke="rgba(99,179,237,0.7)"  fill="rgba(99,179,237,0.3)"  fillOpacity={0.08} strokeWidth={1.5} strokeDasharray="5 3" />
            <Radar name="SVM LOPO" dataKey="SVM LOPO" stroke="rgba(246,173,85,0.7)"  fill="rgba(246,173,85,0.3)"  fillOpacity={0.08} strokeWidth={1.5} strokeDasharray="5 3" />
            <Legend wrapperStyle={{ fontSize: 12, color: '#8b9ab3', paddingTop: 8 }} />
            <Tooltip content={<CustomTooltip />} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
