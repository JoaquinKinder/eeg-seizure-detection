import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart
} from 'recharts'
import styles from './PredictPage.module.css'
import Footer from '../components/Footer'

export default function PredictPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)
  const [chartData, setChartData] = useState([])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
      setResults(null)
      setError(null)
    }
  }

  const handlePredict = async () => {
    if (!file) return

    setLoading(true)
    setError(null)
    setResults(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      // Usar la IP del servidor de FastAPI (por defecto localhost:8000)
      const res = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Error en la predicción')
      }

      const data = await res.json()
      setResults(data)

      // Transformar datos para Recharts
      const formattedData = data.time_seconds.map((t, i) => ({
        time: t / 3600.0, // Convertir a horas para consistencia
        probabilidad: data.probabilities[i],
        deteccion: data.predictions[i]
      }))
      setChartData(formattedData)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>🔍 Inferencia en Vivo</h1>
        <p className={styles.subtitle}>Sube un archivo crudo de EEG (.edf) para buscar crisis epilépticas con nuestro modelo RF de producción.</p>
      </header>

      <main className={styles.main}>
        <section className={styles.uploadSection}>
          <div className={styles.uploadBox}>
            <div className={styles.icon}>📁</div>
            <p>Selecciona o arrastra el archivo <strong>.edf</strong> del paciente</p>
            <input 
              type="file" 
              accept=".edf" 
              onChange={handleFileChange}
              className={styles.fileInput}
            />
            {file && <p className={styles.fileName}>Archivo seleccionado: {file.name}</p>}
          </div>

          <button 
            className={styles.predictBtn} 
            onClick={handlePredict}
            disabled={!file || loading}
          >
            {loading ? 'Procesando (puede tardar minutos)...' : 'Analizar EEG'}
          </button>
          
          {error && <div className={styles.errorAlert}>❌ {error}</div>}
        </section>

        {loading && (
          <div className={styles.loadingBox}>
            <div className={styles.spinner} />
            <p>Aplicando Pipeline (MNE -&gt; Wavelets db4 -&gt; Calibración de Línea Base -&gt; RF -&gt; Histéresis)...</p>
            <p className={styles.loadingSub}>El modelo se está auto-calibrando usando los primeros 5 minutos del paciente.</p>
          </div>
        )}

        {results && (
          <section className={styles.resultsSection}>
            <div className={styles.kpiBox}>
              <h3>Crisis Detectadas</h3>
              <div className={styles.kpiValue}>{results.seizures_detected}</div>
              <p>Ventanas positivas después del filtro de histéresis temporal.</p>
            </div>

            <div className={styles.chartWrapper}>
              <h3>Línea de Tiempo de Probabilidad</h3>
              <div className={styles.chart}>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorProb" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f6ad55" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#f6ad55" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="time" stroke="#8b9ab3" fontSize={12} tickFormatter={(tick) => tick.toFixed(2) + 'h'} />
                    <YAxis stroke="#8b9ab3" fontSize={12} domain={[0, 1]} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#e2e8f0' }}
                      labelFormatter={(label) => `Tiempo: ${label.toFixed(3)} horas`}
                    />
                    <ReferenceLine y={0.6} stroke="#fc8181" strokeDasharray="3 3" />
                    <ReferenceLine y={0.4} stroke="#68d391" strokeDasharray="3 3" />
                    <Area type="monotone" dataKey="probabilidad" stroke="#f6ad55" fillOpacity={1} fill="url(#colorProb)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <h3>Detección Final</h3>
              <div className={styles.chart}>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="time" stroke="#8b9ab3" fontSize={12} tickFormatter={(tick) => tick.toFixed(2) + 'h'} />
                    <YAxis stroke="#8b9ab3" fontSize={12} domain={[0, 1]} ticks={[0, 1]} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#e2e8f0' }}
                      labelFormatter={(label) => `Tiempo: ${label.toFixed(3)} horas`}
                    />
                    <Area type="step" dataKey="deteccion" stroke="#63b3ed" fillOpacity={0.3} fill="#63b3ed" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        )}
      </main>
      <Footer />
    </div>
  )
}
