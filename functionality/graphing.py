'''
Visualizes the output audio in frequency domain
using matplotlib.

Provides functions for displaying the graph.
'''
from ui.theme import *
import numpy as np
from scipy.io import wavfile
from scipy.fft import rfft, rfftfreq
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
import customtkinter as ctk


def create_freq_domain_graph(master, audio_path):
    '''
    Creates a frequency domain plot of an audio file and returns it as a Tkinter widget.

    :param master: The parent customtkinter widget.
    :param audio_path: The path to the .wav audio file.
    :return: A Tkinter widget containing the matplotlib plot.
    '''
    try:
        # 1. Read the audio file
        samplerate, data = wavfile.read(audio_path)
        # If stereo, take one channel
        if data.ndim > 1:
            data = data[:, 0]
        
        # 2. Perform FFT
        n_points = len(data)
        yf = rfft(data)
        xf = rfftfreq(n_points, 1 / samplerate)

        # 3. Create a Matplotlib figure and axes
        fig = Figure(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor(COLOR_BACKGROUND)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COLOR_CARD_BACKGROUND)

        # 4. Plot the data
        yf_abs = np.abs(yf)
        db_magnitude = 20 * np.log10(yf_abs + 1e-9) # Add epsilon to avoid log10(0)
        ax.plot(xf, db_magnitude, color=COLOR_BUTTON)
        ax.set_xscale('log') # Use a logarithmic scale for frequency
        ax.set_title("Frequency Domain", color=COLOR_TEXT)
        ax.set_xlabel("Frequency (Hz)", color=COLOR_TEXT)
        ax.set_ylabel("Magnitude (dB)", color=COLOR_TEXT)
        ax.grid(True, color=COLOR_BUTTON_HOVER, linestyle='--')
        ax.tick_params(axis='x', colors=COLOR_TEXT)
        ax.tick_params(axis='y', colors=COLOR_TEXT)

        # 5. Create and return the canvas widget
        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()
        return canvas.get_tk_widget()
    except Exception as e:
        print(f"Error creating graph: {e}")
        error_label = ctk.CTkLabel(master, text=f"Could not load graph:\n{e}", text_color="red")
        return error_label