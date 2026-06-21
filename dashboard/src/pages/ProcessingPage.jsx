import { useState, useCallback, useRef, useEffect } from 'react'
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
  const [showSignal, setShowSignal] = useState(false)

  const magnitudes = data.magnitudes[selCh] || []
  const zData = magnitudes

  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>📊 STFT — Espectrograma</h2>
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
            shapes: seizureMarker?.active && seizureMarker.start && seizureMarker.end ? [{
              type: 'rect',
              xref: 'x',
              yref: 'paper',
              x0: parseFloat(seizureMarker.start),
              x1: parseFloat(seizureMarker.end),
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

  // Build 2D z matrix: rows = subbands, cols = time windows
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
        margin: { t: 30, l: 60, r: 20, b: 50 },
        autosize: true,
        shapes: seizureMarker?.active && seizureMarker.start && seizureMarker.end ? [{
          type: 'rect',
          xref: 'x',
          yref: 'paper',
          x0: parseFloat(seizureMarker.start),
          x1: parseFloat(seizureMarker.end),
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
      <h2 className={styles.panelTitle}>🌊 DWT — Escalograma Wavelet</h2>
      <p className={styles.panelDesc}>
        Wavelet Daubechies-4 · 5 niveles · Sub-bandas D3/D4/D5/A5 · Energía por ventana
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

  const chCoeffs = data.coefficients[selCh] || []
  const coeffLabels = data.coeff_labels || []
  const times = data.times || []

  // Transpose: chCoeffs is [windows x 12] → z[coeff_idx][window_idx]
  const rawMatrix = coeffLabels.map((_, coeffIdx) =>
    chCoeffs.map(windowRow => windowRow[coeffIdx] ?? 0)
  )

  // Normalización Z-score por fila (coeficiente): cada fila usa su propio rango de color
  // Esto evita que a1 (el más grande) aplaste visualmente a los demás coeficientes
  const zMatrix = rawMatrix.map(row => {
    const mean = row.reduce((a, b) => a + b, 0) / row.length
    const std  = Math.sqrt(row.reduce((a, b) => a + (b - mean) ** 2, 0) / row.length)
    if (std === 0) return row.map(() => 0)
    return row.map(v => (v - mean) / std)
  })

  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>🔢 LPC — Coeficientes de Predicción Lineal</h2>
      <p className={styles.panelDesc}>
        12 coeficientes LPC · Algoritmo Levinson-Durbin · Ventana Hanning 1s · Solapamiento 50% · Normalización Z-score por coeficiente
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
        {!mode3d ? (
          <Plot
            data={[
              {
                type: 'heatmap',
                z: zMatrix,
                x: times,
                y: coeffLabels,
              colorscale: [
                [0.0,  '#1a237e'],
                [0.2,  '#1565c0'],
                [0.4,  '#4fc3f7'],
                [0.5,  '#f5f5f5'],
                [0.6,  '#ffb74d'],
                [0.8,  '#e53935'],
                [1.0,  '#7b1fa2'],
              ],
              zmid: 0,
              zmin: -3,
              zmax:  3,
              colorbar: {
                title: 'Z-score',
                tickvals: [-3, -2, -1, 0, 1, 2, 3],
                ticktext: ['-3σ', '-2σ', '-1σ', '0', '+1σ', '+2σ', '+3σ'],
                x: 1.15
              },
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
              shapes: seizureMarker?.active && seizureMarker.start && seizureMarker.end ? [{
                type: 'rect',
                xref: 'x',
                yref: 'paper',
                x0: parseFloat(seizureMarker.start),
                x1: parseFloat(seizureMarker.end),
                y0: 0,
                y1: 1,
                fillcolor: 'rgba(214, 59, 70, 0.15)',
                line: { color: 'rgba(214, 59, 70, 0.8)', width: 2, dash: 'dashdot' }
              }] : []
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '420px' }}
            useResizeHandler
            onRelayout={onRelayout}
          />
        ) : (
          <Plot
            data={[{
              type: 'surface',
              z: zMatrix,
              x: times,
              y: coeffLabels,
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
        )}
      </div>
    </section>
  )
}


// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ProcessingPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState(null)
  const [macroResults, setMacroResults] = useState(null)
  const [isZooming, setIsZooming] = useState(false)
  const [seizureMarker, setSeizureMarker] = useState({ start: '', end: '', active: false, showInput: false })

  const handleFileChange = useCallback(e => {
    if (e.target.files?.length > 0) {
      setFile(e.target.files[0])
      setResults(null)
      setMacroResults(null)
      setError(null)
    }
  }, [])

  const handleDrop = useCallback(e => {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0]
    if (f?.name.endsWith('.edf')) {
      setFile(f)
      setResults(null)
      setMacroResults(null)
      setError(null)
    }
  }, [])

  const handleAnalyze = async () => {
    if (!file) return
    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/analyze', { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Error en el análisis')
      }
      const data = await res.json()
      setResults(data)
      setMacroResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const [debugLog, setDebugLog] = useState("");
  const macroResultsRef = useRef(null);
  const ignoreRelayoutUntilRef = useRef(0);

  useEffect(() => {
    macroResultsRef.current = macroResults;
  }, [macroResults]);

  const handleRelayout = useCallback(async (event) => {
    // Cuando nosotros cambiamos los datos (setResults), los 3 paneles (STFT, DWT, LPC)
    // re-renderizan y cada uno dispara onRelayout. Bloqueamos TODOS durante 1 segundo
    // después de un cambio programático para evitar que reviertan los datos.
    if (Date.now() < ignoreRelayoutUntilRef.current) {
      return;
    }

    const currentMacro = macroResultsRef.current;
    if (!currentMacro || !currentMacro.file_id) {
      return;
    }

    let start = undefined;
    let end = undefined;
    let isAutorange = Object.keys(event).some(k => k.includes('autorange') && event[k] === true);

    for (const key in event) {
      if (key === 'xaxis.range[0]') start = parseFloat(event[key]);
      if (key === 'xaxis.range[1]') end = parseFloat(event[key]);
    }

    if (isAutorange) {
      ignoreRelayoutUntilRef.current = Date.now() + 1000;
      setResults(currentMacro);
      return;
    }

    if (start !== undefined && end !== undefined && !isNaN(start) && !isNaN(end)) {
      const windowSize = end - start;
      if (windowSize <= 600) {
        setIsZooming(true);
        try {
          const res = await fetch(`/api/zoom/${currentMacro.file_id}?start=${start}&end=${end}`);
          if (res.ok) {
            const highResData = await res.json();
            ignoreRelayoutUntilRef.current = Date.now() + 1000;
            setResults(highResData);
          } else {
            console.error("Zoom error: status", res.status);
          }
        } catch (err) {
          console.error("Error fetching high-res segment:", err);
        } finally {
          setIsZooming(false);
        }
      }
    }
  }, []);

  const channelNames = results?.channel_names || CHANNEL_OPTIONS

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Análisis de Señal EEG</h1>
      </header>

      <main className={styles.main}>
        {/* Upload Zone */}
        <section className={styles.uploadSection}>
          <div
            className={styles.uploadBox}
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
          >
            <div className={styles.icon}>📁</div>
            <p>Seleccioná o arrastrá el archivo <strong>.edf</strong> del paciente</p>
            <input
              type="file"
              accept=".edf"
              onChange={handleFileChange}
              className={styles.fileInput}
              id="edf-upload"
            />
            <label htmlFor="edf-upload" className={styles.fileLabel}>
              Seleccionar archivo
            </label>
            {file && <p className={styles.fileName}>✅ {file.name}</p>}
          </div>

          <button
            className={styles.analyzeBtn}
            onClick={handleAnalyze}
            disabled={!file || loading}
          >
            {loading ? '⏳ Procesando...' : '▶ Analizar EEG'}
          </button>

          {loading && (
            <div className={styles.loadingBox}>
              <div className={styles.spinner} />
              <p>Aplicando Butterworth → Hanning → STFT · DWT · LPC</p>
              <p className={styles.loadingSub}>Esto puede tardar 1-2 minutos dependiendo del largo del archivo.</p>
            </div>
          )}
          {error && <div className={styles.errorAlert}>❌ {error}</div>}
        </section>

        {/* Results */}
        {results && (
          <div className={styles.results}>
            <div className={styles.metaBar}>
              <span>📄 {file.name}</span>
              <span>⏱ {results.duration_seconds.toFixed(1)}s ({(results.duration_seconds / 3600).toFixed(2)}h)</span>
              <span>📡 {results.fs} Hz · 23 canales</span>
            </div>

            <div className={styles.markerControls}>
              {!seizureMarker.showInput ? (
                <button 
                  className={styles.markerBtn} 
                  onClick={() => setSeizureMarker(s => ({...s, showInput: true}))}
                >
                  📍 Añadir marcador de crisis
                </button>
              ) : (
                <div className={styles.markerInputs}>
                  <label>Inicio (s): <input type="number" min="0" value={seizureMarker.start} onChange={e => setSeizureMarker(s => ({...s, start: e.target.value}))} /></label>
                  <label>Fin (s): <input type="number" min="0" value={seizureMarker.end} onChange={e => setSeizureMarker(s => ({...s, end: e.target.value}))} /></label>
                  <button className={styles.markerBtnApply} onClick={() => setSeizureMarker(s => ({...s, active: true}))}>Aplicar</button>
                  <button className={styles.markerBtnCancel} onClick={() => setSeizureMarker({start:'', end:'', active:false, showInput:false})}>Cancelar</button>
                </div>
              )}
            </div>

            <StftPanel data={results.stft} signalData={results.signal} channelNames={channelNames} seizureMarker={seizureMarker} onRelayout={handleRelayout} />
            <DwtPanel data={results.dwt} signalData={results.signal} channelNames={channelNames} seizureMarker={seizureMarker} onRelayout={handleRelayout} />
            <LpcPanel data={results.lpc} signalData={results.signal} channelNames={channelNames} seizureMarker={seizureMarker} onRelayout={handleRelayout} />
          </div>
        )}

        {isZooming && (
          <div style={{ position: 'fixed', bottom: 20, right: 20, background: 'rgba(5, 150, 105, 0.9)', color: 'white', padding: '8px 16px', borderRadius: 20, fontSize: 13, fontWeight: 600, boxShadow: '0 4px 12px rgba(0,0,0,0.2)', zIndex: 100 }}>
            ⏳ Cargando alta resolución...
          </div>
        )}


      </main>
    </div>
  )
}
