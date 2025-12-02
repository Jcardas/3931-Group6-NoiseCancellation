import numpy as np
from .audio_utils import read_audio, manual_stft, manual_istft


class NoiseCanceller:
    def process(self, input_path, noise_path, M=256, alpha=1.05, beta=0.001):
        """
        Performs spectral subtraction to remove noise from audio.

        Args:
            input_path: Path to the noisy speech file.
            noise_path: Path to the noise profile file.
            M: Window size (FFT size).
            alpha: Over-subtraction factor (controls how aggressively noise is removed).
            beta: Spectral floor (prevents magnitude from hitting absolute zero/artifacts).

        Returns:
            A dictionary containing raw audio arrays and frequency domain data (dB) for plotting.
        """
        # 1. Load Data
        # Read the input (noisy audio) and the noise profile (pure noise sample)
        # Returns sample rate (rate) and normalized float32 audio data
        rate, input_data = read_audio(input_path)
        _, noise_data = read_audio(noise_path)

        # 2. Setup STFT
        # R is the hop size (overlap), set to 50% of the window size
        R = M // 2
        # Create a Hanning window to smooth segment edges and reduce spectral leakage
        window = np.hanning(M)
        # Calculate normalization factor to ensure correct amplitude scaling later
        norm_factor = np.sum(window) / 2

        # 3. Perform STFT
        # Convert the time-domain input signal into the frequency domain (complex numbers)
        f, t, input_stft = manual_stft(input_data, rate, window, M, R)
        # Convert the noise signal to frequency domain to analyze its characteristics
        _, _, noise_stft = manual_stft(noise_data, rate, window, M, R)

        # 4. Spectral Subtraction Logic
        # Calculate Magnitude of the Input Signal (|S|)
        mag_input = np.abs(input_stft)

        # Estimate the Noise Profile: Average the magnitude of the noise file across all time frames
        # This assumes the noise is relatively stationary (constant) over time
        mag_noise = np.mean(np.abs(noise_stft), axis=0, keepdims=True)

        # Save the Phase of the original input. We subtract magnitudes but must keep original phase
        # because the human ear is less sensitive to phase errors than magnitude errors.
        phase_input = np.angle(input_stft)

        # Subtract Noise:
        # Formula: |Denoised| = |Input| - (alpha * |Noise|)
        # np.maximum(..., ...) implements the "Spectral Floor":
        # It ensures the result never drops below a small fraction (beta) of the original signal.
        # This prevents negative magnitudes and reduces "musical noise" artifacts.
        mag_denoised = np.maximum(beta * mag_input, mag_input - alpha * mag_noise)

        # Reconstruct Complex STFT: Combine the new denoised magnitude with the original phase
        denoised_stft = mag_denoised * np.exp(1j * phase_input)

        # 5. ISTFT (Inverse Short-Time Fourier Transform)
        # Convert the modified frequency domain signal back into a time-domain audio waveform
        cleaned_audio = manual_istft(denoised_stft.T, rate, window, M, R)

        # 6. Prepare Graph Data
        # Convert magnitudes to Decibels (dB) for visualization (Logarithmic scale)
        # 20 * log10(|Mag|) is the standard formula for amplitude to dB
        # 1e-9 is added to prevent log(0) errors
        return {
            "sample_rate": rate,
            "original_audio": input_data,
            "cleaned_audio": cleaned_audio,
            "noise_audio": noise_data,
            "stft_freq": f,
            "stft_time": t,
            "original_mag_db": 20 * np.log10(np.abs(input_stft.T) / norm_factor + 1e-9),
            "cleaned_mag_db": 20
            * np.log10(np.abs(denoised_stft.T) / norm_factor + 1e-9),
            "noise_mag_db": 20 * np.log10(np.abs(mag_noise.T) / norm_factor + 1e-9),
        }
