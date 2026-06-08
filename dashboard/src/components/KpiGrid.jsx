import { fmt, psGlobal, C } from '../utils'
import styles from './KpiGrid.module.css'

function KpiCard({ label, value, unit, color, delta, deltaLabel }) {
  return (
    <div className={styles.card}>
      <div className={styles.label}>{label}</div>
      <div className={styles.value} style={{ color: color || 'var(--text-primary)' }}>
        {value}
        {unit && <span className={styles.unit}>{unit}</span>}
      </div>
      {delta != null && (
        <span className={`${styles.delta} ${delta < 0 ? styles.neg : styles.pos}`}>
          {delta > 0 ? '↑' : '↓'} {Math.abs(delta).toFixed(3)} {deltaLabel}
        </span>
      )}
    </div>
  )
}

export default function KpiGrid({ data }) {
  const { patient_specific, lopo } = data
  const rfPS   = patient_specific.random_forest.global
  const rfLopo = lopo.random_forest.global

  const sensDrop = rfLopo['Sensibilidad (TPR)'] - rfPS['Sensibilidad (TPR)']
  const aucDrop  = rfLopo['AUC-ROC'] - rfPS['AUC-ROC']

  return (
    <>
      <h2 className={styles.sectionTitle}>📊 Indicadores Clave (RF — Patient-Specific vs. LOPO)</h2>
      <div className={styles.grid}>
        <KpiCard label="Sensibilidad RF · Patient-Specific" value={fmt(rfPS['Sensibilidad (TPR)'])} color={C.rfPS}   delta={sensDrop} deltaLabel="vs LOPO" />
        <KpiCard label="Sensibilidad RF · LOPO"             value={fmt(rfLopo['Sensibilidad (TPR)'])} color={C.rfLopo} />
        <KpiCard label="AUC-ROC RF · Patient-Specific"      value={fmt(rfPS['AUC-ROC'])} color={C.green}  delta={aucDrop}  deltaLabel="vs LOPO" />
        <KpiCard label="AUC-ROC RF · LOPO"                  value={fmt(rfLopo['AUC-ROC'])} color={C.teal}  />
        <KpiCard label="FA/hora RF · Patient-Specific" unit="FA/h" value={fmt(rfPS['Tasa de Falsas Alarmas (FA/h)'], 2)}   color={C.rfPS} />
        <KpiCard label="FA/hora RF · LOPO"             unit="FA/h" value={fmt(rfLopo['Tasa de Falsas Alarmas (FA/h)'], 2)} color={C.rfLopo} />
        <KpiCard label="Latencia RF · Patient-Specific" unit="s" value={fmt(rfPS['Latencia de Detección (s)'], 1)}   color={C.svmPS} />
        <KpiCard label="Latencia RF · LOPO"             unit="s" value={fmt(rfLopo['Latencia de Detección (s)'], 1)} color={C.svmLopo} />
      </div>
    </>
  )
}
