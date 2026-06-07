# Ventaneo de 1 segundo (256 muestras) con solapamiento del 50%
import numpy as np

def segment_eeg_signals(data, fs=256, window_duration=1.0, overlap_percentage=0.5):
    """
    Segmenta una señal continua de EEG en ventanas temporales con solapamiento.
    
    Parameters:
    - data (ndarray): Matriz de la señal filtrada. 
                      Se asume forma (canales, muestras) o un vector unidimensional (muestras,).
    - fs (int): Frecuencia de muestreo (256 Hz para CHB-MIT).
    - window_duration (float): Duración de cada ventana en segundos (1.0 s).
    - overlap_percentage (float): Porcentaje de solapamiento (0.5 para 50%).
    
    Returns:
    - windows (ndarray): Matriz de ventanas segmentadas.
                         Si la entrada es multicanal, la forma será (ventanas, canales, muestras_por_ventana).
    """
    # Si la señal es unidimensional (un solo canal), le agregamos un eje para estandarizar
    if data.ndim == 1:
        data = np.expand_dims(data, axis=0)
        
    num_channels, total_samples = data.shape
    
    samples_per_window = int(window_duration * fs)                  # 256 muestras
    step_size = int(samples_per_window * (1.0 - overlap_percentage)) # 128 muestras
    
    # Calcular cuántas ventanas completas entran en la señal total
    num_windows = int((total_samples - samples_per_window) / step_size) + 1
    
    if num_windows <= 0:
        raise ValueError("La señal es demasiado corta para el tamaño de ventana especificado.")
        
    # Pre-asignar memoria para optimizar el rendimiento de Python
    windows = np.zeros((num_windows, num_channels, samples_per_window))
    
    # Extraer las ventanas deslizando el paso temporal
    for w in range(num_windows):
        start_idx = w * step_size
        end_idx = start_idx + samples_per_window
        windows[w, :, :] = data[:, start_idx:end_idx]
        
    # Si entró un solo canal, removemos la dimensión extra para comodidad del usuario
    if num_channels == 1:
        windows = np.squeeze(windows, axis=1)
        
    return windows
import numpy as np

def window_labels_by_vote(y_samples, window_size=256, overlap=128):
    """
    Segmenta el vector de etiquetas muestra a muestra y asigna una única 
    etiqueta por ventana mediante voto mayoritario (un umbral del 50%).
    """
    total_samples = len(y_samples)
    step = window_size - overlap
    
    # Calcular cuántas ventanas enteras entran en el registro
    num_windows = (total_samples - window_size) // step + 1
    y_windows = np.zeros(num_windows, dtype=int)
    
    for i in range(num_windows):
        start_idx = i * step
        end_idx = start_idx + window_size
        
        # Extraemos las 256 etiquetas de este bloque
        window_segment = y_samples[start_idx:end_idx]
        
        # Si más de la mitad del bloque (128 muestras) es crisis, la ventana es 1
        if np.sum(window_segment) > (window_size / 2):
            y_windows[i] = 1
            
    return y_windows