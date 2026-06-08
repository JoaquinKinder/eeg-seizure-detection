# Métricas: Sensibilidad, Especificidad, AUC-ROC, AUC-PR, Latencia y FA/h
import numpy as np
from sklearn.metrics import confusion_matrix, roc_auc_score, precision_recall_curve, auc

def compute_clinical_metrics(y_true, y_pred, y_prob):
    """
    Calcula las métricas por ventana orientadas al dominio clínico.
    
    Parameters:
    - y_true (ndarray): Etiquetas reales binarias (0: no-crisis, 1: crisis).
    - y_pred (ndarray): Predicciones binarias finales (post-histéresis).
    - y_prob (ndarray): Probabilidades crudas del clasificador p(crisis).
    """
    # Matriz de confusión básica: [VN, FP] / [FN, VP]
    tn, fp, fn, vp = confusion_matrix(y_true, y_pred).ravel()
    
    # Sensibilidad (True Positive Rate)
    sensibilidad = vp / (vp + fn) if (vp + fn) > 0 else 0.0
    
    # Especificidad (True Negative Rate)
    especificidad = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    # Área Bajo la Curva ROC (independiente del umbral)
    try:
        auc_roc = roc_auc_score(y_true, y_prob)
    except ValueError:
        auc_roc = 0.5  # Caso en el que el fold solo contenga una clase
        
    # Área Bajo la Curva Precisión-Recall (F1/AUC-PR: más informativa bajo desbalance)
    precision_vals, recall_vals, _ = precision_recall_curve(y_true, y_prob)
    auc_pr = auc(recall_vals, precision_vals)
    
    return {
        "Sensibilidad (TPR)": sensibilidad,
        "Especificidad (TNR)": especificidad,
        "AUC-ROC": auc_roc,
        "AUC-PR": auc_pr,
        "Verdaderos Positivos (VP)": vp,
        "Falsos Positivos (FP)": fp,
        "Falsos Negativos (FN)": fn,
        "Verdaderos Negativos (VN)": tn
    }

def compute_event_metrics(y_true, y_pred, fs=256, step_size=128):
    """
    Calcula métricas a nivel de evento clínico: Tasa de Falsas Alarmas por Hora (FA/h)
    y estima el impacto de la latencia.
    """
    tn, fp, fn, vp = confusion_matrix(y_true, y_pred).ravel()
    
    # 1. Calcular la duración total del registro evaluado en horas
    # Cada paso de ventana equivale a un desplazamiento temporal (128 muestras = 0.5s)
    total_segundos = len(y_true) * (step_size / fs)
    total_horas = total_segundos / 3600.0
    
    # 2. Tasa de Falsas Alarmas por Hora (FA/h)
    # Se cuenta cada ventana de falso positivo como una alarma espuria para esta métrica base
    fa_per_hour = fp / total_horas if total_horas > 0 else 0.0
    
    return {
        "Horas de Registro": total_horas,
        "Tasa de Falsas Alarmas (FA/h)": fa_per_hour
    }

def compute_detection_latency(y_true, y_pred, fs=256, step_size=128):
    """
    Calcula la latencia de detección: tiempo en segundos entre el inicio real
    anotado de la crisis y la primera ventana positiva detectada por el sistema.
    
    Una latencia positiva significa que el sistema detecta DESPUÉS del onset real
    (retardo). Una latencia negativa significaría detección anticipada (raro).
    
    Parameters:
    - y_true (ndarray): Etiquetas reales binarias (0: no-crisis, 1: crisis).
    - y_pred (ndarray): Predicciones binarias del sistema (post-histéresis).
    - fs (int): Frecuencia de muestreo original (256 Hz para CHB-MIT).
    - step_size (int): Desplazamiento entre ventanas en muestras (128 = 50% overlap).
    
    Returns:
    - latencia_segundos (float | None): Latencia en segundos. None si no hay crisis
      real en y_true, o si el sistema no detectó ninguna crisis (falso negativo total).
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    # Tiempo en segundos de cada ventana
    segundos_por_ventana = step_size / fs  # 128/256 = 0.5 s por ventana
    
    # Buscar el índice de la primera ventana real de crisis
    indices_reales = np.where(y_true == 1)[0]
    if len(indices_reales) == 0:
        # No hay crisis real en este segmento evaluado
        return None
    primer_onset_real = indices_reales[0]
    
    # Buscar el índice de la primera ventana detectada como crisis
    indices_detectados = np.where(y_pred == 1)[0]
    if len(indices_detectados) == 0:
        # El sistema no detectó ninguna crisis (falso negativo total)
        return None
    primer_onset_detectado = indices_detectados[0]
    
    # Latencia = diferencia de ventanas × segundos por ventana
    latencia_ventanas = primer_onset_detectado - primer_onset_real
    latencia_segundos = latencia_ventanas * segundos_por_ventana
    
    return latencia_segundos