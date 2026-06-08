import styles from './Header.module.css'

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.icon}>🧠</div>
      <div className={styles.text}>
        <h1>EEG Seizure Detection — Dashboard</h1>
        <p>Resultados de validación cruzada · CHB-MIT · 23 canales · 256 Hz</p>
        <div className={styles.badges}>
          <span className={`${styles.badge} ${styles.blue}`}>
            <span className={styles.dot} />DWT db4 · 5 niveles
          </span>
          <span className={`${styles.badge} ${styles.purple}`}>
            <span className={styles.dot} />Random Forest + SVM-RBF
          </span>
          <span className={`${styles.badge} ${styles.green}`}>
            <span className={styles.dot} />Histéresis Schmitt-trigger
          </span>
        </div>
      </div>
    </header>
  )
}
