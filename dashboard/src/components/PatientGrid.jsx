import styles from './PatientGrid.module.css'

export default function PatientGrid({ data }) {
  const { metadata, patient_stats } = data
  const patients = metadata.patients

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>🗂️ Estadísticas por Paciente</h2>
      <p className={styles.sectionDesc}>
        Distribución de clases en los datos procesados. El desbalance extremo (~0.3% de crisis)
        justifica el uso de SMOTE + submuestreo exclusivamente en entrenamiento.
      </p>
      <div className={styles.grid}>
        {patients.map(pid => {
          const s = patient_stats[pid] || {}
          const total = s.total_ventanas || 0
          const crisis = s.ventanas_crisis || 0
          const pct = s.pct_crisis || 0

          return (
            <div className={styles.card} key={pid}>
              <div className={styles.pid}>{pid.toUpperCase()}</div>
              <div className={styles.stat}>
                Ventanas totales: <span>{total.toLocaleString('es-AR')}</span>
              </div>
              <div className={styles.stat}>
                Ventanas crisis: <span className={styles.cRed}>{crisis.toLocaleString('es-AR')}</span>
              </div>
              <div className={styles.stat}>
                % crisis: <span className={styles.cAmber}>{pct.toFixed(3)}%</span>
              </div>
              <div className={styles.stat}>
                Nº features: <span>{s.n_features}</span>
              </div>
              
              {/* Mini barra de desbalance (escalada x50 para que se vea) */}
              <div className={styles.barWrap}>
                <div 
                  className={styles.barFill} 
                  style={{ width: `${Math.min(100, pct * 50)}%` }} 
                />
              </div>
              <div className={styles.barLabel}>Crisis / Total (escala visual ×50)</div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
