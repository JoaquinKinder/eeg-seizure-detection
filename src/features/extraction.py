# Extracción de DWT Daubechies-4 (db4) a 4-5 niveles
# Cálculo de: Energía relativa, Varianza y Entropía por sub-banda
import numpy as np
import pywt

def compute_shannon_entropy(coefficients):
    """Calcula la entropía de Shannon sobre la distribución de energía."""
    energy = coefficients ** 2
    total_energy = np.sum(energy)
    
    if total_energy == 0:
        return 0.0
        
    # Distribución de probabilidad de la energía
    p = energy / total_energy
    # Evitar log(0) añadiendo un epsilon
    entropy = -np.sum(p * np.log2(p + 1e-12))
    return entropy

def extract_wavelet_features_from_window(window_data, wavelet='db4', level=5):
    """
    Extrae Energía Relativa, Varianza y Entropía de las sub-bandas D3, D4, D5 y A5.
    
    Parameters:
    - window_data (ndarray): Matriz de una ventana de EEG, forma (canales, muestras_256)
    
    Returns:
    - feature_vector (ndarray): Vector de características plano para la ventana.
    """
    num_channels, _ = window_data.shape
    channel_features = []
    
    for ch in range(num_channels):
        # 1. Aplicar DWT Daubechies-4 a 5 niveles usando Mallat
        coeffs = pywt.wavedec(window_data[ch, :], wavelet, level=level)
        
        # wavedec devuelve: [A5, D5, D4, D3, D2, D1]
        a5, d5, d4, d3, d2, d1 = coeffs
        
        # Mapeamos las sub-bandas de interés (D3, D4, D5 y A5)
        subbands = {
            'A5': a5,
            'D5': d5,
            'D4': d4,
            'D3': d3
        }
        
        # Calcular la energía total de la ventana (usando todas las sub-bandas para normalizar)
        total_energy = sum(np.sum(c ** 2) for c in coeffs)
        
        # Extraer los 3 rasgos para cada una de las 4 sub-bandas seleccionadas
        for name, subband_coeffs in subbands.items():
            # Descriptor 1: Energía Relativa
            sb_energy = np.sum(subband_coeffs ** 2)
            relative_energy = sb_energy / (total_energy + 1e-12)
            
            # Descriptor 2: Varianza
            variance = np.var(subband_coeffs)
            
            # Descriptor 3: Entropía de Shannon
            entropy = compute_shannon_entropy(subband_coeffs)
            
            # Agregar descriptores al pozo del canal
            channel_features.extend([relative_energy, variance, entropy])
            
    return np.array(channel_features)

def extract_features_pipeline(windows_data):
    """
    Procesa todas las ventanas de la señal y devuelve la matriz de características X.
    Forma de salida: (num_ventanas, num_canales * 4_subbandas * 3_descriptores)
    """
    # SOLUCIÓN: Si viene en 2D (caso de 1 solo canal), le devolvemos la dimensión del canal
    if windows_data.ndim == 2:
        # Pasa de (ventanas, muestras) a (ventanas, 1_canal, muestras)
        windows_data = np.expand_dims(windows_data, axis=1)

    num_windows = windows_data.shape[0]
    features_list = []
    
    for w in range(num_windows):
        # Ahora sí, windows_data[w, :, :] siempre va a tener 3 dimensiones válidas
        window_feat = extract_wavelet_features_from_window(windows_data[w, :, :])
        features_list.append(window_feat)
        
    return np.array(features_list)