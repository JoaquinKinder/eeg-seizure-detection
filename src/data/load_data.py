import mne
import os
import re
import numpy as np

def load_edf_signal(edf_path):
    """
    Lee un archivo .edf de CHB-MIT utilizando MNE.
    Retorna la matriz de datos y la frecuencia de muestreo.
    """
    # preload=True carga los datos en RAM para poder manipularlos con NumPy al toque
    # verbose=False evita que la consola se llene de texto de MNE
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
    
    # Extraemos la matriz de señales (canales, muestras)
    data = raw.get_data()
    fs = int(raw.info['sfreq']) # Debería ser 256 Hz
    
    return data, fs, raw.ch_names

def generate_labels_for_file(total_samples, fs, seizure_windows_seconds):
    """
    Crea el vector de etiquetas binarias (y) basándose en los segundos anotados de crisis.
    
    Parameters:
    - total_samples (int): Muestras totales del archivo EDF.
    - fs (int): Frecuencia de muestreo (256).
    - seizure_windows_seconds (list of tuples): Lista con tuplas (inicio_seg, fin_seg) de las crisis.
    """
    # Inicializamos todo el registro como estado normal (0)
    y_labels = np.zeros(total_samples, dtype=int)
    
    # Marcamos con 1 los rangos de muestras donde hay crisis real
    for start_sec, end_sec in seizure_windows_seconds:
        start_sample = int(start_sec * fs)
        end_sample = int(end_sec * fs)
        
        # Resguardo para no pasarnos de los límites del archivo por redondeos
        end_sample = min(end_sample, total_samples)
        
        y_labels[start_sample:end_sample] = 1
        
    return y_labels

def parse_summary_file(summary_path):
    """
    Parsea el archivo chbXX-summary.txt y extrae los intervalos de crisis de cada archivo.
    
    Returns:
    - info_crisis (dict): Diccionario donde la clave es el nombre del archivo .edf 
                          y el valor es una lista de tuplas (inicio_seg, fin_seg).
    """
    info_crisis = {}
    current_file = None
    
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"No se encontró el archivo de resumen en: {summary_path}")
        
    with open(summary_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 1. Detectar el nombre del archivo EDF
            if line.startswith("File Name:"):
                current_file = line.split(":")[-1].strip()
                info_crisis[current_file] = []
                
            # 2. Detectar el inicio de una crisis
            elif "Start Time:" in line and "Seizure" in line:
                # Usamos expresiones regulares para sacar solo los números enteros
                segundos = re.findall(r'\d+', line)
                if segundos:
                    # El último número de la línea suele ser el tiempo en segundos
                    start_sec = int(segundos[-1])
                    # Guardamos temporalmente el inicio (usamos una lista auxiliar para armar la tupla después)
                    info_crisis[current_file].append([start_sec])
                    
            # 3. Detectar el fin de una crisis
            elif "End Time:" in line and "Seizure" in line:
                segundos = re.findall(r'\d+', line)
                if segundos and current_file in info_crisis and len(info_crisis[current_file]) > 0:
                    end_sec = int(segundos[-1])
                    # Agregamos el tiempo de fin al último registro abierto
                    info_crisis[current_file][-1].append(end_sec)
                    
    # Limpiamos el diccionario para convertir las listas internas en tuplas (inicio, fin)
    for filename in list(info_crisis.keys()):
        # Si el archivo no tuvo crisis, la lista estará vacía, lo cual es correcto (0 crisis)
        info_crisis[filename] = [tuple(intervalo) for intervalo in info_crisis[filename] if len(intervalo) == 2]
        
    return info_crisis