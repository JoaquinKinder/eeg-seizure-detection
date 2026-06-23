import { useState, useEffect, useRef, useCallback } from 'react'
import Plot from 'react-plotly.js'
import styles from './ProcessingPage.module.css'

const CHANNEL_OPTIONS = Array.from({ length: 23 }, (_, i) => `ch${i}`)

function ChannelSelector({ channels, value, onChange }) {
  const currentIdx = parseInt(value.replace('ch', ''), 10)
  const currentName = channels[currentIdx] || value
  const maxIdx = channels.length > 0 ? channels.length - 1 : 1
  const percentage = (currentIdx / maxIdx) * 100

  return (
    <div className={styles.sliderWrap}>
      <div className={styles.sliderHeader}>
        <span className={styles.selectorLabel}>Canal:</span>
        <span className={styles.channelBadge}>
          <span className={styles.channelDot} />
          {currentName} <span className={styles.channelIdx}>(ch{currentIdx})</span>
        </span>
      </div>
      <div className={styles.sliderRow}>
        <span className={styles.sliderEdge}>ch0</span>
        <input
          type="range"
          min={0}
          max={maxIdx}
          step={1}
          value={currentIdx}
          onChange={e => onChange(`ch${e.target.value}`)}
          className={styles.rangeSlider}
          style={{
            background: `linear-gradient(to right, var(--accent-blue) ${percentage}%, rgba(5, 150, 105, 0.15) ${percentage}%)`
          }}
        />
        <span className={styles.sliderEdge}>ch{maxIdx}</span>
      </div>
    </div>
  )
}


// ─── STFT Panel ──────────────────────────────────────────────────────────────
function StftPanel({ data, signalData, channelNames, seizureMarker, onRelayout }) {
  const [selCh, setSelCh] = useState('ch0')
  const [showSignal, setShowSignal] = useState(true)

  const magnitudes = data.magnitudes[selCh] || []
  const zData = magnitudes

  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>STFT — Espectrograma</h2>
      <p className={styles.panelDesc}>
        Transformada de Fourier de Tiempo Corto · Ventana Hanning 1s · Solapamiento 50%
      </p>

      <div className={styles.controlsRow}>
        <div style={{ flex: 1 }}>
          <ChannelSelector channels={channelNames} value={selCh} onChange={setSelCh} />
        </div>
        <div className={styles.toggleWrap}>
          <span className={styles.toggleInactive}>Ver Señal Original</span>
          <label className={styles.switch}>
            <input type="checkbox" checked={showSignal} onChange={e => setShowSignal(e.target.checked)} />
            <span className={styles.slider} />
          </label>
        </div>
      </div>

      <div className={styles.plotWrap}>
        <Plot
          data={[
            {
              type: 'heatmap',
              z: zData,
              x: data.times,
              y: data.freqs,
              colorscale: 'Viridis',
              colorbar: { title: 'Magnitud', x: 1.15 },
            },
            ...(showSignal && signalData ? [{
              type: 'scatter',
              mode: 'lines',
              x: signalData.times,
              y: signalData.amplitudes[selCh],
              yaxis: 'y2',
              line: { color: '#2d7f7f', width: 1.5 },
              name: 'Señal original'
            }] : [])
          ]}
          layout={{
            paper_bgcolor: 'transparent',
            plot_bgcolor: '#f8fafc',
            font: { color: '#1e293b', family: 'Inter' },
            xaxis: { title: 'Tiempo (s)', gridcolor: 'rgba(0,0,0,0.05)' },
            yaxis: {
              title: 'Frecuencia (Hz)',
              gridcolor: 'rgba(0,0,0,0.05)',
              domain: showSignal ? [0, 0.7] : [0, 1]
            },
            ...(showSignal ? {
              yaxis2: {
                title: 'Amplitud (µV)',
                domain: [0.75, 1],
                showgrid: true,
                gridcolor: 'rgba(0,0,0,0.05)',
                zeroline: true
              }
            } : {}),
            margin: { t: 30, l: 60, r: 20, b: 50 },
            autosize: true,
            shapes: seizureMarker ? [{
              type: 'rect',
              xref: 'x',
              yref: 'paper',
              x0: seizureMarker.start,
              x1: seizureMarker.end,
              y0: 0,
              y1: 1,
              fillcolor: 'rgba(214, 59, 70, 0.15)',
              line: { color: 'rgba(214, 59, 70, 0.8)', width: 2, dash: 'dashdot' }
            }] : []
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%', height: '380px' }}
          useResizeHandler
          onRelayout={onRelayout}
        />
      </div>
    </section>
  )
}


// ─── DWT Panel ───────────────────────────────────────────────────────────────
function DwtPanel({ data, signalData, channelNames, seizureMarker, onRelayout }) {
  const [selCh, setSelCh] = useState('ch0')
  const [mode3d, setMode3d] = useState(false)
  const [showSignal, setShowSignal] = useState(false)

  const chEnergy = data.energy[selCh] || {}
  const subbands = data.subbands || ['A5', 'D5', 'D4', 'D3']
  const times = data.times || []
  const zMatrix = subbands.map(sb => chEnergy[sb] || [])

  const plot2d = (
    <Plot
      data={[
        {
          type: 'heatmap',
          z: zMatrix,
          x: times,
          y: subbands,
          colorscale: 'Hot',
          colorbar: { title: 'Energía', x: 1.15 },
        },
        ...(showSignal && signalData ? [{
          type: 'scatter',
          mode: 'lines',
          x: signalData.times,
          y: signalData.amplitudes[selCh],
          yaxis: 'y2',
          line: { color: '#2d7f7f', width: 1.5 },
          name: 'Señal original'
        }] : [])
      ]}
      layout={{
        paper_bgcolor: 'transparent',
        plot_bgcolor: '#f8fafc',
        font: { color: '#1e293b', family: 'Inter' },
        xaxis: { title: 'Tiempo (s)', gridcolor: 'rgba(0,0,0,0.05)' },
        yaxis: {
          title: 'Sub-banda',
          gridcolor: 'rgba(0,0,0,0.05)',
          autorange: 'reversed',
          domain: showSignal ? [0, 0.7] : [0, 1]
        },
        ...(showSignal ? {
          yaxis2: {
            title: 'Amplitud (µV)',
            domain: [0.75, 1],
            showgrid: true,
            gridcolor: 'rgba(0,0,0,0.05)',
            zeroline: true
          }
        } : {}),
        margin: { t: 30, l: 60, r: 80, b: 50 },
        autosize: true,
        shapes: seizureMarker ? [{
          type: 'rect',
          xref: 'x',
          yref: 'paper',
          x0: seizureMarker.start,
          x1: seizureMarker.end,
          y0: 0,
          y1: 1,
          fillcolor: 'rgba(214, 59, 70, 0.15)',
          line: { color: 'rgba(214, 59, 70, 0.8)', width: 2, dash: 'dashdot' }
        }] : []
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%', height: '340px' }}
      useResizeHandler
      onRelayout={onRelayout}
    />
  )

  const plot3d = (
    <Plot
      data={[{
        type: 'surface',
        z: zMatrix,
        x: times,
        y: subbands,
        colorscale: 'Hot',
        colorbar: { title: 'Energía' },
      }]}
      layout={{
        paper_bgcolor: 'transparent',
        font: { color: '#1e293b', family: 'Inter' },
        scene: {
          xaxis: { title: 'Tiempo (s)', gridcolor: 'rgba(0,0,0,0.1)', color: '#475569' },
          yaxis: { title: 'Sub-banda', gridcolor: 'rgba(0,0,0,0.1)', color: '#475569' },
          zaxis: { title: 'Energía', gridcolor: 'rgba(0,0,0,0.1)', color: '#475569' },
          bgcolor: '#f8fafc',
        },
        margin: { t: 20, l: 0, r: 0, b: 0 },
        autosize: true,
      }}
      config={{ responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['toImage'] }}
      style={{ width: '100%', height: '480px' }}
      useResizeHandler
      onRelayout={onRelayout}
    />
  )

  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>DWT — Energía por Sub-banda</h2>
      <p className={styles.panelDesc}>
        Transformada Wavelet Discreta · Descomposición A5/D5/D4/D3
      </p>

      <div className={styles.controlsRow}>
        <div style={{ flex: 1 }}>
          <ChannelSelector channels={channelNames} value={selCh} onChange={setSelCh} />
        </div>
        <div className={styles.toggleWrap}>
          <span className={styles.toggleInactive}>Ver Señal Original</span>
          <label className={styles.switch}>
            <input type="checkbox" checked={showSignal} onChange={e => setShowSignal(e.target.checked)} disabled={mode3d} />
            <span className={styles.slider} />
          </label>
        </div>
        <div className={styles.toggleWrap}>
          <span className={!mode3d ? styles.toggleActive : styles.toggleInactive}>2D</span>
          <label className={styles.switch}>
            <input type="checkbox" checked={mode3d} onChange={e => setMode3d(e.target.checked)} />
            <span className={styles.slider} />
          </label>
          <span className={mode3d ? styles.toggleActive : styles.toggleInactive}>3D</span>
        </div>
      </div>

      <div className={styles.plotWrap}>
        {mode3d ? plot3d : plot2d}
      </div>
    </section>
  )
}


// ─── LPC Panel ───────────────────────────────────────────────────────────────
function LpcPanel({ data, signalData, channelNames, seizureMarker, onRelayout }) {
  const [selCh, setSelCh] = useState('ch0')
  const [mode3d, setMode3d] = useState(false)
  const [showSignal, setShowSignal] = useState(false)

  const coeffs = data.coefficients[selCh] || []
  const times = data.times || []
  const rawMatrix = coeffs.length > 0 && coeffs[0]?.length
    ? Array.from({ length: coeffs[0].length }, (_, ci) => coeffs.map(row => row[ci]))
    : []

  const yLabels = rawMatrix.map((_, i) => `a${i + 1}`)

  // Compute z-scores for normalization
  let zScored = rawMatrix
  if (rawMatrix.length > 0) {
    zScored = rawMatrix.map(row => {
      const mean = row.reduce((a, b) => a + b, 0) / row.length
      const std = Math.sqrt(row.reduce((a, b) => a + (b - mean) ** 2, 0) / row.length) || 1
      return row.map(v => (v - mean) / std)
    })
  }

  const plot2d = (
    <Plot
      data={[
        {
          type: 'heatmap',
          z: zScored,
          x: times,
          y: yLabels,
          colorscale: [
            [0, '#1a237e'],
            [0.2, '#4fc3f7'],
            [0.4, '#e0f7fa'],
            [0.5, '#fffde7'],
            [0.6, '#ffb74d'],
            [0.8, '#e53935'],
            [1.0, '#7b1fa2'],
          ],
          cmin: -3,
          cmax: 3,
          colorbar: { title: 'Z-score', x: 1.15 },
        },
        ...(showSignal && signalData ? [{
          type: 'scatter',
          mode: 'lines',
          x: signalData.times,
          y: signalData.amplitudes[selCh],
          yaxis: 'y2',
          line: { color: '#2d7f7f', width: 1.5 },
          name: 'Señal original'
        }] : [])
      ]}
      layout={{
        paper_bgcolor: 'transparent',
        plot_bgcolor: '#f8fafc',
        font: { color: '#1e293b', family: 'Inter' },
        xaxis: { title: 'Tiempo (s)', gridcolor: 'rgba(0,0,0,0.05)' },
        yaxis: {
          title: 'Coeficiente',
          gridcolor: 'rgba(0,0,0,0.05)',
          domain: showSignal ? [0, 0.7] : [0, 1]
        },
        ...(showSignal ? {
          yaxis2: {
            title: 'Amplitud (µV)',
            domain: [0.75, 1],
            showgrid: true,
            gridcolor: 'rgba(0,0,0,0.05)',
            zeroline: true
          }
        } : {}),
        margin: { t: 30, l: 60, r: 80, b: 50 },
        autosize: true,
        shapes: seizureMarker ? [{
          type: 'rect',
          xref: 'x',
          yref: 'paper',
          x0: seizureMarker.start,
          x1: seizureMarker.end,
          y0: 0,
          y1: 1,
          fillcolor: 'rgba(214, 59, 70, 0.15)',
          line: { color: 'rgba(214, 59, 70, 0.8)', width: 2, dash: 'dashdot' }
        }] : []
      }}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: '100%', height: '340px' }}
      useResizeHandler
      onRelayout={onRelayout}
    />
  )

  const plot3d = (
    <Plot
      data={[{
        type: 'surface',
        z: zScored,
        x: times,
        y: yLabels,
        colorscale: [
          [0.0,  '#1a237e'],
          [0.2,  '#1565c0'],
          [0.4,  '#4fc3f7'],
          [0.5,  '#f5f5f5'],
          [0.6,  '#ffb74d'],
          [0.8,  '#e53935'],
          [1.0,  '#7b1fa2'],
        ],
        cmin: -3,
        cmax: 3,
        colorbar: { title: 'Z-score', x: 1.1 }
      }]}
      layout={{
        paper_bgcolor: 'transparent',
        plot_bgcolor: '#f8fafc',
        font: { color: '#1e293b', family: 'Inter' },
        margin: { t: 20, l: 0, r: 0, b: 0 },
        autosize: true,
      }}
      config={{ responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['toImage'] }}
      style={{ width: '100%', height: '480px' }}
      useResizeHandler
      onRelayout={onRelayout}
    />
  )

  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>LPC — Coeficientes de Predicción Lineal</h2>
      <p className={styles.panelDesc}>
        Linear Predictive Coding · Orden 12
      </p>

      <div className={styles.controlsRow}>
        <div style={{ flex: 1 }}>
          <ChannelSelector channels={channelNames} value={selCh} onChange={setSelCh} />
        </div>
        <div className={styles.toggleWrap}>
          <span className={styles.toggleInactive}>Ver Señal Original</span>
          <label className={styles.switch}>
            <input type="checkbox" checked={showSignal} onChange={e => setShowSignal(e.target.checked)} disabled={mode3d} />
            <span className={styles.slider} />
          </label>
        </div>
        <div className={styles.toggleWrap}>
          <span className={!mode3d ? styles.toggleActive : styles.toggleInactive}>2D</span>
          <label className={styles.switch}>
            <input type="checkbox" checked={mode3d} onChange={e => setMode3d(e.target.checked)} />
            <span className={styles.slider} />
          </label>
          <span className={mode3d ? styles.toggleActive : styles.toggleInactive}>3D</span>
        </div>
      </div>

      <div className={styles.plotWrap}>
        {mode3d ? plot3d : plot2d}
      </div>
    </section>
  )
}


// ─── Main History Page ───────────────────────────────────────────────────────
export default function HistoryPage() {
  const [patients, setPatients] = useState([])
  const [selectedPatient, setSelectedPatient] = useState(null)
  const [recordType, setRecordType] = useState('crisis')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [zoomedSignal, setZoomedSignal] = useState(null)
  const [isZooming, setIsZooming] = useState(false)

  const ignoreRelayoutUntilRef = useRef(0)
  const currentPatientRef = useRef(null)

  useEffect(() => {
    currentPatientRef.current = { id: selectedPatient?.id, type: recordType }
  }, [selectedPatient, recordType])

  const handleRelayout = useCallback(async (event) => {
    if (Date.now() < ignoreRelayoutUntilRef.current) return;

    const pt = currentPatientRef.current;
    if (!pt || !pt.id) return;

    let start = undefined;
    let end = undefined;
    let isAutorange = Object.keys(event).some(k => k.includes('autorange') && event[k] === true);

    for (const key in event) {
      if (key === 'xaxis.range[0]') start = parseFloat(event[key]);
      if (key === 'xaxis.range[1]') end = parseFloat(event[key]);
      if (key === 'xaxis.range' && Array.isArray(event[key])) {
        start = parseFloat(event[key][0]);
        end = parseFloat(event[key][1]);
      }
    }

    if (isAutorange) {
      ignoreRelayoutUntilRef.current = Date.now() + 1000;
      setZoomedSignal(null);
      return;
    }

    if (start !== undefined && end !== undefined && !isNaN(start) && !isNaN(end)) {
      const windowSize = end - start;
      if (windowSize <= 600) {
        setIsZooming(true);
        try {
          const res = await fetch(`/api/history/zoom/${pt.id}/${pt.type}?start=${start}&end=${end}`);
          if (res.ok) {
            const highResData = await res.json();
            ignoreRelayoutUntilRef.current = Date.now() + 1000;
            setZoomedSignal(highResData.signal);
          }
        } catch (err) {
          console.error("Zoom fetch error", err);
        } finally {
          setIsZooming(false);
        }
      } else {
        ignoreRelayoutUntilRef.current = Date.now() + 1000;
        setZoomedSignal(null);
      }
    }
  }, []);

  // Cargar índice de pacientes al montar
  useEffect(() => {
    fetch('/api/history/index')
      .then(r => {
        if (!r.ok) throw new Error(`El backend respondió con error ${r.status}. ¿Está corriendo el servidor en el puerto 8000?`)
        return r.json()
      })
      .then(data => {
        setPatients(data)
        if (data.length > 0) setSelectedPatient(data[0])
      })
      .catch(err => setError('No se pudo cargar el índice de pacientes: ' + err.message))
  }, [])

  // Cargar registro cuando cambia paciente o tipo
  useEffect(() => {
    if (!selectedPatient) return

    setLoading(true)
    setError(null)
    setResults(null)
    setZoomedSignal(null)

    fetch(`/api/history/${selectedPatient.id}/${recordType}`)
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => {
        setResults(data)
      })
      .catch(err => setError('Error cargando registro: ' + err.message))
      .finally(() => setLoading(false))
  }, [selectedPatient, recordType])

  const channelNames = results?.channel_names || CHANNEL_OPTIONS

  const seizureMarker = recordType === 'crisis' && selectedPatient?.crisis
    ? { start: selectedPatient.crisis.seizure_start, end: selectedPatient.crisis.seizure_end }
    : null

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Registros Historicos</h1>
        <p className={styles.subtitle}>
          Analisis pre-computado de 6 pacientes del dataset CHB-MIT. Selecciona un paciente y tipo de registro para visualizar las transformadas STFT, DWT y LPC.
        </p>
      </header>

      <main className={styles.main}>
        {/* Patient Selector */}
        <section className={styles.panel} style={{ padding: '20px 28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
              Paciente:
            </span>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {patients.map(p => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPatient(p)}
                  style={{
                    padding: '8px 18px',
                    borderRadius: 20,
                    border: selectedPatient?.id === p.id ? '2px solid var(--accent-blue)' : '1px solid var(--border)',
                    background: selectedPatient?.id === p.id ? 'rgba(5, 150, 105, 0.12)' : 'transparent',
                    color: selectedPatient?.id === p.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
                    fontWeight: selectedPatient?.id === p.id ? 700 : 500,
                    fontSize: 13,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    fontFamily: "'Inter', sans-serif",
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <button
                onClick={() => setRecordType('crisis')}
                style={{
                  padding: '8px 20px',
                  borderRadius: 20,
                  border: recordType === 'crisis' ? '2px solid #d63b46' : '1px solid var(--border)',
                  background: recordType === 'crisis' ? 'rgba(214, 59, 70, 0.12)' : 'transparent',
                  color: recordType === 'crisis' ? '#d63b46' : 'var(--text-secondary)',
                  fontWeight: recordType === 'crisis' ? 700 : 500,
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  fontFamily: "'Inter', sans-serif",
                }}
              >
                Con Crisis
              </button>
              <button
                onClick={() => setRecordType('no_crisis')}
                style={{
                  padding: '8px 20px',
                  borderRadius: 20,
                  border: recordType === 'no_crisis' ? '2px solid var(--accent-blue)' : '1px solid var(--border)',
                  background: recordType === 'no_crisis' ? 'rgba(5, 150, 105, 0.12)' : 'transparent',
                  color: recordType === 'no_crisis' ? 'var(--accent-blue)' : 'var(--text-secondary)',
                  fontWeight: recordType === 'no_crisis' ? 700 : 500,
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  fontFamily: "'Inter', sans-serif",
                }}
              >
                Sin Crisis
              </button>
            </div>
          </div>

          {selectedPatient && (
            <div className={styles.metaBar} style={{ marginTop: 12 }}>
              <span>Archivo: {recordType === 'crisis' ? selectedPatient.crisis.file : selectedPatient.no_crisis.file}</span>
              {results && <span>Duracion: {results.duration_seconds.toFixed(1)}s ({(results.duration_seconds / 3600).toFixed(2)}h)</span>}
              {results && <span>Frecuencia: {results.fs} Hz · {results.channel_names?.length || 23} canales</span>}
              {seizureMarker && (
                <span style={{ color: '#d63b46', fontWeight: 600 }}>
                  Crisis: {seizureMarker.start}s - {seizureMarker.end}s
                </span>
              )}
            </div>
          )}
        </section>

        {/* Loading / Error */}
        {loading && (
          <div className={styles.loadingBox}>
            <div className={styles.spinner} />
            <p>Cargando registro pre-computado...</p>
          </div>
        )}
        {error && <div className={styles.errorAlert}>{error}</div>}

        {/* Results */}
        {results && !loading && (
          <div className={styles.results}>
            {isZooming && (
              <div style={{ padding: '8px 16px', background: 'rgba(5, 150, 105, 0.1)', color: 'var(--accent-blue)', borderRadius: '8px', fontSize: '13px', fontWeight: 600, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className={styles.spinner} style={{ width: 14, height: 14, borderWidth: 2 }} /> Cargando señal original en alta resolución...
              </div>
            )}
            <StftPanel data={results.stft} signalData={zoomedSignal || results.signal} channelNames={channelNames} seizureMarker={seizureMarker} onRelayout={handleRelayout} />
            <DwtPanel data={results.dwt} signalData={zoomedSignal || results.signal} channelNames={channelNames} seizureMarker={seizureMarker} onRelayout={handleRelayout} />
            <LpcPanel data={results.lpc} signalData={zoomedSignal || results.signal} channelNames={channelNames} seizureMarker={seizureMarker} onRelayout={handleRelayout} />
          </div>
        )}
      </main>
    </div>
  )
}
