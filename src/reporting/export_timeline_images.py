import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg') # Usar backend sin interfaz gráfica para no abrir ventanas
import matplotlib.pyplot as plt

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline

from src.models.classifiers import get_random_forest_pipeline
from src.models.hysteresis import apply_hysteresis_logic

def generate_patient_timeline_image(patient_id, X, y, output_dir):
    """
    Entrena modelo con split cronológico y exporta el gráfico de la línea de tiempo.
    El gráfico se estiliza con colores oscuros para combinar con el dashboard React.
    """
    print(f"  Graficando línea de tiempo para {patient_id}...")
    
    # Split cronológico (70% train, 30% test)
    split_idx = int(len(X) * 0.7)
    
    X_train, y_train = X[:split_idx], y[:split_idx]
    
    # Validar que haya suficientes crisis en train para SMOTE (al menos 6)
    n_crisis_train = np.sum(y_train == 1)
    if n_crisis_train < 6:
        print(f"    -> Saltando {patient_id}: Solo {n_crisis_train} crisis en el conjunto de entrenamiento (muy pocas para balancear).")
        return False
        
    smote = SMOTE(sampling_strategy=0.1, random_state=42)
    rus = RandomUnderSampler(sampling_strategy=0.5, random_state=42)
    clf = get_random_forest_pipeline(n_estimators=100, random_state=42)
    
    pipeline = ImbPipeline([('smote', smote), ('rus', rus), ('clf', clf)])
    pipeline.fit(X_train, y_train)
    
    # Predecir probabilidades para TODO el registro
    y_pred_proba = pipeline.predict_proba(X)[:, 1]
    
    # Aplicar histéresis
    y_pred_smooth = apply_hysteresis_logic(
        y_pred_proba, 
        N_windows=3, 
        threshold_high=0.6, 
        threshold_low=0.4
    )
    
    # Eje de tiempo (en horas). Paso = 2s
    AVANCE_S = 2.0
    tiempo_horas = (np.arange(len(y)) * AVANCE_S) / 3600.0
    
    # ==========================================
    # ESTILIZACIÓN DEL GRÁFICO (Dark Theme)
    # ==========================================
    # Para encajar con el CSS del Dashboard:
    # bg-surface: #0d1117, bg-card: rgba(255,255,255,0.04)
    # text-primary: #e8edf5
    
    plt.style.use('dark_background')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
    fig.patch.set_facecolor('#0d1117')
    
    for ax in (ax1, ax2, ax3):
        ax.set_facecolor('#05070f')
        ax.grid(True, color='#ffffff0f', linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#4a5568')
        ax.spines['left'].set_color('#4a5568')
        ax.tick_params(colors='#8b9ab3', labelsize=10)
    
    # Colores definidos en App.module.css
    color_real = '#fc8181'     # accent-red
    color_prob = '#f6ad55'     # accent-amber
    color_pred = '#63b3ed'     # accent-blue
    
    # 1. Etiquetas reales del neurólogo
    ax1.plot(tiempo_horas, y, color=color_real, label='Real (Neurólogo)', linewidth=1.5)
    ax1.fill_between(tiempo_horas, 0, y, color=color_real, alpha=0.3)
    ax1.set_title('A. Crisis Reales (Anotación Médica)', color='#e8edf5', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Crisis', color='#8b9ab3')
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['Normal', 'Crisis'])
    ax1.axvline(tiempo_horas[split_idx], color='#8b9ab3', linestyle='--', label='Fin Train / Inicio Test')
    ax1.legend(loc='upper right', facecolor='#0d1117', edgecolor='#4a5568', labelcolor='#e8edf5')

    # 2. Probabilidad cruda del modelo
    ax2.plot(tiempo_horas, y_pred_proba, color=color_prob, label='Probabilidad RF', alpha=0.9, linewidth=1)
    ax2.fill_between(tiempo_horas, 0, y_pred_proba, color=color_prob, alpha=0.2)
    ax2.axhline(0.6, color='#fc8181', linestyle=':', label='Umbral Alto (0.6)')
    ax2.axhline(0.4, color='#68d391', linestyle=':', label='Umbral Bajo (0.4)')
    ax2.set_title('B. Probabilidad Estimada por el Modelo (Random Forest)', color='#e8edf5', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Probabilidad', color='#8b9ab3')
    ax2.set_ylim(0, 1.05)
    ax2.axvline(tiempo_horas[split_idx], color='#8b9ab3', linestyle='--')
    ax2.legend(loc='upper right', facecolor='#0d1117', edgecolor='#4a5568', labelcolor='#e8edf5')

    # 3. Detección final (con Histéresis)
    ax3.plot(tiempo_horas, y_pred_smooth, color=color_pred, label='Detección Modelo', linewidth=1.5)
    ax3.fill_between(tiempo_horas, 0, y_pred_smooth, color=color_pred, alpha=0.3)
    ax3.set_title('C. Detección Final (con Histéresis)', color='#e8edf5', fontweight='bold', fontsize=12)
    ax3.set_ylabel('Detección', color='#8b9ab3')
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['Normal', 'Crisis'])
    ax3.set_xlabel('Tiempo de registro (Horas)', color='#8b9ab3')
    ax3.axvline(tiempo_horas[split_idx], color='#8b9ab3', linestyle='--')
    ax3.legend(loc='upper right', facecolor='#0d1117', edgecolor='#4a5568', labelcolor='#e8edf5')
    
    plt.tight_layout()
    
    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f'timeline_{patient_id}.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight', transparent=True)
    plt.close(fig)
    return True

def export_all_timelines(patients_data, dashboard_public_dir):
    """
    Itera sobre todos los pacientes y genera las imágenes PNG.
    """
    out_dir = os.path.join(dashboard_public_dir, 'timelines')
    print(f"\n=== Generando Gráficos de Línea de Tiempo (Imágenes) ===")
    print(f"Directorio de salida: {out_dir}")
    
    generados = 0
    for pid, (X, y) in patients_data.items():
        success = generate_patient_timeline_image(pid, X, y, out_dir)
        if success:
            generados += 1
            
    print(f"OK: Se generaron {generados} imágenes de línea de tiempo.")
    return generados
