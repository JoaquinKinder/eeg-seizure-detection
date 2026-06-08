import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ReferenceLine, ResponsiveContainer
} from 'recharts'
import { C, CustomTooltip } from '../utils'
import styles from './ChartCard.module.css'

export default function AucFaCharts({ data }) {
  const { metadata, patient_specific, lopo } = data
  const patients = metadata.patients

  const aucData = patients.map(pid => ({
    patient: pid.toUpperCase(),
    'RF PS':    patient_specific.random_forest.por_paciente[pid]?.['AUC-ROC'],
    'SVM PS':   patient_specific.svm.por_paciente[pid]?.['AUC-ROC'],
    'RF LOPO':  lopo.random_forest.por_paciente[pid]?.['AUC-ROC'],
    'SVM LOPO': lopo.svm.por_paciente[pid]?.['AUC-ROC'],
  }))

  const faData = patients.map(pid => ({
    patient: pid.toUpperCase(),
    'RF PS':    patient_specific.random_forest.por_paciente[pid]?.['Tasa de Falsas Alarmas (FA/h)'],
    'SVM PS':   patient_specific.svm.por_paciente[pid]?.['Tasa de Falsas Alarmas (FA/h)'],
    'RF LOPO':  lopo.random_forest.por_paciente[pid]?.['Tasa de Falsas Alarmas (FA/h)'],
    'SVM LOPO': lopo.svm.por_paciente[pid]?.['Tasa de Falsas Alarmas (FA/h)'],
  }))

  const tickStyle = { fill: '#8b9ab3', fontSize: 12 }
  const legendStyle = { fontSize: 12, color: '#8b9ab3', paddingTop: 8 }

  return (
    <section className={styles.section}>
      <div className={styles.grid2}>
        {/* AUC-ROC */}
        <div className={styles.card}>
          <div className={styles.cardTitle}>AUC-ROC por Paciente</div>
          <div className={styles.cardSub}>Independiente del umbral · &gt; 0.90 = excelente</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={aucData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
              <XAxis dataKey="patient" tick={tickStyle} />
              <YAxis domain={[0.5, 1]} tick={tickStyle} tickFormatter={v => v.toFixed(1)} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={legendStyle} />
              <ReferenceLine y={0.9} stroke="rgba(104,211,145,0.25)" strokeDasharray="5 3"
                label={{ value: '0.90', fill: '#68d391', fontSize: 10, position: 'right' }} />
              <Bar dataKey="RF PS"    fill={C.rfPS}   radius={[3,3,0,0]} />
              <Bar dataKey="SVM PS"   fill={C.svmPS}  radius={[3,3,0,0]} />
              <Bar dataKey="RF LOPO"  fill={C.rfLopo} radius={[3,3,0,0]} />
              <Bar dataKey="SVM LOPO" fill={C.svmLopo}radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* FA/h */}
        <div className={styles.card}>
          <div className={styles.cardTitle}>Falsas Alarmas por Hora (FA/h)</div>
          <div className={styles.cardSub}>Menor es mejor · meta clínica: &lt; 1 FA/h (línea roja)</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={faData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
              <XAxis dataKey="patient" tick={tickStyle} />
              <YAxis tick={tickStyle} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={legendStyle} />
              <ReferenceLine y={1} stroke="rgba(252,129,129,0.35)" strokeDasharray="5 3"
                label={{ value: '1 FA/h', fill: '#fc8181', fontSize: 10, position: 'right' }} />
              <Bar dataKey="RF PS"    fill={C.rfPS}   radius={[3,3,0,0]} />
              <Bar dataKey="SVM PS"   fill={C.svmPS}  radius={[3,3,0,0]} />
              <Bar dataKey="RF LOPO"  fill={C.rfLopo} radius={[3,3,0,0]} />
              <Bar dataKey="SVM LOPO" fill={C.svmLopo}radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}
