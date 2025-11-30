''' 
Processes the input audio with the noise file to remove noise.

Performs a STFT on the input using the noise. Then normalizes the audio
and outputs it to the Downloads folder.
'''

import numpy as np
from scipy.io import wavfile
from scipy import signal
import os

M = 1024  # STFT window size
R = M // 2   # STFT hop size
window = np.hanning(M)  # Hanning window

def _to_mono_and_float(rate, data):
    '''
    Converts audio data to mono and float format for processing.
    e.g: we perform the STFT on one signal only, instead of both channels in a stereo signal.
    '''
    # If stereo, average the channels
    if data.ndim > 1:
        data = data.mean(axis=1)
    # Convert to float
    if np.issubdtype(data.dtype, np.integer):
        # Get the maximum possible value for the integer type
        max_val = np.iinfo(data.dtype).max
        data = data.astype(np.float32) / max_val
    return data

def manual_stft(x, fs, window, nperseg, noverlap):
    '''
    Manually computes the Short-Time Fourier Transform (STFT) of a signal.
    
    :param x: Input signal (time-domain audio data).
    :param fs: Sampling frequency (rate).
    :param window: Window function (Hanning M).
    :param nperseg: Number of samples per segment (M).
    :param noverlap: Number of overlapping samples between segments (R).
    :return: Frequencies, times, and STFT matrix. 
    '''
    # The hop size (R) is the difference between the segment size and the overlap
    step = nperseg - noverlap

    # 1. Calculate the number of full frames available
    n_frames = (x.size - nperseg) // step + 1
    
    # Initialize a list to hold the windowed segments
    windowed_segments_list = []

    # 2. Framing using a loop for boundary handling
    for i in range(n_frames):
        start = i * step
        end = start + nperseg
        
        # Extract segment and apply window
        segment = x[start:end] * window
        windowed_segments_list.append(segment)

    # Convert the list of segments into a 2D NumPy array
    windowed_segments = np.array(windowed_segments_list)

    # 3. Compute the FFT for each windowed segment
    stft_matrix = np.fft.rfft(windowed_segments, axis=1)

    # 4. Generate time and frequency vectors
    # Time vector: center time of each frame (in seconds)
    times = (np.arange(0, stft_matrix.shape[0]) * step + nperseg / 2) / fs
    # Frequency vector: center frequencies for each FFT bin
    frequencies = np.fft.rfftfreq(nperseg, d=1/fs)

    return frequencies, times, stft_matrix

def manual_istft(stft_matrix_t, fs, window, nperseg, noverlap):
    '''
    Manually computes the Inverse Short-Time Fourier Transform (ISTFT) of a signal.
    
    :param stft_matrix_t: Transposed STFT matrix (time x frequency).
    :param fs: Sampling frequency (rate).
    :param window: Window function (Hanning M).
    :param nperseg: Number of samples per segment (M).
    :param noverlap: Number of overlapping samples between segments (R).
    :return: Reconstructed time-domain signal.
    '''
    stft_matrix = stft_matrix_t.T  # Transpose back to frequency x time for iterations

    n_frames = stft_matrix.shape[0]
    step = nperseg - noverlap

    # Estimate the length of the output signal
    total_length = (n_frames - 1) * step + nperseg

    output_signal = np.zeros(total_length)

    # Compute the normalization factor (window sum of squares)
    window_sum = np.zeros(total_length)
    for i in range(n_frames):
        start = i * step
        end = start + nperseg

        window_sum[start:end] += window ** 2
    
    window_sum[window_sum == 0] = 1e-6  # Prevent division by zero

    # Inverse FFT using overlap-add method
    for i in range(n_frames):
        start = i * step
        end = start + nperseg

        # Inverse FFT to get the current frame's frequency data
        time_frame = np.fft.irfft(stft_matrix[i, :])

        # Apply the window to the time frame
        windowed_frame = time_frame * window

        # Overlap-add to reconstruct the output signal
        output_signal[start:end] += windowed_frame / window_sum[start:end]

    return output_signal


def cancel_noise(input_path, noise_path, use_highpass=False, highpass_cutoff=200):
    '''
    Reduces noise from an audio file using spectral subtraction (STFT)

    Learn more at this link
    https://www.dsprelated.com/freebooks/sasp/Short_Time_Fourier_Transform.html

    :param input_path: Path to the noisy audio file (.wav).
    :param noise_path: Path to the audio file containing a sample of the noise (.wav).
    :param use_highpass: Boolean flag to enable the high-pass filter.
    :param highpass_cutoff: The cutoff frequency for the high-pass filter.
    :return: The path to the cleaned output audio file.
    '''
    # Step 1. Load the audio files and convert to a processable format (mono, float)
    input_rate, input_data = wavfile.read(input_path)
    noise_rate, noise_data = wavfile.read(noise_path)

    if input_rate != noise_rate:
        raise ValueError("Input and noise audio must have the same sample rate.")

    input_data_float = _to_mono_and_float(input_rate, input_data)
    noise_data_float = _to_mono_and_float(noise_rate, noise_data)

    # Step 2. Perform STFT on both signals
    # TODO: manually perform STFT
    f, t, input_signal = manual_stft(input_data_float, input_rate, window, nperseg=M, noverlap=R)
    f_noise, _, noise_signal = manual_stft(noise_data_float, noise_rate, window, nperseg=M, noverlap=R) # We only need the magnitude from this

    # Step 3. Create noise profile (mean magnitude of noise frequency spectrum)
    mag_noise = np.mean(np.abs(noise_signal), axis=0, keepdims=True)

    # Step 4. Subtract noise profile from input signal (spectral subtraction)
    mag_input = np.abs(input_signal) # Magnitude
    phase_input = np.angle(input_signal) # Phase

    alpha = 1.05 # Over-subtraction factor
    beta = 0.001 # Flooring factor to avoid negative values

    # THIS IS THE OUTPUT SIGNAL
    mag_denoised = np.maximum(beta * mag_input, mag_input - alpha * mag_noise) # Use maximum to avoid negative values

    # --- High-pass filter: Remove frequencies below cutoff if enabled ---
    if use_highpass:
        # Find the indices of the frequency bins that are below the cutoff
        low_freq_indices = np.where(f < highpass_cutoff)[0]
        mag_denoised[low_freq_indices, :] = 0 # Set magnitude to 0 for these frequencies

    denoised_signal = mag_denoised * np.exp(1j * phase_input)
    denoised_signal_T = denoised_signal.T 

    # Step 5. Perform Inverse STFT to get back to the time domain (Added transpose and fixed parameters to match manual STFT)
    ## _, cleaned_data_float = signal.istft(denoised_signal_T, fs=input_rate, window=window, nperseg=M, noverlap=R)
    cleaned_data_float = manual_istft(denoised_signal_T, fs=input_rate, window=window, nperseg=M, noverlap=R)

    # Step 6. Normalize the output audio and convert to 16-bit integer for saving
    # Currently manual stft produces audios that are too loud in amplitude. We need to scale them down for proper playback in the UI. 
    max_abs_val_input = np.max(np.abs(input_data_float)) if np.max(np.abs(input_data_float)) > 0 else 1.0
    
    # Global gain factor. This is set low to prevent loud amplification in the UI player.
    gamma = 0.95
    
    # Calculate the scale factor to bring the audio down to the target level (32767 * gamma)
    scaling_target = 32767 * gamma
    
    # Calculate the scale we need for the raw float data:
    # Scale_Factor = Target_Int_Max / Original_Float_Max
    scaling_factor = scaling_target / max_abs_val_input 
    
     # Initialize scaled output arrays 
    cleaned_data_float_scaled = np.zeros_like(cleaned_data_float, dtype=np.float32) 
    cleaned_data = np.zeros_like(cleaned_data_float, dtype=np.int16) 
    
    if max_abs_val_input > 0:
        # Scale the raw float data to the integer target range (32767 * gamma)
        cleaned_data_float_raw_scaled = cleaned_data_float * scaling_factor
        
        # SCALED float version for UI return (range [-gamma, gamma])
        cleaned_data_float_scaled = cleaned_data_float_raw_scaled / 32767
        
        # 16-bit integer version for WAV writing
        cleaned_data = np.int16(np.clip(cleaned_data_float_raw_scaled, -32767, 32767))

    # Step 7. Save processed audio to Downloads folder with prefix "cleaned_"
    downloads_folder = os.path.expanduser("~/Downloads")
    input_filename = os.path.basename(input_path)
    output_file_path = os.path.join(downloads_folder, f"cleaned_{input_filename}")
    wavfile.write(output_file_path, input_rate, cleaned_data)

    mag_input_T = mag_input.T
    mag_denoised_T = mag_denoised.T
    mag_noise_T = mag_noise.T

    # Return a dictionary with all necessary data for playback and visualization
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
        "noise_stft_mag_db": 20 * np.log10(mag_noise_T + 1e-9)
    
    }