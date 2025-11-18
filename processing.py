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

  # Load the audio files
  input_rate, input_data = wavfile.read(input_path)
  noise_rate, noise_data = wavfile.read(noise_path)

  # Resample noise if needed
  if noise_rate != input_rate:
      raise ValueError("Input and noise sample rates do not match.")

  # Ensure both inputs are the same length for noise subtraction
  min_len = min(len(input_data), len(noise_data))
  input_data = input_data[:min_len]
  noise_data = noise_data[:min_len]

  # Perform FFT on both signals
  input_fft = np.fft.rfft(input_data, axis=0)
  noise_fft = np.fft.rfft(noise_data, axis=0)

  # Subtract noise spectrum from input spectrum
  cleaned_fft = input_fft - noise_fft

  # Reconstruct the audio with inverse FFT
  cleaned_data = np.fft.irfft(cleaned_fft, n=min_len, axis=0)

  # Clip to original dtype range and convert type
  if input_data.dtype == np.int16:
      max_val = np.iinfo(np.int16).max
      min_val = np.iinfo(np.int16).min
      cleaned_data = np.clip(cleaned_data, min_val, max_val)
      cleaned_data = cleaned_data.astype(np.int16)
  else:
      # For other dtypes, just convert to original type
      cleaned_data = cleaned_data.astype(input_data.dtype)

  # Save processed audio to Downloads folder with prefix "cleaned_"
  downloads_folder = os.path.expanduser("~/Downloads")
  input_filename = os.path.basename(input_path)
  output_file_path = os.path.join(downloads_folder, f"cleaned_{input_filename}")
  wavfile.write(output_file_path, input_rate, cleaned_data)

  return output_file_path