from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import tempfile as _tempfile
import os
import sys
import shutil
import numpy as np
import mne
import uuid
import json
# Usar el directorio temporal del sistema operativo para evitar que 
# Uvicorn StatReload detecte cambios y reinicie el servidor constantemente.
UPLOAD_DIR = os.path.join(_tempfile.gettempdir(), "eeg_seizure_detection_tmp")

# Solo crear el directorio si no existe (NO borrar archivos existentes,
# porque Uvicorn --reload reinicia este módulo cada vez que detecta cambios
# y borraría el EDF que el usuario acaba de subir).
os.makedirs(UPLOAD_DIR, exist_ok=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.api.inference import process_and_predict_edf
from src.preprocessing.filters import butter_bandpass_filter
from src.features.stft_features import compute_stft_per_channel
from src.features.dwt_features import compute_dwt_energy_per_channel
from src.features.lpc_features import compute_lpc_per_channel

app = FastAPI(title="EEG Seizure Detection API")

# Permitir requests desde React (localhost:5173 y red local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "API is running. Use /predict or /analyze to upload an EDF file."}

@app.post("/predict")
async def predict_edf(file: UploadFile = File(...)):
    if not file.filename.endswith('.edf'):
        raise HTTPException(status_code=400, detail="Only .edf files are supported.")

    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(suffix=".edf")
        with os.fdopen(fd, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)

        results = process_and_predict_edf(temp_path)
        os.remove(temp_path)
        return JSONResponse(content=results)

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_edf(file: UploadFile = File(...)):
    """
    Endpoint de Analisis de Senales.
    Aplica pipeline DSP completo (Butterworth 0.5-40Hz, ventana Hanning 1s/50%)
    y calcula STFT, DWT (energia A5/D5/D4/D3) y LPC (12 coeficientes).
    Devuelve los datos para visualizacion en el frontend.
    """
    if not file.filename.endswith('.edf'):
        raise HTTPException(status_code=400, detail="Only .edf files are supported.")

    temp_path = None
    try:
        file_id = str(uuid.uuid4())
        temp_path = os.path.join(UPLOAD_DIR, f"{file_id}.edf")
        with open(temp_path, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)

        print(f"[/analyze] Cargando EDF: {temp_path}")
        raw = mne.io.read_raw_edf(temp_path, preload=False, verbose=False)

        if len(raw.ch_names) < 23:
            raise ValueError(f"El archivo debe tener al menos 23 canales. Se encontraron {len(raw.ch_names)}.")

        data_cruda = raw.get_data(picks=range(23))
        fs = int(raw.info['sfreq'])
        ch_names = [raw.ch_names[i] for i in range(23)]

        print(f"[/analyze] fs={fs}Hz, shape={data_cruda.shape}. Aplicando Butterworth 0.5-40Hz...")

        # Filtro Butterworth pasabanda 0.5-40Hz (sin Notch - redundante con highcut=40Hz)
        data_filtrada = np.zeros_like(data_cruda)
        for ch in range(23):
            data_filtrada[ch, :] = butter_bandpass_filter(
                data_cruda[ch, :], fs=fs, lowcut=0.5, highcut=40.0
            )

        window_samples = int(1.0 * fs)   # 1 segundo
        step_samples   = int(0.5 * fs)   # 50% overlap

        print("[/analyze] Calculando STFT...")
        stft_result = compute_stft_per_channel(data_filtrada, fs, window_samples, step_samples)

        print("[/analyze] Calculando DWT energias...")
        dwt_result = compute_dwt_energy_per_channel(data_filtrada, fs, window_samples, step_samples)

        print("[/analyze] Calculando LPC coeficientes...")
        lpc_result = compute_lpc_per_channel(data_filtrada, fs, window_samples, step_samples, order=12)

        # ── DOWNSAMPLING ──
        # Reduce la cantidad de puntos a un maximo de 800 para evitar que el JSON 
        # sea gigantesco (archivos de muchas horas pueden pesar 200MB de JSON puro).
        MAX_POINTS = 800
        n_windows = len(stft_result["times"])
        if n_windows > MAX_POINTS:
            step = max(1, n_windows // MAX_POINTS)
            print(f"[/analyze] Downsampling: reduciendo de {n_windows} a {n_windows//step} puntos (step={step}) para graficado.")
            
            stft_result["times"] = stft_result["times"][::step]
            dwt_result["times"] = dwt_result["times"][::step]
            lpc_result["times"] = lpc_result["times"][::step]
            
            for i in range(len(ch_names)):
                ch_key = f"ch{i}"
                # STFT
                stft_result["magnitudes"][ch_key] = [row[::step] for row in stft_result["magnitudes"][ch_key]]
                # DWT
                for sb in ["A5", "D5", "D4", "D3"]:
                    if sb in dwt_result["energy"][ch_key]:
                        dwt_result["energy"][ch_key][sb] = dwt_result["energy"][ch_key][sb][::step]
                # LPC
                # LPC
                lpc_result["coefficients"][ch_key] = lpc_result["coefficients"][ch_key][::step]

        # ── DOWNSAMPLING SEÑAL ORIGINAL ──
        total_samples = data_filtrada.shape[1]
        signal_step = max(1, total_samples // MAX_POINTS)
        signal_payload = {
            "times": (np.arange(0, total_samples, signal_step) / fs).tolist(),
            "amplitudes": {}
        }
        for i in range(len(ch_names)):
            # Escalar a microvoltios (MNE suele dar los datos en Volts)
            signal_payload["amplitudes"][f"ch{i}"] = (data_filtrada[i, ::signal_step] * 1e6).tolist()

        print("[/analyze] Analisis completado y serializando JSON...")

        return JSONResponse(content={
            "file_id": file_id,
            "channel_names": ch_names,
            "fs": fs,
            "duration_seconds": data_cruda.shape[1] / fs,
            "stft": stft_result,
            "dwt": dwt_result,
            "lpc": lpc_result,
            "signal": signal_payload,
        })

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        import traceback
        print(f"[/analyze] Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/zoom/{file_id}")
async def get_zoom(file_id: str, start: float, end: float):
    """
    Devuelve los datos procesados en ALTA RESOLUCION (sin downsampling)
    para un segmento especifico de tiempo.
    """
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.edf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found or expired.")

    try:
        print(f"[/segment] Cargando segmento {start}s - {end}s del archivo {file_id}")
        raw = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
        fs = int(raw.info['sfreq'])
        
        # Validar limites
        tmax_file = raw.times[-1]
        start = max(0.0, min(start, tmax_file))
        end = max(0.0, min(end, tmax_file))
        if start >= end:
            raise HTTPException(status_code=400, detail="Invalid time range")

        data_cruda, times = raw.get_data(picks=range(23), tmin=start, tmax=end, return_times=True)
        ch_names = [raw.ch_names[i] for i in range(23)]

        print(f"[/segment] Filtrando segmento de shape {data_cruda.shape}...")
        data_filtrada = np.zeros_like(data_cruda)
        for ch in range(23):
            data_filtrada[ch, :] = butter_bandpass_filter(data_cruda[ch, :], fs=fs, lowcut=0.5, highcut=40.0)

        window_samples = int(1.0 * fs)
        step_samples   = int(0.5 * fs)

        print("[/segment] Calculando STFT...")
        stft_result = compute_stft_per_channel(data_filtrada, fs, window_samples, step_samples)
        
        print("[/segment] Calculando DWT energias...")
        dwt_result = compute_dwt_energy_per_channel(data_filtrada, fs, window_samples, step_samples)
        
        print("[/segment] Calculando LPC coeficientes...")
        lpc_result = compute_lpc_per_channel(data_filtrada, fs, window_samples, step_samples, order=12)

        # Ajustar los tiempos devueltos (los compute_* asumen que la senal empieza en t=0)
        # Sumamos el 'start' a los tiempos relativos de la ventana
        stft_result["times"] = [t + start for t in stft_result["times"]]
        dwt_result["times"] = [t + start for t in dwt_result["times"]]
        lpc_result["times"] = [t + start for t in lpc_result["times"]]

        # Senal en crudo de alta resolucion
        signal_payload = {
            "times": times.tolist(),
            "amplitudes": {}
        }
        for i in range(len(ch_names)):
            signal_payload["amplitudes"][f"ch{i}"] = (data_filtrada[i, :] * 1e6).tolist()

        return JSONResponse(content={
            "file_id": file_id,
            "channel_names": ch_names,
            "fs": fs,
            "duration_seconds": end - start,
            "stft": stft_result,
            "dwt": dwt_result,
            "lpc": lpc_result,
            "signal": signal_payload,
        })

    except Exception as e:
        import traceback
        print(f"[/segment] Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Endpoints de Registros Históricos ─────────────────────────────────────────
HISTORY_DIR = os.path.join(os.path.dirname(__file__), '../../data/processed/history')

@app.get("/history/index")
async def history_index():
    """Devuelve el índice de pacientes históricos disponibles."""
    index_path = os.path.join(HISTORY_DIR, "index.json")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="No se encontraron registros históricos. Ejecute scripts/precompute_history.py primero.")
    with open(index_path, 'r', encoding='utf-8') as f:
        return JSONResponse(content=json.load(f))


@app.get("/history/{patient_id}/{record_type}")
async def history_record(patient_id: str, record_type: str):
    """Devuelve los datos pre-computados de un paciente histórico directamente comprimidos."""
    if record_type not in ("crisis", "no_crisis"):
        raise HTTPException(status_code=400, detail="record_type debe ser 'crisis' o 'no_crisis'")
    
    gz_path = os.path.join(HISTORY_DIR, f"{patient_id}_{record_type}.json.gz")
    if not os.path.exists(gz_path):
        raise HTTPException(status_code=404, detail=f"Registro no encontrado: {patient_id}_{record_type}")
    
    # Servimos el archivo directamente desde el disco.
    # Al enviarlo con Content-Encoding: gzip, el navegador del cliente lo descarga
    # y lo descomprime instantáneamente en memoria. Esto evita que el backend tenga que
    # abrir, decodificar el json de 80+ MB, y volver a codificarlo en cada peticion.
    return FileResponse(
        path=gz_path,
        media_type="application/json",
        headers={"Content-Encoding": "gzip"}
    )


@app.get("/history/zoom/{patient_id}/{record_type}")
async def history_zoom(patient_id: str, record_type: str, start: float, end: float):
    """Devuelve un segmento de la señal original de alta resolución para el registro histórico."""
    if record_type not in ("crisis", "no_crisis"):
        raise HTTPException(status_code=400, detail="record_type debe ser 'crisis' o 'no_crisis'")
        
    index_path = os.path.join(HISTORY_DIR, "index.json")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.json no encontrado")
        
    with open(index_path, 'r', encoding='utf-8') as f:
        idx_data = json.load(f)
        
    patient_info = next((p for p in idx_data if p["id"] == patient_id), None)
    if not patient_info:
        raise HTTPException(status_code=404, detail=f"Paciente {patient_id} no encontrado")
        
    file_name = patient_info[record_type]["file"]
    raw_path = os.path.abspath(os.path.join(HISTORY_DIR, "../../raw", patient_id, file_name))
    
    if not os.path.exists(raw_path):
        raise HTTPException(status_code=404, detail=f"Archivo raw {raw_path} no encontrado")

    try:
        raw = mne.io.read_raw_edf(raw_path, preload=False, verbose=False)
        fs = int(raw.info['sfreq'])
        
        tmax_file = raw.times[-1]
        start = max(0.0, min(start, tmax_file))
        end = max(0.0, min(end, tmax_file))
        if start >= end:
            raise HTTPException(status_code=400, detail="Rango de tiempo invalido")

        # Cargar solo el segmento y filtrar
        data_cruda, times = raw.get_data(picks=range(23), tmin=start, tmax=end, return_times=True)
        ch_names = [raw.ch_names[i] for i in range(23)]

        data_filtrada = np.zeros_like(data_cruda)
        for ch in range(23):
            data_filtrada[ch, :] = butter_bandpass_filter(data_cruda[ch, :], fs=fs, lowcut=0.5, highcut=40.0)

        # Downsampling inteligente para la vista del cliente (max 5000 puntos para que la linea no se sature)
        MAX_POINTS = 5000
        total_samples = data_filtrada.shape[1]
        step = max(1, total_samples // MAX_POINTS)

        signal_payload = {
            "times": times[::step].tolist(),
            "amplitudes": {}
        }
        for i in range(len(ch_names)):
            signal_payload["amplitudes"][f"ch{i}"] = (data_filtrada[i, ::step] * 1e6).tolist()

        return JSONResponse(content={"signal": signal_payload})

    except Exception as e:
        import traceback
        print(f"[/history/zoom] Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
