"""
Pre-computa los resultados de análisis DSP para los 6 pacientes históricos.
Genera archivos JSON comprimidos (.json.gz) que el backend sirve directamente.

Uso:
    python scripts/precompute_history.py
"""
import os, sys, json, gzip
import numpy as np
import mne

# Agregar el root del proyecto al path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

from src.preprocessing.filters import butter_bandpass_filter
from src.features.stft_features import compute_stft_per_channel
from src.features.dwt_features import compute_dwt_energy_per_channel
from src.features.lpc_features import compute_lpc_per_channel

# ── Configuración de pacientes ──────────────────────────────────────────────
PATIENTS = [
    {
        "id": "chb01",
        "label": "Paciente 1",
        "crisis":    {"file": "chb01_16.edf", "start": 1015, "end": 1066},
        "no_crisis": {"file": "chb01_17.edf"},
    },
    {
        "id": "chb02",
        "label": "Paciente 2",
        "crisis":    {"file": "chb02_19.edf", "start": 3369, "end": 3378},
        "no_crisis": {"file": "chb02_20.edf"},
    },
    {
        "id": "chb03",
        "label": "Paciente 3",
        "crisis":    {"file": "chb03_04.edf", "start": 2162, "end": 2214},
        "no_crisis": {"file": "chb03_05.edf"},
    },
    {
        "id": "chb04",
        "label": "Paciente 4",
        "crisis":    {"file": "chb04_08.edf", "start": 6446, "end": 6557},
        "no_crisis": {"file": "chb04_09.edf"},
    },
    {
        "id": "chb05",
        "label": "Paciente 5",
        "crisis":    {"file": "chb05_06.edf", "start": 417, "end": 532},
        "no_crisis": {"file": "chb05_07.edf"},
    },
    {
        "id": "chb08",
        "label": "Paciente 6",
        "crisis":    {"file": "chb08_02.edf", "start": 2670, "end": 2841},
        "no_crisis": {"file": "chb08_03.edf"},
    },
]

RAW_DIR = os.path.join(ROOT, "data", "raw")
OUTPUT_DIR = os.path.join(ROOT, "data", "processed", "history")
MAX_POINTS = 5000


def process_edf(edf_path):
    """Procesa un EDF con el mismo pipeline que /analyze."""
    print(f"  Cargando: {edf_path}")
    raw = mne.io.read_raw_edf(edf_path, preload=False, verbose=False)
    n_ch = min(23, len(raw.ch_names))
    data_cruda = raw.get_data(picks=range(n_ch))
    fs = int(raw.info['sfreq'])
    ch_names = [raw.ch_names[i] for i in range(n_ch)]

    print(f"  fs={fs}Hz, shape={data_cruda.shape}. Filtrando Butterworth 0.5-40Hz...")
    data_filtrada = np.zeros_like(data_cruda)
    for ch in range(n_ch):
        data_filtrada[ch, :] = butter_bandpass_filter(
            data_cruda[ch, :], fs=fs, lowcut=0.5, highcut=40.0
        )

    window_samples = int(1.0 * fs)
    step_samples = int(0.5 * fs)

    print("  Calculando STFT...")
    stft_result = compute_stft_per_channel(data_filtrada, fs, window_samples, step_samples)
    print("  Calculando DWT energías...")
    dwt_result = compute_dwt_energy_per_channel(data_filtrada, fs, window_samples, step_samples)
    print("  Calculando LPC coeficientes...")
    lpc_result = compute_lpc_per_channel(data_filtrada, fs, window_samples, step_samples, order=12)

    # Downsampling (idéntico al endpoint /analyze)
    n_windows = len(stft_result["times"])
    if n_windows > MAX_POINTS:
        step = max(1, n_windows // MAX_POINTS)
        print(f"  Downsampling: {n_windows} -> {n_windows // step} puntos")
        stft_result["times"] = stft_result["times"][::step]
        dwt_result["times"] = dwt_result["times"][::step]
        lpc_result["times"] = lpc_result["times"][::step]

        for i in range(n_ch):
            ch_key = f"ch{i}"
            stft_result["magnitudes"][ch_key] = [row[::step] for row in stft_result["magnitudes"][ch_key]]
            for sb in ["A5", "D5", "D4", "D3"]:
                if sb in dwt_result["energy"][ch_key]:
                    dwt_result["energy"][ch_key][sb] = dwt_result["energy"][ch_key][sb][::step]
            lpc_result["coefficients"][ch_key] = lpc_result["coefficients"][ch_key][::step]

    # Señal original downsampled
    total_samples = data_filtrada.shape[1]
    signal_step = max(1, total_samples // MAX_POINTS)
    signal_payload = {
        "times": (np.arange(0, total_samples, signal_step) / fs).tolist(),
        "amplitudes": {}
    }
    for i in range(n_ch):
        signal_payload["amplitudes"][f"ch{i}"] = np.round(
            data_filtrada[i, ::signal_step] * 1e6, 2
        ).tolist()

    return {
        "channel_names": ch_names,
        "fs": fs,
        "duration_seconds": data_cruda.shape[1] / fs,
        "stft": stft_result,
        "dwt": dwt_result,
        "lpc": lpc_result,
        "signal": signal_payload,
    }


def round_nested(obj, decimals=4):
    """Redondea todos los floats en estructuras anidadas para reducir tamaño del JSON."""
    if isinstance(obj, float):
        return round(obj, decimals)
    elif isinstance(obj, list):
        return [round_nested(x, decimals) for x in obj]
    elif isinstance(obj, dict):
        return {k: round_nested(v, decimals) for k, v in obj.items()}
    return obj


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generar también un índice de pacientes para el frontend
    index = []

    for p in PATIENTS:
        print(f"\n{'='*60}")
        print(f"Procesando {p['label']} ({p['id']})")
        print(f"{'='*60}")

        patient_entry = {
            "id": p["id"],
            "label": p["label"],
            "crisis": {
                "file": p["crisis"]["file"],
                "seizure_start": p["crisis"]["start"],
                "seizure_end": p["crisis"]["end"],
            },
            "no_crisis": {
                "file": p["no_crisis"]["file"],
            }
        }

        for record_type in ["crisis", "no_crisis"]:
            info = p[record_type]
            edf_path = os.path.join(RAW_DIR, p["id"], info["file"])

            if not os.path.exists(edf_path):
                print(f"  [!] ARCHIVO NO ENCONTRADO: {edf_path}")
                continue

            print(f"\n  [{record_type.upper()}] {info['file']}")
            result = process_edf(edf_path)

            # Agregar metadata de crisis si aplica
            if record_type == "crisis":
                result["seizure"] = {
                    "start": info["start"],
                    "end": info["end"],
                }

            # Guardar como JSON comprimido
            out_name = f"{p['id']}_{record_type}.json.gz"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            with gzip.open(out_path, 'wt', encoding='utf-8', compresslevel=6) as f:
                json.dump(result, f, separators=(',', ':'))
            
            size_mb = os.path.getsize(out_path) / (1024 * 1024)
            print(f"  [OK] Guardado: {out_name} ({size_mb:.1f} MB)")

        index.append(patient_entry)

    # Guardar índice
    index_path = os.path.join(OUTPUT_DIR, "index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Índice guardado: {index_path}")
    print(f"[OK] Todos los registros históricos generados en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
