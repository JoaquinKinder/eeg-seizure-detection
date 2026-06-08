# Protocolos: Patient-specific y Leave-one-patient-out (Validación cruzada anidada)
import numpy as np
from sklearn.model_selection import StratifiedKFold

from src.models.balance import apply_balance_to_train
from src.models.hysteresis import apply_hysteresis_logic
from src.evaluation.metrics import (
    compute_clinical_metrics,
    compute_event_metrics,
    compute_detection_latency
)


def _run_single_fold(X_train, y_train, X_test, y_test, clf_pipeline,
                     smote_strategy=0.1, undersample_strategy=0.5,
                     N_windows=3, threshold_high=0.6, threshold_low=0.4,
                     random_state=42):
    """
    Función interna que ejecuta un único fold de entrenamiento/evaluación.
    
    Aplica el balanceo SOLO sobre X_train/y_train (anti-leakage), entrena el
    pipeline de clasificación, predice sobre X_test y aplica la histéresis.
    
    Returns:
    - dict con todas las métricas clínicas, de evento y latencia para este fold.
    """
    # 1. Balanceo SOLO en train (regla crítica anti-fuga de datos)
    X_train_bal, y_train_bal = apply_balance_to_train(
        X_train, y_train,
        smote_strategy=smote_strategy,
        undersample_strategy=undersample_strategy,
        random_state=random_state
    )
    
    # 2. Entrenamiento del pipeline (incluye StandardScaler interno)
    clf_pipeline.fit(X_train_bal, y_train_bal)
    
    # 3. Predicción probabilística sobre TEST (sin tocar el balanceo)
    y_prob = clf_pipeline.predict_proba(X_test)[:, 1]
    
    # 4. Post-procesamiento: histéresis temporal (Schmitt-trigger)
    y_pred_hist = apply_hysteresis_logic(
        y_prob,
        N_windows=N_windows,
        threshold_high=threshold_high,
        threshold_low=threshold_low
    )
    
    # 5. Cálculo de métricas
    # Protección: si el fold de test solo tiene una clase, algunas métricas no aplican
    if len(np.unique(y_test)) < 2:
        return None
    
    metricas_clinicas = compute_clinical_metrics(y_test, y_pred_hist, y_prob)
    metricas_evento = compute_event_metrics(y_test, y_pred_hist)
    latencia = compute_detection_latency(y_test, y_pred_hist)
    
    resultado = {**metricas_clinicas, **metricas_evento, "Latencia de Detección (s)": latencia}
    return resultado


def _agregar_metricas(lista_resultados):
    """
    Promedia las métricas numéricas de una lista de diccionarios de resultados.
    Ignora valores None en la latencia (falsos negativos totales).
    """
    if not lista_resultados:
        return {}
    
    resumen = {}
    claves = lista_resultados[0].keys()
    
    for clave in claves:
        valores = [r[clave] for r in lista_resultados if r[clave] is not None]
        if valores:
            resumen[clave] = np.mean(valores)
        else:
            resumen[clave] = None
    
    return resumen


def patient_specific_cv(X, y, clf_pipeline, n_splits=5,
                         smote_strategy=0.1, undersample_strategy=0.5,
                         N_windows=3, threshold_high=0.6, threshold_low=0.4,
                         random_state=42, verbose=True):
    """
    Validación cruzada estratificada K-Fold dentro de un único paciente.
    Baseline histórico del enfoque de Shoeb & Guttag (2004): entrenar y evaluar
    sobre los datos del mismo paciente.
    
    Regla anti-leakage garantizada: el balanceo y el ajuste del scaler se realizan
    ÚNICAMENTE sobre el fold de entrenamiento de cada iteración.
    
    Parameters:
    - X (ndarray): Matriz de características del paciente (ventanas x rasgos).
    - y (ndarray): Vector de etiquetas binarias (ventanas,).
    - clf_pipeline: Pipeline sklearn con scaler + clasificador (de classifiers.py).
    - n_splits (int): Número de folds de la validación cruzada.
    - smote_strategy (float): Ratio SMOTE para sobremuestreo de crisis.
    - undersample_strategy (float): Ratio de submuestreo de clase mayoritaria.
    - N_windows (int): Ventanas consecutivas exigidas por la histéresis.
    - threshold_high (float): Umbral de entrada a crisis (Schmitt-trigger).
    - threshold_low (float): Umbral de salida de crisis (Schmitt-trigger).
    - random_state (int): Semilla para reproducibilidad.
    - verbose (bool): Si True, imprime métricas por fold.
    
    Returns:
    - resultados_por_fold (list of dict): Métricas de cada fold.
    - resumen (dict): Promedio y desviación estándar de las métricas.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    resultados_por_fold = []
    
    if verbose:
        print(f"\n=== VALIDACIÓN PATIENT-SPECIFIC ({n_splits}-Fold CV) ===")
        print(f"  Total ventanas: {len(y)} | Crisis: {np.sum(y==1)} | Normal: {np.sum(y==0)}")
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        resultado = _run_single_fold(
            X_train, y_train, X_test, y_test, clf_pipeline,
            smote_strategy=smote_strategy,
            undersample_strategy=undersample_strategy,
            N_windows=N_windows,
            threshold_high=threshold_high,
            threshold_low=threshold_low,
            random_state=random_state
        )
        
        if resultado is None:
            if verbose:
                print(f"  Fold {fold_idx+1}: Saltado (test sin crisis o sin negativos)")
            continue
        
        resultados_por_fold.append(resultado)
        
        if verbose:
            lat_str = f"{resultado['Latencia de Detección (s)']:.1f}s" if resultado['Latencia de Detección (s)'] is not None else "N/D"
            print(f"  Fold {fold_idx+1}: Sensib={resultado['Sensibilidad (TPR)']:.3f} | "
                  f"Especif={resultado['Especificidad (TNR)']:.3f} | "
                  f"AUC-ROC={resultado['AUC-ROC']:.3f} | "
                  f"FA/h={resultado['Tasa de Falsas Alarmas (FA/h)']:.2f} | "
                  f"Latencia={lat_str}")
    
    resumen = _agregar_metricas(resultados_por_fold)
    
    if verbose and resumen:
        print(f"\n  --- PROMEDIO ({len(resultados_por_fold)} folds válidos) ---")
        lat_str = f"{resumen['Latencia de Detección (s)']:.1f}s" if resumen['Latencia de Detección (s)'] is not None else "N/D"
        print(f"  Sensib={resumen['Sensibilidad (TPR)']:.3f} | "
              f"Especif={resumen['Especificidad (TNR)']:.3f} | "
              f"AUC-ROC={resumen['AUC-ROC']:.3f} | "
              f"FA/h={resumen['Tasa de Falsas Alarmas (FA/h)']:.2f} | "
              f"Latencia={lat_str}")
    
    return resultados_por_fold, resumen


def leave_one_patient_out_cv(patients_data, clf_pipeline,
                              smote_strategy=0.1, undersample_strategy=0.5,
                              N_windows=3, threshold_high=0.6, threshold_low=0.4,
                              random_state=42, verbose=True):
    """
    Validación Leave-One-Patient-Out (LOPO): mide la generalización entre sujetos.
    
    En cada iteración, UN paciente es el conjunto de test; el resto de los pacientes
    son concatenados como entrenamiento. Es el protocolo más exigente y el verdadero
    indicador de aplicabilidad clínica (el modelo no ha visto al paciente de test).
    
    Regla anti-leakage garantizada: el balanceo y el ajuste del scaler se realizan
    ÚNICAMENTE sobre el conjunto de entrenamiento de cada iteración.
    
    Parameters:
    - patients_data (dict): Diccionario {patient_id: (X, y)} con los datos de cada
      paciente cargados desde los archivos .npy procesados.
    - clf_pipeline: Pipeline sklearn con scaler + clasificador (de classifiers.py).
    - smote_strategy (float): Ratio SMOTE para sobremuestreo de crisis.
    - undersample_strategy (float): Ratio de submuestreo de clase mayoritaria.
    - N_windows (int): Ventanas consecutivas exigidas por la histéresis.
    - threshold_high (float): Umbral de entrada a crisis (Schmitt-trigger).
    - threshold_low (float): Umbral de salida de crisis (Schmitt-trigger).
    - random_state (int): Semilla para reproducibilidad.
    - verbose (bool): Si True, imprime métricas por paciente de test.
    
    Returns:
    - resultados_por_paciente (dict): {patient_id: dict_metricas} para cada paciente.
    - resumen_global (dict): Promedio de las métricas sobre todos los pacientes.
    """
    patient_ids = list(patients_data.keys())
    resultados_por_paciente = {}
    
    if verbose:
        print(f"\n=== VALIDACIÓN LEAVE-ONE-PATIENT-OUT (LOPO) ===")
        print(f"  Pacientes disponibles: {patient_ids}")
    
    for test_id in patient_ids:
        # Paciente de test
        X_test, y_test = patients_data[test_id]
        
        # Concatenar el resto como entrenamiento
        X_train_parts = []
        y_train_parts = []
        for train_id in patient_ids:
            if train_id != test_id:
                X_train_parts.append(patients_data[train_id][0])
                y_train_parts.append(patients_data[train_id][1])
        
        X_train = np.vstack(X_train_parts)
        y_train = np.concatenate(y_train_parts)
        
        if verbose:
            print(f"\n  Test: {test_id} | Train: {[pid for pid in patient_ids if pid != test_id]}")
            print(f"  Train → ventanas: {len(y_train)} (crisis: {np.sum(y_train==1)})")
            print(f"  Test  → ventanas: {len(y_test)} (crisis: {np.sum(y_test==1)})")
        
        resultado = _run_single_fold(
            X_train, y_train, X_test, y_test, clf_pipeline,
            smote_strategy=smote_strategy,
            undersample_strategy=undersample_strategy,
            N_windows=N_windows,
            threshold_high=threshold_high,
            threshold_low=threshold_low,
            random_state=random_state
        )
        
        if resultado is None:
            if verbose:
                print(f"  {test_id}: Saltado (test sin crisis o sin negativos)")
            continue
        
        resultados_por_paciente[test_id] = resultado
        
        if verbose:
            lat_str = f"{resultado['Latencia de Detección (s)']:.1f}s" if resultado['Latencia de Detección (s)'] is not None else "N/D"
            print(f"  {test_id}: Sensib={resultado['Sensibilidad (TPR)']:.3f} | "
                  f"Especif={resultado['Especificidad (TNR)']:.3f} | "
                  f"AUC-ROC={resultado['AUC-ROC']:.3f} | "
                  f"FA/h={resultado['Tasa de Falsas Alarmas (FA/h)']:.2f} | "
                  f"Latencia={lat_str}")
    
    # Promedio global LOPO
    resumen_global = _agregar_metricas(list(resultados_por_paciente.values()))
    
    if verbose and resumen_global:
        print(f"\n  --- PROMEDIO GLOBAL LOPO ({len(resultados_por_paciente)} pacientes válidos) ---")
        lat_str = f"{resumen_global['Latencia de Detección (s)']:.1f}s" if resumen_global['Latencia de Detección (s)'] is not None else "N/D"
        print(f"  Sensib={resumen_global['Sensibilidad (TPR)']:.3f} | "
              f"Especif={resumen_global['Especificidad (TNR)']:.3f} | "
              f"AUC-ROC={resumen_global['AUC-ROC']:.3f} | "
              f"FA/h={resumen_global['Tasa de Falsas Alarmas (FA/h)']:.2f} | "
              f"Latencia={lat_str}")
    
    return resultados_por_paciente, resumen_global
