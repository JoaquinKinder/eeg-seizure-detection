"""
STFT Feature Extraction for EEG signals.
Computes the Short-Time Fourier Transform using a Hanning window (1s, 50% overlap).
Returns magnitude spectrogram per channel for visualization.
"""
import numpy as np
from scipy.signal import stft


def compute_stft_per_channel(data_filtrada, fs=256, window_samples=256, step_samples=128):
    """
    Computes STFT for each of the 23 EEG channels.

    Parameters:
    - data_filtrada: ndarray of shape (23, total_samples)
    - fs: sampling frequency in Hz (default 256)
    - window_samples: samples per window (1s at 256Hz = 256)
    - step_samples: step between windows (50% overlap = 128)

    Returns:
    - dict with:
        "freqs": list of frequency bins (Hz)
        "times": list of time centers (seconds)
        "magnitudes": dict { "ch0": 2D list [freq x time], "ch1": ..., ... }
    """
    n_channels = data_filtrada.shape[0]
    hop = step_samples  # noverlap = window_samples - hop

    results = {"freqs": None, "times": None, "magnitudes": {}}

    for ch in range(n_channels):
        signal = data_filtrada[ch, :]

        freqs, times, Zxx = stft(
            signal,
            fs=fs,
            window='hann',
            nperseg=window_samples,
            noverlap=window_samples - hop,
            boundary=None,
            padded=False
        )

        # Magnitude spectrum (absolute value)
        magnitude = np.abs(Zxx)

        # Only keep frequencies up to 40 Hz (already filtered, but trim for clarity)
        freq_mask = freqs <= 40.0
        freqs_trimmed = freqs[freq_mask]
        magnitude_trimmed = magnitude[freq_mask, :]

        if results["freqs"] is None:
            results["freqs"] = freqs_trimmed.tolist()
            results["times"] = times.tolist()

        # Store as 2D list [freq_bins x time_frames]
        results["magnitudes"][f"ch{ch}"] = magnitude_trimmed.tolist()

    return results
