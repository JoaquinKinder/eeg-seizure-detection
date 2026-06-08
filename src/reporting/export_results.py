"""
Módulo de exportación de resultados a JSON.
Convierte los resultados de la validación cruzada a un formato legible
por el dashboard React.
"""
import json
import os
import numpy as np
from datetime import datetime


def _clean_value(v):
    """Convierte tipos NumPy a tipos nativos de Python para serialización JSON."""
    if v is None:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


def _clean_dict(d):
    """Limpia recursivamente un diccionario para serialización JSON."""
    if d is None:
        return {}
    return {k: _clean_value(v) for k, v in d.items()}


def export_results_to_json(
    patients_data,
    ps_rf_results,
    ps_svm_results,
    lopo_rf_por_paciente,
    lopo_rf_global,
    lopo_svm_por_paciente,
    lopo_svm_global,
    output_path=None,
    n_splits=5,
    metadata_extra=None
):
    """
    Exporta todos los resultados de validación cruzada a un archivo JSON
    listo para ser consumido por el dashboard React.

    Parameters:
    - patients_data (dict): {patient_id: (X, y)} para obtener estadísticas de los datos.
    - ps_rf_results (dict): {patient_id: resumen_cv} de validación patient-specific RF.
    - ps_svm_results (dict): {patient_id: resumen_cv} de validación patient-specific SVM.
    - lopo_rf_por_paciente (dict): {patient_id: metricas} de LOPO RF.
    - lopo_rf_global (dict): Promedio global de LOPO RF.
    - lopo_svm_por_paciente (dict): {patient_id: metricas} de LOPO SVM.
    - lopo_svm_global (dict): Promedio global de LOPO SVM.
    - output_path (str|None): Ruta del archivo JSON de salida.
      Si es None, guarda en 'dashboard/public/results.json'.
    - n_splits (int): Número de folds usado en la validación patient-specific.
    - metadata_extra (dict|None): Metadatos adicionales a incluir en el JSON.

    Returns:
    - output_path (str): Ruta donde se guardó el JSON.
    """
    if output_path is None:
        # Ruta relativa desde la raíz del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_path = os.path.join(base_dir, 'dashboard', 'public', 'results.json')

    # Asegurar que el directorio de salida exista
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Estadísticas por paciente (distribución de clases)
    patient_stats = {}
    for pid, (X, y) in patients_data.items():
        n_total = len(y)
        n_crisis = int(np.sum(y == 1))
        n_normal = int(np.sum(y == 0))
        patient_stats[pid] = {
            "total_ventanas": n_total,
            "ventanas_crisis": n_crisis,
            "ventanas_normal": n_normal,
            "pct_crisis": round(100.0 * n_crisis / n_total, 3) if n_total > 0 else 0.0,
            "n_features": int(X.shape[1]) if X.ndim > 1 else 0
        }

    # Calcular global de patient-specific (promedio de promedios de cada paciente)
    def _ps_global(ps_results):
        if not ps_results:
            return {}
        claves = list(list(ps_results.values())[0].keys())
        global_res = {}
        for k in claves:
            vals = [v[k] for v in ps_results.values() if v.get(k) is not None]
            global_res[k] = float(np.mean(vals)) if vals else None
        return global_res

    ps_rf_global = _ps_global(ps_rf_results)
    ps_svm_global = _ps_global(ps_svm_results)

    # Construir estructura de salida
    results = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "patients": sorted(list(patients_data.keys())),
            "n_splits_cv": n_splits,
            "dataset": "CHB-MIT Scalp EEG Database",
            "sampling_rate_hz": 256,
            "window_duration_s": 1.0,
            "overlap_pct": 50,
            "wavelet": "db4",
            "levels": 5,
            **(metadata_extra or {})
        },
        "patient_stats": patient_stats,
        "patient_specific": {
            "random_forest": {
                "global": _clean_dict(ps_rf_global),
                "por_paciente": {pid: _clean_dict(v) for pid, v in ps_rf_results.items()}
            },
            "svm": {
                "global": _clean_dict(ps_svm_global),
                "por_paciente": {pid: _clean_dict(v) for pid, v in ps_svm_results.items()}
            }
        },
        "lopo": {
            "random_forest": {
                "global": _clean_dict(lopo_rf_global),
                "por_paciente": {pid: _clean_dict(v) for pid, v in lopo_rf_por_paciente.items()}
            },
            "svm": {
                "global": _clean_dict(lopo_svm_global),
                "por_paciente": {pid: _clean_dict(v) for pid, v in lopo_svm_por_paciente.items()}
            }
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✓ Resultados exportados a: {output_path}")
    return output_path
