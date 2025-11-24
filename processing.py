''' 
Contains all processing code. 

Responsibilities:
  - Reading input and noise audio files
  - Performing noise cancellation / filtering
  - Returning processed audio to the GUI
  - Saving processed audio to disk
'''

def cancel_noise(input_path, noise_path):
  import numpy as np
  from scipy.io import wavfile
  import os

 # This all doesnt work very good.

  # Load the audio files
  input_rate, input_data = wavfile.read(input_path)
  noise_rate, noise_data = wavfile.read(noise_path)

  # Checking sample rate of each file
  if noise_rate != input_rate:
      raise ValueError("Input and noise sample rates do not match.")

  # Take a window of noise data if it's longer than input
  min_len = min(len(input_data), len(noise_data))
  input_data = input_data[:min_len]
  noise_data = noise_data[:min_len]

  # Apply a Hann window to isolate a clean noise sample
  hann_window = np.hanning(min_len)
  noise_data = noise_data * hann_window

  # Perform FFT on both signals
  input_fft = np.fft.rfft(input_data, axis=0)
  noise_fft = np.fft.rfft(noise_data, axis=0)

  # --- Wiener Filter Noise Reduction (best for background noise) ---

  # Magnitudes and phase
  input_mag = np.abs(input_fft)
  noise_mag = np.abs(noise_fft)
  input_phase = np.angle(input_fft)

  # Power spectral densities
  input_psd = input_mag ** 2
  noise_psd = noise_mag ** 2

  # Avoid division by zero
  noise_psd = np.maximum(noise_psd, 1e-12)

  # Compute Wiener gain: G = SNR / (SNR + 1)
  snr = np.maximum(input_psd / noise_psd - 1, 0)
  gain = snr / (snr + 1)

  # Apply smoothing to avoid artifacts
  gain = 0.8 * gain + 0.2 * np.clip(gain, 0.1, 1.0)

  # Apply gain to magnitude
  cleaned_mag = gain * input_mag

  # Reconstruct FFT
  cleaned_fft = cleaned_mag * np.exp(1j * input_phase)

  # Reconstruct the audio with inverse FFT
  cleaned_data = np.fft.irfft(cleaned_fft, n=min_len, axis=0)

  # Normalize cleaned audio to prevent clipping / extreme loudness
  max_val = np.max(np.abs(cleaned_data))
  if max_val > 0:
      cleaned_data = cleaned_data / max_val  # scale to -1..1 range
      cleaned_data = (cleaned_data * 0.8 * 32767).astype(np.int16)  # safe headroom
  else:
      cleaned_data = cleaned_data.astype(np.int16)

  # Save processed audio to Downloads folder with prefix "cleaned_"
  downloads_folder = os.path.expanduser("~/Downloads")
  input_filename = os.path.basename(input_path)
  output_file_path = os.path.join(downloads_folder, f"cleaned_{input_filename}")
  wavfile.write(output_file_path, input_rate, cleaned_data)

  return output_file_path