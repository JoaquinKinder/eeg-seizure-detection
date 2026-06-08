import os
import sys
import numpy as np
import joblib

# Permite importar desde src/ si se corre desde la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from src.models.classifiers import get_random_forest_pipeline

DATA_DIR = os.path.join('data', 'processed')
MODEL_DIR = os.path.join('models')

def train_and_save_production_model():
    print("=== Entrenando Modelo Global de Producción ===")
    
    # 1. Cargar todos los pacientes
    X_list = []
    y_list = []
    
    npy_files = [f for f in os.listdir(DATA_DIR) if f.startswith('X_') and f.endswith('.npy')]
    patient_ids = sorted([f.replace('X_', '').replace('_completo.npy', '') for f in npy_files])
    
    for pid in patient_ids:
        X = np.load(os.path.join(DATA_DIR, f'X_{pid}_completo.npy'))
        y = np.load(os.path.join(DATA_DIR, f'y_{pid}_completo.npy'))
        X_list.append(X)
        y_list.append(y)
        
    X_all = np.vstack(X_list)
    y_all = np.concatenate(y_list)
    
    print(f"Total ventanas de entrenamiento: {len(y_all)}")
    print(f"Total crisis (y=1): {np.sum(y_all == 1)}")
    
    # 2. Configurar Pipeline
    smote = SMOTE(sampling_strategy=0.1, random_state=42)
    rus = RandomUnderSampler(sampling_strategy=0.5, random_state=42)
    clf = get_random_forest_pipeline(n_estimators=100, random_state=42)
    
    pipeline = ImbPipeline([('smote', smote), ('rus', rus), ('clf', clf)])
    
    # 3. Entrenar
    print("\nEntrenando Random Forest... (esto puede tardar unos minutos)")
    pipeline.fit(X_all, y_all)
    
    # 4. Guardar
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, 'rf_production.joblib')
    joblib.dump(pipeline, model_path)
    
    print(f"✅ Modelo guardado exitosamente en: {model_path}")

if __name__ == '__main__':
    train_and_save_production_model()
