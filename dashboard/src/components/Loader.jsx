import styles from './Loader.module.css'

export default function Loader() {
  return (
    <div className={styles.loading}>
      <div className={styles.spinner} />
      <span>Cargando resultados...</span>
    </div>
  )
}
