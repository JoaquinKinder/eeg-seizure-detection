from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
import sys
import shutil
import numpy as np
import mne

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
        fd, temp_path = tempfile.mkstemp(suffix=".edf")
        with os.fdopen(fd, "wb") as f_out:
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
                lpc_result["coefficients"][ch_key] = lpc_result["coefficients"][ch_key][::step]

        os.remove(temp_path)
        print("[/analyze] Analisis completado y serializando JSON...")

        return JSONResponse(content={
            "channel_names": ch_names,
            "fs": fs,
            "duration_seconds": data_cruda.shape[1] / fs,
            "stft": stft_result,
            "dwt": dwt_result,
            "lpc": lpc_result,
        })

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        import traceback
        print(f"[/analyze] Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
