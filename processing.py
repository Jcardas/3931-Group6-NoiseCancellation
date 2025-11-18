''' 
Contains all processing code. 

Responsibilities:
  - Reading input and noise audio files
  - Performing noise cancellation / filtering
  - Returning processed audio to the GUI
  - Saving processed audio to disk
'''

def cancel_noise(input_path, noise_path):
  # Load the audio
  # FFT -> Noise subtraction
  # iFFT -> Reconstruct audio
  # Save processed audio
  
  
  output_file_path = "output.wav" # Temp
  
  return output_file_path