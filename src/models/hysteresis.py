# Lógica de histéresis temporal (Doble umbral tipo Schmitt-trigger)
import numpy as np

def apply_hysteresis_logic(probabilities, N_windows=3, threshold_high=0.6, threshold_low=0.4):
    """
    Aplica una lógica de histéresis temporal tipo Schmitt-trigger sobre las 
    probabilidades predichas para suprimir falsos positivos aislados.
    
    Parameters:
    - probabilities (ndarray): Vector de probabilidades p(crisis) devuelto por el clasificador,
                               forma (num_ventanas,).
    - N_windows (int): Cantidad de ventanas consecutivas positivas exigidas para activar la alarma.
    - threshold_high (float): Umbral para considerar una ventana como "potencial crisis".
    - threshold_low (float): Umbral por debajo del cual se considera "regreso a la normalidad".
    
    Returns:
    - decisions (ndarray): Vector binario (0: No-crisis, 1: Crisis) con la decisión final.
    """
    num_windows = len(probabilities)
    decisions = np.zeros(num_windows, dtype=int)
    
    # Estado inicial: 0 = Normal (No-crisis), 1 = Alarma activa (Crisis)
    current_state = 0
    consecutive_highs = 0
    consecutive_lows = 0
    
    for i in range(num_windows):
        p = probabilities[i]
        
        if current_state == 0:
            # Estamos en estado NORMAL. Evaluamos si entramos en crisis.
            if p >= threshold_high:
                consecutive_highs += 1
            else:
                consecutive_highs = 0  # Se rompió la racha consecutiva
                
            # Si acumulamos N ventanas positivas consecutivas, se dispara la alarma
            if consecutive_highs >= N_windows:
                current_state = 1
                consecutive_lows = 0  # Reiniciamos el contador inverso
                
        else:
            # Estamos en estado de CRISIS (Alarma activa). Evaluamos si salimos.
            if p < threshold_low:
                consecutive_lows += 1
            else:
                consecutive_lows = 0  # Se rompió la racha de negativos
                
            # Exigimos la misma persistencia N para apagar la alarma y evitar parpadeos
            if consecutive_lows >= N_windows:
                current_state = 0
                consecutive_highs = 0  # Reiniciamos el contador de entrada
                
        decisions[i] = current_state
        
    return decisions