"""
LPC (Linear Predictive Coding) Feature Extraction for EEG signals.
Uses Levinson-Durbin algorithm implemented with NumPy (no extra dependencies).
Applies Hanning windowing (1s windows, 50% overlap) before computing LPC coefficients.
Extracts 12 LPC coefficients per window per channel.
"""
import numpy as np


def _levinson_durbin(r, order):
    """
    Levinson-Durbin recursion to compute LPC coefficients.
    
    Parameters:
    - r: autocorrelation sequence (at least order+1 elements)
    - order: number of LPC coefficients to compute

    Returns:
    - a: LPC coefficients [a1, a2, ..., a_order]
    - error: prediction error (gain)
    """
    a = np.zeros(order)
    error = r[0]

    if error == 0:
        return a, 0.0

    for i in range(order):
        # Compute reflection coefficient
        lambda_val = -np.dot(a[:i], r[i:0:-1]) - r[i + 1]
        k = lambda_val / error

        # Update coefficients
        a_new = a.copy()
        a_new[i] = k
        for j in range(i):
            a_new[j] = a[j] + k * a[i - 1 - j]
        a = a_new

        # Update prediction error
        error = error * (1 - k ** 2)
        if error <= 0:
            break

    return a, error


def compute_lpc_per_channel(data_filtrada, fs=256, window_samples=256, step_samples=128, order=12):
    """
    Computes LPC coefficients (a1..a12) per window for all 23 EEG channels.

    Parameters:
    - data_filtrada: ndarray of shape (23, total_samples)
    - fs: sampling frequency (default 256 Hz)
    - window_samples: samples per window (1s = 256)
    - step_samples: step between windows (50% overlap = 128)
    - order: number of LPC coefficients (default 12)

    Returns:
    - dict with:
        "times": list of window center times in seconds
        "coeff_labels": ["a1", "a2", ..., "a12"]
        "coefficients": {
            "ch0": [[a1..a12], [a1..a12], ...],  # one row per window
            "ch1": [...],
            ...
        }
    """
    n_channels, total_samples = data_filtrada.shape
    num_windows = (total_samples - window_samples) // step_samples + 1

    times = [(i * step_samples + window_samples / 2) / fs for i in range(num_windows)]
    coeff_labels = [f"a{i+1}" for i in range(order)]

    coefficients = {}
    hanning_win = np.hanning(window_samples)

    for ch in range(n_channels):
        signal = data_filtrada[ch, :]
        ch_coeffs = []

        for i in range(num_windows):
            start = i * step_samples
            end = start + window_samples
            window_data = signal[start:end] * hanning_win  # Apply Hanning

            # Compute autocorrelation sequence (lags 0 to order)
            r = np.correlate(window_data, window_data, mode='full')
            r = r[len(r) // 2:]  # Take non-negative lags only
            r = r[:order + 1]

            # Levinson-Durbin to get LPC coefficients
            lpc_coeffs, _ = _levinson_durbin(r, order)
            ch_coeffs.append(lpc_coeffs.tolist())

        coefficients[f"ch{ch}"] = ch_coeffs

    return {
        "times": times,
        "coeff_labels": coeff_labels,
        "coefficients": coefficients
    }
