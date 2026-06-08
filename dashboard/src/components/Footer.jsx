import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p>Detección automática de crisis epilépticas · CHB-MIT · Señales y Sistemas — TPI Hito 2</p>
      <p className={styles.sub}>
        Pipeline: DWT db4 · Random Forest · SVM-RBF · Histéresis Schmitt-trigger · Validación LOPO
      </p>
    </footer>
  )
}
