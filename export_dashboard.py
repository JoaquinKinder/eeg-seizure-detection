"""
Script de exportación standalone para generar results.json para el dashboard.
Carga los archivos .npy procesados y ejecuta la validación cruzada completa,
exportando los resultados al dashboard React.

Uso:
    python export_dashboard.py

O desde Jupyter:
    %run export_dashboard.py
"""
import sys
import os
import numpy as np

# Permite importar desde src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.classifiers import get_random_forest_pipeline, get_svm_pipeline
from src.evaluation.validation import patient_specific_cv, leave_one_patient_out_cv, _agregar_metricas
from src.reporting.export_results import export_results_to_json

# ─── CONFIGURACIÓN ──────────────────────────────────────────────────────────
DATA_DIR             = os.path.join(os.path.dirname(__file__), 'data', 'processed')
N_SPLITS             = 5
SMOTE_STRATEGY       = 0.1
UNDERSAMPLE_STRATEGY = 0.5
N_WINDOWS            = 3
THRESHOLD_HIGH       = 0.6
THRESHOLD_LOW        = 0.4
RANDOM_STATE         = 42

def main():
    # ── 1. Cargar datos ──────────────────────────────────────────────────────
    print("=== Cargando datos procesados ===")
    patients_data = {}
    npy_files = [f for f in os.listdir(DATA_DIR) if f.startswith('X_') and f.endswith('.npy')]
    patient_ids = sorted([f.replace('X_', '').replace('_completo.npy', '') for f in npy_files])

    for pid in patient_ids:
        X = np.load(os.path.join(DATA_DIR, f'X_{pid}_completo.npy'))
        y = np.load(os.path.join(DATA_DIR, f'y_{pid}_completo.npy'))
        patients_data[pid] = (X, y)
        pct = 100 * np.sum(y == 1) / len(y)
        print(f"  {pid}: {X.shape} | Crisis: {np.sum(y==1)} ({pct:.3f}%)")

    print(f"\nTotal pacientes: {len(patients_data)}")

    # ── 2. Patient-Specific RF ───────────────────────────────────────────────
    print("\n=== Validación Patient-Specific — Random Forest ===")
    ps_rf_results = {}
    for pid, (X, y) in patients_data.items():
        if np.sum(y == 1) < N_SPLITS:
            print(f"  {pid}: SKIP (pocas crisis)")
            continue
        clf = get_random_forest_pipeline(n_estimators=100, random_state=RANDOM_STATE)
        _, resumen = patient_specific_cv(
            X, y, clf, n_splits=N_SPLITS,
            smote_strategy=SMOTE_STRATEGY, undersample_strategy=UNDERSAMPLE_STRATEGY,
            N_windows=N_WINDOWS, threshold_high=THRESHOLD_HIGH, threshold_low=THRESHOLD_LOW,
            random_state=RANDOM_STATE, verbose=True
        )
        if resumen:
            ps_rf_results[pid] = resumen

    # ── 3. Patient-Specific SVM ──────────────────────────────────────────────
    print("\n=== Validación Patient-Specific — SVM-RBF ===")
    ps_svm_results = {}
    for pid, (X, y) in patients_data.items():
        if np.sum(y == 1) < N_SPLITS:
            continue
        clf = get_svm_pipeline(C=1.0, gamma='scale', random_state=RANDOM_STATE)
        _, resumen = patient_specific_cv(
            X, y, clf, n_splits=N_SPLITS,
            smote_strategy=SMOTE_STRATEGY, undersample_strategy=UNDERSAMPLE_STRATEGY,
            N_windows=N_WINDOWS, threshold_high=THRESHOLD_HIGH, threshold_low=THRESHOLD_LOW,
            random_state=RANDOM_STATE, verbose=True
        )
        if resumen:
            ps_svm_results[pid] = resumen

    # ── 4. LOPO RF ───────────────────────────────────────────────────────────
    print("\n=== LOPO — Random Forest ===")
    clf_rf = get_random_forest_pipeline(n_estimators=100, random_state=RANDOM_STATE)
    lopo_rf_por_paciente, lopo_rf_global = leave_one_patient_out_cv(
        patients_data, clf_rf,
        smote_strategy=SMOTE_STRATEGY, undersample_strategy=UNDERSAMPLE_STRATEGY,
        N_windows=N_WINDOWS, threshold_high=THRESHOLD_HIGH, threshold_low=THRESHOLD_LOW,
        random_state=RANDOM_STATE, verbose=True
    )

    # ── 5. LOPO SVM ──────────────────────────────────────────────────────────
    print("\n=== LOPO — SVM-RBF ===")
    clf_svm = get_svm_pipeline(C=1.0, gamma='scale', random_state=RANDOM_STATE)
    lopo_svm_por_paciente, lopo_svm_global = leave_one_patient_out_cv(
        patients_data, clf_svm,
        smote_strategy=SMOTE_STRATEGY, undersample_strategy=UNDERSAMPLE_STRATEGY,
        N_windows=N_WINDOWS, threshold_high=THRESHOLD_HIGH, threshold_low=THRESHOLD_LOW,
        random_state=RANDOM_STATE, verbose=True
    )

    # ── 6. Exportar JSON ─────────────────────────────────────────────────────
    out = export_results_to_json(
        patients_data=patients_data,
        ps_rf_results=ps_rf_results,
        ps_svm_results=ps_svm_results,
        lopo_rf_por_paciente=lopo_rf_por_paciente,
        lopo_rf_global=lopo_rf_global,
        lopo_svm_por_paciente=lopo_svm_por_paciente,
        lopo_svm_global=lopo_svm_global,
        n_splits=N_SPLITS
    )

    # ── 7. Exportar Imágenes de Línea de Tiempo ──────────────────────────────
    from src.reporting.export_timeline_images import export_all_timelines
    dashboard_public = os.path.join(os.path.dirname(__file__), 'dashboard', 'public')
    export_all_timelines(patients_data, dashboard_public)

    print(f"\n{'='*60}")
    print(f"✅ JSON exportado: {out}")
    print(f"\nPara ver el dashboard:")
    print(f"  Abrí una terminal en 'dashboard/' y ejecutá:")
    print(f"  python -m http.server 8080")
    print(f"  Luego abrí: http://localhost:8080")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
