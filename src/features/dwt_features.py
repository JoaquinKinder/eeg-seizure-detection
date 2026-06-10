"""
DWT Feature Extraction for EEG signals.
Applies Discrete Wavelet Transform (Daubechies-4, 5 levels) using a Hanning-windowed
segmentation (1s windows, 50% overlap).

Only retains the last 3 detail levels (D3, D4, D5) and approximation A5,
since D1 and D2 correspond to frequencies above 40Hz which were removed by the bandpass filter.

Frequency bands for fs=256Hz, db4 level 5 decomposition:
  A5:  0 - 4 Hz   (Delta)
  D5:  4 - 8 Hz   (Theta)
  D4:  8 - 16 Hz  (Alpha / low Beta)
  D3: 16 - 32 Hz  (Beta)
  D2: 32 - 64 Hz  (filtered out)
  D1: 64 - 128Hz  (filtered out)
"""
import numpy as np
import pywt


def compute_dwt_energy_per_channel(data_filtrada, fs=256, window_samples=256, step_samples=128):
    """
    Computes per-window DWT energy for sub-bands A5, D5, D4, D3 across all 23 channels.

    Parameters:
    - data_filtrada: ndarray of shape (23, total_samples)
    - fs: sampling frequency (default 256 Hz)
    - window_samples: samples per window (1s = 256)
    - step_samples: step between windows (50% overlap = 128)

    Returns:
    - dict with:
        "subbands": ["A5", "D5", "D4", "D3"]
        "times": list of window center times in seconds
        "energy": {
            "ch0": { "A5": [...], "D5": [...], "D4": [...], "D3": [...] },
            "ch1": { ... },
            ...
        }
    """
    n_channels, total_samples = data_filtrada.shape
    num_windows = (total_samples - window_samples) // step_samples + 1

    subbands = ["A5", "D5", "D4", "D3"]
    times = [(i * step_samples + window_samples / 2) / fs for i in range(num_windows)]

    energy = {f"ch{ch}": {sb: [] for sb in subbands} for ch in range(n_channels)}

    hanning_win = np.hanning(window_samples)

    for ch in range(n_channels):
        signal = data_filtrada[ch, :]

        for i in range(num_windows):
            start = i * step_samples
            end = start + window_samples
            window_data = signal[start:end] * hanning_win  # Apply Hanning

            # DWT Daubechies-4, 5 levels: returns [A5, D5, D4, D3, D2, D1]
            coeffs = pywt.wavedec(window_data, 'db4', level=5)
            a5, d5, d4, d3, d2, d1 = coeffs

            # Compute energy (sum of squares) for each retained sub-band
            energy[f"ch{ch}"]["A5"].append(float(np.sum(a5 ** 2)))
            energy[f"ch{ch}"]["D5"].append(float(np.sum(d5 ** 2)))
            energy[f"ch{ch}"]["D4"].append(float(np.sum(d4 ** 2)))
            energy[f"ch{ch}"]["D3"].append(float(np.sum(d3 ** 2)))

    return {
        "subbands": subbands,
        "times": times,
        "energy": energy
    }
