import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ReferenceLine, ResponsiveContainer
} from 'recharts'
import { C, CustomTooltip } from '../utils'
import styles from './ChartCard.module.css'

export default function SensibilityChart({ data }) {
  const { metadata, patient_specific, lopo } = data
  const patients = metadata.patients

  const chartData = patients.map(pid => ({
    patient: pid.toUpperCase(),
    'RF Patient-Specific': patient_specific.random_forest.por_paciente[pid]?.['Sensibilidad (TPR)'],
    'SVM Patient-Specific': patient_specific.svm.por_paciente[pid]?.['Sensibilidad (TPR)'],
    'RF LOPO':              lopo.random_forest.por_paciente[pid]?.['Sensibilidad (TPR)'],
    'SVM LOPO':             lopo.svm.por_paciente[pid]?.['Sensibilidad (TPR)'],
  }))

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>📈 Sensibilidad (TPR) por Paciente</h2>
      <p className={styles.sectionDesc}>
        Comparativa de los 4 escenarios por paciente. La brecha entre Patient-Specific y LOPO
        revela la dependencia del modelo a datos del mismo individuo.
      </p>
      <div className={styles.card}>
        <div className={styles.cardTitle}>Sensibilidad — Todos los escenarios</div>
        <div className={styles.cardSub}>Umbral clínico de referencia: 0.80 (línea punteada)</div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
            <XAxis dataKey="patient" tick={{ fill: '#8b9ab3', fontSize: 12 }} />
            <YAxis domain={[0, 1]} tick={{ fill: '#8b9ab3', fontSize: 12 }} tickFormatter={v => v.toFixed(1)} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: '#8b9ab3', paddingTop: 12 }} />
            <ReferenceLine y={0.8} stroke="rgba(255,255,255,0.2)" strokeDasharray="6 3"
              label={{ value: '0.80', fill: '#8b9ab3', fontSize: 11, position: 'right' }} />
            <Bar dataKey="RF Patient-Specific"  fill={C.rfPS}   radius={[4,4,0,0]} />
            <Bar dataKey="SVM Patient-Specific" fill={C.svmPS}  radius={[4,4,0,0]} />
            <Bar dataKey="RF LOPO"              fill={C.rfLopo} radius={[4,4,0,0]} />
            <Bar dataKey="SVM LOPO"             fill={C.svmLopo}radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
