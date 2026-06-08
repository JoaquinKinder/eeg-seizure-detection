import { fmt, colorClass, psGlobal } from '../utils'
import styles from './MetricsTable.module.css'

const METRICS = [
  ['Sensibilidad (TPR)',             3],
  ['Especificidad (TNR)',            3],
  ['AUC-ROC',                        3],
  ['AUC-PR',                         3],
  ['Tasa de Falsas Alarmas (FA/h)',  2],
  ['Latencia de Detección (s)',       1],
]

export default function MetricsTable({ data }) {
  const { patient_specific, lopo } = data
  const psRfGlob  = patient_specific.random_forest.global
  const psSvmGlob = patient_specific.svm.global
  const lopoRfGlob  = lopo.random_forest.global
  const lopoSvmGlob = lopo.svm.global

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>📋 Tabla Comparativa Global</h2>
      <p className={styles.sectionDesc}>
        Promedios de métricas clínicas sobre todos los pacientes.&nbsp;
        <span className={styles.best}>■ excelente</span> ·{' '}
        <span className={styles.good}>■ bueno</span> ·{' '}
        <span className={styles.warn}>■ aceptable</span> ·{' '}
        <span className={styles.bad}>■ deficiente</span>
      </p>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Métrica</th>
              <th><span className={styles.badgePS}>PS</span> Random Forest</th>
              <th><span className={styles.badgePS}>PS</span> SVM-RBF</th>
              <th><span className={styles.badgeLopo}>LOPO</span> Random Forest</th>
              <th><span className={styles.badgeLopo}>LOPO</span> SVM-RBF</th>
            </tr>
          </thead>
          <tbody>
            {METRICS.map(([key, d]) => (
              <tr key={key}>
                <td className={styles.metricName}>{key}</td>
                {[psRfGlob, psSvmGlob, lopoRfGlob, lopoSvmGlob].map((src, i) => {
                  const v = src?.[key]
                  const cls = colorClass(key, v)
                  return (
                    <td key={i}>
                      <span className={`${styles.val} ${styles[cls] || ''}`}>
                        {fmt(v, d)}
                      </span>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={styles.legend}>
        PS = Patient-Specific (5-Fold CV por paciente) &nbsp;·&nbsp;
        LOPO = Leave-One-Patient-Out (generalización entre sujetos)
      </p>
    </section>
  )
}
