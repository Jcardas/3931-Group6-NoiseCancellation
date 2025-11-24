''' 
Processes the input audio with the noise file to remove noise.

Performs a STFT on the input using the noise. Then normalizes the audio
and outputs it to the Downloads folder.
'''

import numpy as np
from scipy.io import wavfile
from scipy import signal
import os

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

def cancel_noise(input_path, noise_path):
    '''
    Reduces noise from an audio file using spectral subtraction (STFT)

    Learn more at this link
    https://www.dsprelated.com/freebooks/sasp/Short_Time_Fourier_Transform.html

    :param input_path: Path to the noisy audio file (.wav).
    :param noise_path: Path to the audio file containing a sample of the noise (.wav).
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
    _, _, Zxx_input = signal.stft(input_data_float, fs=input_rate)
    _, _, Zxx_noise = signal.stft(noise_data_float, fs=input_rate)

    # Step 3. Create noise profile (mean magnitude of noise frequency spectrum)
    noise_profile = np.mean(np.abs(Zxx_noise), axis=1, keepdims=True)

    # Step 4. Subtract noise profile from input signal (spectral subtraction)
    mag_input = np.abs(Zxx_input)
    phase_input = np.angle(Zxx_input)
    mag_denoised = np.maximum(0, mag_input - noise_profile) # Use maximum to avoid negative values
    Zxx_denoised = mag_denoised * np.exp(1j * phase_input)

    # Step 5. Perform Inverse STFT to get back to the time domain
    _, cleaned_data_float = signal.istft(Zxx_denoised, fs=input_rate)

    # Step 6. Normalize the output audio and convert to 16-bit integer for saving
    cleaned_data = np.int16(cleaned_data_float / np.max(np.abs(cleaned_data_float)) * 32767)

    # Step 7. Save processed audio to Downloads folder with prefix "cleaned_"
    downloads_folder = os.path.expanduser("~/Downloads")
    input_filename = os.path.basename(input_path)
    output_file_path = os.path.join(downloads_folder, f"cleaned_{input_filename}")
    wavfile.write(output_file_path, input_rate, cleaned_data)

    return output_file_path