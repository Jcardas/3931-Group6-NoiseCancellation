import numpy as np
from scipy.io import wavfile


def read_audio(path):
    rate, data = wavfile.read(path)
    # Convert to float32 and mono immediately
    if data.ndim > 1:
        data = data.mean(axis=1)
    if np.issubdtype(data.dtype, np.integer):
        max_val = np.iinfo(data.dtype).max
        data = data.astype(np.float32) / max_val
    return rate, data


def save_audio(path, rate, data):
    # Scale back to int16
    data_scaled = np.int16(np.clip(data * 32767, -32767, 32767))
    wavfile.write(path, rate, data_scaled)


# FIX: Added 'fs' as the second parameter
def manual_stft(x, fs, window, nperseg, noverlap):
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

    # 'fs' is used here, so it must be an argument
    times = (np.arange(0, stft_matrix.shape[0]) * step + nperseg / 2) / fs
    frequencies = np.fft.rfftfreq(nperseg, d=1 / fs)
    return frequencies, times, stft_matrix


# FIX: Renamed first argument to 'stft_matrix_t' to match the body
def manual_istft(stft_matrix_t, fs, window, nperseg, noverlap):
    stft_matrix = (
        stft_matrix_t.T
    )  # This line requires the argument to be named stft_matrix_t
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
