# Clasificador principal: Random Forest | Comparación: SVM-RBF
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

def get_random_forest_classifier(n_estimators=100, max_depth=None, random_state=42):
    """
    Inicializa el clasificador principal Random Forest.
    Retorna un modelo capaz de entregar predict_proba() para la histéresis.
    """
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1 # Usa todos los núcleos del procesador para acelerar el entrenamiento
    )
    return model

def get_svm_rbf_classifier(C=1.0, gamma='scale', random_state=42):
    """
    Inicializa el clasificador de comparación SVM con kernel RBF.
    Se activa probability=True para que pueda escupir scores de probabilidad
    compatibles con el post-procesamiento temporal de histéresis.
    """
    model = SVC(
        kernel='rbf',
        C=C,
        gamma=gamma,
        probability=True,  # Habilita predict_proba() en SVM
        class_weight='balanced',  # Salvaguarda complementaria para el desbalance
        random_state=random_state
    )
    return model