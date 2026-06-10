import os
import numpy as np
import mne
from src.data.load_data import parse_summary_file, generate_labels_for_file
from src.preprocessing.filters import butter_bandpass_filter
from src.preprocessing.windowing import window_labels_by_vote
from src.features.extraction import extract_wavelet_features_from_window

def process_patient_batch(data_dir, patient_id, window_size=256, step=128):
    """
    Procesa todos los archivos .edf de un paciente, extrae rasgos Wavelet y 
    unifica todo en matrices X e y consolidadas.
    """
    patient_dir = os.path.join(data_dir, patient_id)
    summary_path = os.path.join(patient_dir, f"{patient_id}-summary.txt")
    
    # 1. Parsear el archivo de texto del paciente
    diccionario_crisis = parse_summary_file(summary_path)
    
    X_patient_list = []
    y_patient_list = []
    
    # Listar todos los archivos .edf reales en la carpeta
    edf_files = [f for f in os.listdir(patient_dir) if f.endswith('.edf')]
    edf_files.sort()
    
    print(f"\n=== PROCESANDO EN LOTE EL PACIENTE: {patient_id} ===")
    print(f"Se encontraron {len(edf_files)} archivos .edf para procesar.")
    
    for filename in edf_files:
        edf_path = os.path.join(patient_dir, filename)
        
        # Validación de seguridad: verificar que el archivo esté mapeado en el summary
        if filename not in diccionario_crisis:
            continue
            
        print(f"-> Masticando: {filename}...", end="", flush=True)
        
        try:
            # 2. Carga perezosa (preload=False) para proteger la RAM
            raw = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)
            
            # CHB-MIT a veces tiene variaciones de canales; nos aseguramos de usar los primeros 23 estándar
            # Si un archivo tiene menos canales por algún error, lo salteamos para no romper las dimensiones de X
            if len(raw.ch_names) < 23:
                print(" [Salteado: Menos de 23 canales]")
                continue
                
            # Levantamos los datos a memoria (solo los canales estándar)
            data_cruda = raw.get_data(picks=range(23))
            fs = int(raw.info['sfreq'])
            
            # 3. Filtrado digital multicanal
            data_filtrada = np.zeros_like(data_cruda)
            for ch in range(23):
                # Filtro Butterworth pasabanda 0.5-40 Hz (sin Notch - redundante con highcut=40Hz)
                data_filtrada[ch, :] = butter_bandpass_filter(data_cruda[ch, :], fs=fs, lowcut=0.5, highcut=40.0)
                
            # 4. Etiquetas muestra a muestra y colapso por votación a nivel ventana
            tiempos_crisis = diccionario_crisis[filename]
            y_muestras = generate_labels_for_file(data_cruda.shape[1], fs, tiempos_crisis)
            y_ventanas = window_labels_by_vote(y_muestras, window_size=window_size, overlap=step)
            
            # 5. Segmentación temporal y extracción Wavelet usando tu función
            total_samples = data_filtrada.shape[1]
            num_windows = (total_samples - window_size) // step + 1
            
            # Ajustamos por seguridad si hay un desajuste mínimo de redondeo con las etiquetas
            num_windows = min(num_windows, len(y_ventanas))
            
            lista_X_file = []
            for i in range(num_windows):
                start_idx = i * step
                end_idx = start_idx + window_size
                window_multicanal = data_filtrada[:, start_idx:end_idx]
                
                features_ventana = extract_wavelet_features_from_window(window_multicanal, wavelet='db4', level=5)
                lista_X_file.append(features_ventana)
                
            X_file = np.array(lista_X_file)
            y_file = y_ventanas[:num_windows]
            
            # Acumular en la lista del paciente
            X_patient_list.append(X_file)
            y_patient_list.append(y_file)
            print(f" OK | Ventanas: {len(y_file)} (Crisis: {np.sum(y_file == 1)})")
            
        except Exception as e:
            print(f" [ERROR al procesar archivo]: {e}")
            
    # Unificar todas las submatrices del paciente en una sola matriz robusta
    if len(X_patient_list) > 0:
        X_patient_total = np.vstack(X_patient_list)
        y_patient_total = np.concatenate(y_patient_list)
        return X_patient_total, y_patient_total
    else:
        return None, None