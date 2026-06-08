import styles from './MetaBar.module.css'

export default function MetaBar({ meta }) {
  const chips = [
    ['Generado', new Date(meta.generated_at).toLocaleString('es-AR')],
    ['Dataset', meta.dataset],
    ['Pacientes', meta.patients.length],
    ['Fs', `${meta.sampling_rate_hz} Hz`],
    ['Ventana', `${meta.window_duration_s}s · ${meta.overlap_pct}% overlap`],
    ['Wavelet', `${meta.wavelet} · ${meta.levels} niveles`],
    ['CV folds', meta.n_splits_cv],
  ]
  return (
    <div className={styles.bar}>
      {chips.map(([k, v]) => (
        <div className={styles.chip} key={k}>
          {k}: <strong>{v}</strong>
        </div>
      ))}
    </div>
  )
}
