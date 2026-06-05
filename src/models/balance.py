# Balanceo de datos: SMOTE y Submuestreo (¡APLICAR SOLO EN FOLDS DE ENTRENAMIENTO!)
import numpy as np
# imblearn maneja el balanceo de forma nativa e integrada con sklearn
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline

def get_balance_pipeline(smote_strategy=0.1, undersample_strategy=0.5, random_state=42):
    # Forzamos k_neighbors=1 por seguridad en datasets de prueba chicos
    over = SMOTE(sampling_strategy=smote_strategy, k_neighbors=1, random_state=random_state)
    under = RandomUnderSampler(sampling_strategy=undersample_strategy, random_state=random_state)
    
    balance_steps = Pipeline(steps=[('oversample', over), ('undersample', under)])
    return balance_steps

def apply_balance_to_train(X_train, y_train, smote_strategy=0.1, undersample_strategy=0.5, random_state=42):
    """
    Aplica el balanceo de forma directa. 
    Úsese EXCLUSIVAMENTE dentro del bucle de validación cruzada sobre los folds de train.
    """
    pipeline = get_balance_pipeline(smote_strategy, undersample_strategy, random_state)
    X_resampled, y_resampled = pipeline.fit_resample(X_train, y_train)
    
    return X_resampled, y_resampled