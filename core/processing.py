import numpy as np
from .audio_utils import read_audio, manual_stft, manual_istft


class NoiseCanceller:
    def process(self, input_path, noise_path, M=256, alpha=1.05, beta=0.001):
        """
        Performs spectral subtraction.
        Returns a dictionary of DATA, not file paths.
        """
        # 1. Load Data
        rate, input_data = read_audio(input_path)
        _, noise_data = read_audio(noise_path)

        # 2. Setup STFT
        R = M // 2
        window = np.hanning(M)
        norm_factor = np.sum(window) / 2

        # 3. Perform STFT
        # FIX: Pass 'rate' as the second argument to manual_stft
        f, t, input_stft = manual_stft(input_data, rate, window, M, R)
        _, _, noise_stft = manual_stft(noise_data, rate, window, M, R)

        # 4. Spectral Subtraction Logic
        mag_input = np.abs(input_stft)
        mag_noise = np.mean(np.abs(noise_stft), axis=0, keepdims=True)
        phase_input = np.angle(input_stft)

        mag_denoised = np.maximum(beta * mag_input, mag_input - alpha * mag_noise)
        denoised_stft = mag_denoised * np.exp(1j * phase_input)

        # 5. ISTFT
        cleaned_audio = manual_istft(denoised_stft.T, rate, window, M, R)

        # 6. Prepare Graph Data (Log conversions here)
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
