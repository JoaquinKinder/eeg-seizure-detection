# Ejemplo conceptual de integración de la etapa 2 completa:
from src.preprocessing.filters import eeg_condition_pipeline
from src.preprocessing.windowing import segment_eeg_signals

def preprocess_pipeline(raw_data, fs=256):
    # 1. Aplicar filtros pasa-banda y notch (Fase cero)
    filtered_data = eeg_condition_pipeline(raw_data, fs=fs)
    
    # 2. Aplicar el ventaneo de 1s con 50% de overlap
    eeg_windows = segment_eeg_signals(filtered_data, fs=fs, window_duration=1.0, overlap_percentage=0.5)
    
    return eeg_windows  # Salida lista para la DWT Daubechies-4