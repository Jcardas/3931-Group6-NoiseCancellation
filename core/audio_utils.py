import numpy as np
from scipy.io import wavfile


def read_audio(path):
    # Read the WAV file from the specified path; returns sample rate and raw data
    rate, data = wavfile.read(path)

    # Check if the audio has more than one channel (e.g., stereo has 2 dimensions)
    if data.ndim > 1:
        # Convert stereo to mono by averaging the channels into a single stream
        data = data.mean(axis=1)

    # Check if the data type is integer (standard WAV is typically int16 or int32)
    if np.issubdtype(data.dtype, np.integer):
        # specific integer type limits (e.g., 32767 for int16)
        max_val = np.iinfo(data.dtype).max
        # Normalize the integer data to a floating-point range between -1.0 and 1.0
        data = data.astype(np.float32) / max_val

    return rate, data


def save_audio(path, rate, data):
    # Scale float data (-1.0 to 1.0) back to 16-bit integer range (-32767 to 32767)
    # np.clip ensures no values exceed the limits, preventing overflow distortion
    data_scaled = np.int16(np.clip(data * 32767, -32767, 32767))

    # Write the scaled integer data to a WAV file at the specified path
    wavfile.write(path, rate, data_scaled)


# Manually performs an Short-Time Fourier Transform (STFT)
def manual_stft(x, fs, window, nperseg, noverlap):
    # Calculate the step size (hop size) between consecutive windows
    step = nperseg - noverlap

    # Calculate total number of time frames that fit in the signal
    n_frames = (x.size - nperseg) // step + 1

    windowed_segments_list = []
    # Loop through each frame index
    for i in range(n_frames):
        # Determine start and end indices for the current segment
        start = i * step
        end = start + nperseg

        # Extract the segment and multiply by the window function (e.g., Hanning)
        # This tapers the edges to reduce spectral leakage
        segment = x[start:end] * window
        windowed_segments_list.append(segment)

    # Convert list of segments into a 2D numpy array
    windowed_segments = np.array(windowed_segments_list)

    # Perform Real FFT on each segment (row) to get frequency domain representation
    stft_matrix = np.fft.rfft(windowed_segments, axis=1)

    # Calculate time stamps for the center of each frame
    times = (np.arange(0, stft_matrix.shape[0]) * step + nperseg / 2) / fs

    # Calculate the specific frequency bins corresponding to the FFT result
    frequencies = np.fft.rfftfreq(nperseg, d=1 / fs)

    return frequencies, times, stft_matrix


# Manually Performs an Inverse STFT (ISTFT)
def manual_istft(stft_matrix_t, fs, window, nperseg, noverlap):
    # Transpose input to ensure shape is (n_frames, n_freq_bins)
    stft_matrix = stft_matrix_t.T

    n_frames = stft_matrix.shape[0]
    # Calculate step size based on overlap
    step = nperseg - noverlap

    # Calculate the total length of the reconstructed time-domain signal
    total_length = (n_frames - 1) * step + nperseg

    # Initialize array for the final output signal
    output_signal = np.zeros(total_length)
    # Initialize array to track the sum of window weights (for normalization)
    window_sum = np.zeros(total_length)

    # First pass: Calculate the sum of squared windows
    # This creates a normalization vector to correct amplitude changes caused by overlapping windows
    for i in range(n_frames):
        start = i * step
        end = start + nperseg
        window_sum[start:end] += window**2

    # Avoid division by zero errors by setting empty spots to a tiny number
    window_sum[window_sum == 0] = 1e-6

    # Second pass: Reconstruct the signal using Overlap-Add method
    for i in range(n_frames):
        start = i * step
        end = start + nperseg

        # Perform Inverse Real FFT to get back to time domain for this frame
        time_frame = np.fft.irfft(stft_matrix[i, :])

        # Apply the window function again (synthesis window)
        windowed_frame = time_frame * window

        # Add the frame to the output buffer, dividing by the window sum to normalize amplitude
        output_signal[start:end] += windowed_frame / window_sum[start:end]

    return output_signal
