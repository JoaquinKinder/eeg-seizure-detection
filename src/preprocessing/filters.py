# Filtro pasa-banda Butterworth (0.5-45 Hz) y Notch (60 Hz) usando scipy.signal.filtfilt
import numpy as np
from scipy.signal import butter, iirnotch, filtfilt

def butter_bandpass_filter(data, lowcut, highcut, fs, order=4):
    """
    Aplica un filtro pasa-banda Butterworth de fase cero.
    
    Parameters:
    - data (ndarray): Señal de EEG (puede ser multicanal, forma: canales x muestras o muestras x canales).
    - lowcut (float): Frecuencia de corte inferior (e.g., 0.5 Hz).
    - highcut (float): Frecuencia de corte superior (e.g., 45 Hz).
    - fs (float): Frecuencia de muestreo de la señal (256 Hz para CHB-MIT).
    - order (int): Orden del filtro.
    """
    nyq = 0.5 * fs  # Frecuencia de Nyquist
    low = lowcut / nyq
    high = highcut / nyq
    
    # Diseñar el filtro (salida en coeficientes b, a)
    b, a = butter(order, [low, high], btype='band')
    
    # Aplicar filtfilt para garantizar fase cero (bidireccional)
    # axis=-1 asegura que filtre a lo largo del eje del tiempo
    y = filtfilt(b, a, data, axis=-1)
    return y

def notch_filter(data, notch_freq, fs, Q=30):
    """
    Aplica un filtro Notch (rechaza-banda) de fase cero para eliminar la interferencia de red.
    
    Parameters:
    - data (ndarray): Señal de EEG.
    - notch_freq (float): Frecuencia a atenuar (60 Hz para CHB-MIT).
    - fs (float): Frecuencia de muestreo (256 Hz).
    - Q (float): Factor de calidad (a mayor Q, más estrecha la banda de rechazo).
    """
    nyq = 0.5 * fs
    w0 = notch_freq / nyq
    
    # Diseñar filtro Notch IIR
    b, a = iirnotch(w0, Q)
    
    # Aplicar en fase cero
    y = filtfilt(b, a, data, axis=-1)
    return y

def eeg_condition_pipeline(data, fs=256.0):
    """
    Pipeline completo de acondicionamiento en cascada para CHB-MIT.
    Remueve deriva de línea base, ruido muscular (EMG) e interferencia de 60 Hz.
    """
    # 1. Pasa-banda 0.5 - 45 Hz (Orden 4)
    filtered_data = butter_bandpass_filter(data, lowcut=0.5, highcut=45.0, fs=fs, order=4)
    
    # 2. Notch 60 Hz
    conditioned_data = notch_filter(filtered_data, notch_freq=60.0, fs=fs)
    
    return conditioned_data