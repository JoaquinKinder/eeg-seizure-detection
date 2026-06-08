import { useState } from 'react'
import styles from './TimelineGallery.module.css'

export default function TimelineGallery({ patients }) {
  const [selectedPid, setSelectedPid] = useState(patients[0])
  const [imageError, setImageError] = useState(false)

  // Reset image error when patient changes
  const handleSelect = (pid) => {
    setSelectedPid(pid)
    setImageError(false)
  }

  const imageUrl = `/timelines/timeline_${selectedPid}.png`

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>⏱️ Línea de Tiempo de Predicciones</h2>
      <p className={styles.sectionDesc}>
        Visualización cronológica (Train/Test) para cada paciente evaluado.
        El panel superior muestra las crisis reales, el medio la probabilidad del modelo, y el inferior la detección final suavizada por histéresis.
      </p>

      <div className={styles.card}>
        <div className={styles.tabsWrapper}>
          <div className={styles.tabs}>
            {patients.map(pid => (
              <button
                key={pid}
                className={`${styles.tab} ${selectedPid === pid ? styles.active : ''}`}
                onClick={() => handleSelect(pid)}
              >
                {pid.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.imageContainer}>
          {imageError ? (
            <div className={styles.errorState}>
              <span className={styles.errorIcon}>🖼️</span>
              <p>Imagen no encontrada para <strong>{selectedPid}</strong></p>
              <p className={styles.errorSub}>Asegurate de haber ejecutado <code>python export_dashboard.py</code> para generar las imágenes.</p>
            </div>
          ) : (
            <img
              key={selectedPid} // force re-render animation
              src={imageUrl}
              alt={`Línea de tiempo para ${selectedPid}`}
              className={styles.image}
              onError={() => setImageError(true)}
            />
          )}
        </div>
      </div>
    </section>
  )
}
