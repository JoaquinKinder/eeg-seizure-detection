import os
import tempfile
import numpy as np
import mne
import joblib
from sklearn.preprocessing import StandardScaler

from src.preprocessing.filters import notch_filter, butter_bandpass_filter
from src.features.extraction import extract_wavelet_features_from_window
from src.models.hysteresis import apply_hysteresis_logic

# Path to the trained global model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../models/rf_production.joblib')
_model = None

def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run train_production.py first.")
        _model = joblib.load(MODEL_PATH)
    return _model

def process_and_predict_edf(edf_path, window_size=256, step=128):
    """
    Procesa un archivo EDF crudo y devuelve la predicción cronológica.
    fs esperado: 256 Hz (CHB-MIT). 
    window_size=256 (1s) según el pipeline actual o depende de la parametrización de CHB-MIT (a menudo 1024 para 4s).
    Wait, in process_batch.py, window_size=256, step=128 which at 256Hz is 1s windows.
    Let's stick to the 256 and 128 as in process_batch.py
    """
    print(f"Cargando EDF: {edf_path}")
    raw = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)
    
    # CHB-MIT standard channels check
    if len(raw.ch_names) < 23:
        raise ValueError(f"El archivo debe tener al menos 23 canales. Se encontraron {len(raw.ch_names)}.")
        
    data_cruda = raw.get_data(picks=range(23))
    fs = int(raw.info['sfreq'])
    
    # Adaptar la ventana a 1s y paso de 0.5s (256 muestras, 128 overlap)
    # para coincidir exactamente con cómo se entrenó el modelo.
    window_size_samples = int(1.0 * fs)
    step_samples = int(0.5 * fs)
    
    print(f"Frecuencia de muestreo: {fs}Hz. Aplicando filtrado...")
    data_filtrada = np.zeros_like(data_cruda)
    for ch in range(23):
        sig_notch = notch_filter(data_cruda[ch, :], notch_freq=60.0, fs=fs)
        data_filtrada[ch, :] = butter_bandpass_filter(sig_notch, fs=fs, lowcut=0.5, highcut=30.0)
        
    total_samples = data_filtrada.shape[1]
    num_windows = (total_samples - window_size_samples) // step_samples + 1
    
    print(f"Extrayendo características Wavelet para {num_windows} ventanas...")
    lista_X_file = []
    for i in range(num_windows):
        start_idx = i * step_samples
        end_idx = start_idx + window_size_samples
        window_multicanal = data_filtrada[:, start_idx:end_idx]
        
        # wavelet features expect raw values or filtered, we use filtered
        features_ventana = extract_wavelet_features_from_window(window_multicanal, wavelet='db4', level=5)
        lista_X_file.append(features_ventana)
        
    X_file = np.array(lista_X_file)
    
    print("Ejecutando inferencia con Random Forest (Pipeline Global)...")
    clf = get_model()
    
    # Predicción de probabilidades usando el pipeline original (incluye StandardScaler global)
    y_pred_proba = clf.predict_proba(X_file)[:, 1]
    
    # Histéresis
    y_pred_smooth = apply_hysteresis_logic(
        y_pred_proba, 
        N_windows=3, 
        threshold_high=0.6, 
        threshold_low=0.4
    )
    
    # Armar la respuesta temporal
    # Calculamos el tiempo en segundos para cada ventana
    tiempo_segundos = np.arange(num_windows) * (step_samples / fs)
    
    # Convertimos numpy arrays a listas para JSON
    return {
        "time_seconds": tiempo_segundos.tolist(),
        "probabilities": y_pred_proba.tolist(),
        "predictions": y_pred_smooth.tolist(),
        "seizures_detected": int(np.sum(y_pred_smooth == 1))
    }
