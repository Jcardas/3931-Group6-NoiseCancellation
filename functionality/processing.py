"""
Processes the input audio with the noise file to remove noise.
Performs a STFT on the input using the noise. Then normalizes the audio
and outputs it to the Downloads folder.
"""

import numpy as np
from scipy.io import wavfile
from scipy import signal
import os

# ... [Keep imports and helper functions _to_mono_and_float, manual_stft, manual_istft unchanged] ...


def _to_mono_and_float(rate, data):
    """
    Converts audio data to mono and float format for processing.
    e.g: we perform the STFT on one signal only, instead of both channels in a stereo signal.
    """
    if data.ndim > 1:
        data = data.mean(axis=1)
    if np.issubdtype(data.dtype, np.integer):
        max_val = np.iinfo(data.dtype).max
        data = data.astype(np.float32) / max_val
    return data


def manual_stft(x, fs, window, nperseg, noverlap):
    # ... [Keep existing implementation] ...
    step = nperseg - noverlap
    n_frames = (x.size - nperseg) // step + 1
    windowed_segments_list = []
    for i in range(n_frames):
        start = i * step
        end = start + nperseg
        segment = x[start:end] * window
        windowed_segments_list.append(segment)
    windowed_segments = np.array(windowed_segments_list)
    stft_matrix = np.fft.rfft(windowed_segments, axis=1)
    times = (np.arange(0, stft_matrix.shape[0]) * step + nperseg / 2) / fs
    frequencies = np.fft.rfftfreq(nperseg, d=1 / fs)
    return frequencies, times, stft_matrix


def manual_istft(stft_matrix_t, fs, window, nperseg, noverlap):
    # ... [Keep existing implementation] ...
    stft_matrix = stft_matrix_t.T
    n_frames = stft_matrix.shape[0]
    step = nperseg - noverlap
    total_length = (n_frames - 1) * step + nperseg
    output_signal = np.zeros(total_length)
    window_sum = np.zeros(total_length)
    for i in range(n_frames):
        start = i * step
        end = start + nperseg
        window_sum[start:end] += window**2
    window_sum[window_sum == 0] = 1e-6
    for i in range(n_frames):
        start = i * step
        end = start + nperseg
        time_frame = np.fft.irfft(stft_matrix[i, :])
        windowed_frame = time_frame * window
        output_signal[start:end] += windowed_frame / window_sum[start:end]
    return output_signal


def cancel_noise(input_path, noise_path, M=256, alpha=1.05, beta=0.001):
    """
    Reduces noise from an audio file using spectral subtraction (STFT)
    """

    # Define STFT parameters dynamically based on M
    R = M // 2  # Hop size (50% overlap)
    window = np.hanning(M)

    # Step 1. Load files
    input_rate, input_data = wavfile.read(input_path)
    noise_rate, noise_data = wavfile.read(noise_path)

    if input_rate != noise_rate:
        raise ValueError("Input and noise audio must have the same sample rate.")

    input_data_float = _to_mono_and_float(input_rate, input_data)
    noise_data_float = _to_mono_and_float(noise_rate, noise_data)

    # Step 2. Perform STFT
    f, t, input_signal = manual_stft(
        input_data_float, input_rate, window, nperseg=M, noverlap=R
    )
    # We only need the magnitude of the noise
    _, _, noise_signal = manual_stft(
        noise_data_float, noise_rate, window, nperseg=M, noverlap=R
    )

    # Step 3. Noise Profile
    mag_noise = np.mean(np.abs(noise_signal), axis=0, keepdims=True)

    # Step 4. Spectral Subtraction
    mag_input = np.abs(input_signal)
    phase_input = np.angle(input_signal)

    # Apply Alpha and Beta
    mag_denoised = np.maximum(beta * mag_input, mag_input - alpha * mag_noise)

    denoised_signal = mag_denoised * np.exp(1j * phase_input)
    denoised_signal_T = denoised_signal.T

    # Step 5. ISTFT
    cleaned_data_float = manual_istft(
        denoised_signal_T, fs=input_rate, window=window, nperseg=M, noverlap=R
    )

    # Step 6. Normalize
    max_abs_val_input = (
        np.max(np.abs(input_data_float))
        if np.max(np.abs(input_data_float)) > 0
        else 1.0
    )
    gamma = 0.95
    scaling_target = 32767 * gamma
    scaling_factor = scaling_target / max_abs_val_input

    cleaned_data = np.zeros_like(cleaned_data_float, dtype=np.int16)
    cleaned_data_float_scaled = np.zeros_like(cleaned_data_float, dtype=np.float32)

    if max_abs_val_input > 0:
        cleaned_data_float_raw_scaled = cleaned_data_float * scaling_factor
        cleaned_data_float_scaled = cleaned_data_float_raw_scaled / 32767
        cleaned_data = np.int16(np.clip(cleaned_data_float_raw_scaled, -32767, 32767))

    # Step 7. Save path
    downloads_folder = os.path.expanduser("~/Downloads")
    input_filename = os.path.basename(input_path)
    output_file_path = os.path.join(downloads_folder, f"cleaned_{input_filename}")

    # Transpose for graphing (Frequency x Time)
    mag_input_T = mag_input.T
    mag_denoised_T = mag_denoised.T
    mag_noise_T = mag_noise.T

    return {
        "output_path": output_file_path,
        "sample_rate": input_rate,
        "original_audio": input_data_float,
        "cleaned_audio": cleaned_data_float_scaled,
        "noise_audio": noise_data_float,
        "stft_freq": f,
        "stft_time": t,
        "original_stft_mag_db": 20 * np.log10(mag_input_T + 1e-9),
        "cleaned_stft_mag_db": 20 * np.log10(mag_denoised_T + 1e-9),
        "noise_stft_mag_db": 20 * np.log10(mag_noise_T + 1e-9),
        "cleaned_data_int_final": cleaned_data,
        # --- NEW: Return parameters so UI can sync ---
        "parameters": {"M": M, "alpha": alpha, "beta": beta},
    }
