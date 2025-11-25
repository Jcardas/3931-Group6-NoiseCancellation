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
from matplotlib import ticker
import customtkinter as ctk


def create_live_freq_domain_graphs(master, stft_freq):
    '''
    Creates a figure with two subplots for live frequency visualization.

    :param master: The parent customtkinter widget.
    :param stft_freq: The array of frequency bins from the STFT.
    :return: A dictionary containing the canvas widget, figure, axes, and line objects.
    '''
    try:
        # Create a figure with 3 subplots (input, cleaned, and noise)
        fig, ax = plt.subplots(1, 1, figsize=(7, 6))
        fig.patch.set_facecolor(COLOR_BACKGROUND)
        fig.tight_layout(pad=4.0)

        # Initial empty data
        initial_data = np.full_like(stft_freq, -100) # Start at -100 dB

        # Plot all three lines on the same axis
        line1, = ax.plot(stft_freq, initial_data, color=COLOR_GRAPH, label='Original Signal')
        line2, = ax.plot(stft_freq, initial_data, color=COLOR_ALT_GRAPH, label='Cleaned Signal')
        line3, = ax.plot(stft_freq, initial_data, color=COLOR_NOISE_GRAPH, label='Noise Signal')

        ax.set_title("Live Frequency Spectrum", color=COLOR_TEXT)
        ax.set_xscale('log')
        ax.set_ylabel("Magnitude (dB)", color=COLOR_TEXT)
        ax.set_xlabel("Frequency (Hz)", color=COLOR_TEXT)
        ax.set_facecolor(COLOR_CARD_BACKGROUND)
        ax.grid(True, color=COLOR_GRAPH, linestyle=':')
        ax.tick_params(colors=COLOR_TEXT)
        ax.set_ylim(-80, 20) # Set a more practical dB range

        # Custom formatter for the x-axis to show Hz/kHz
        def freq_formatter(x, pos):
            if x >= 1000:
                return f'{int(x/1000)} k'
            return f'{int(x)}'
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(freq_formatter))

        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()

        return {"canvas_widget": canvas.get_tk_widget(), "fig": fig, "ax": ax, "line1": line1, "line2": line2, "line3": line3, "canvas": canvas}
    
    except Exception as e:
        print(f"Error creating graph: {e}")
        error_label = ctk.CTkLabel(master, text=f"Could not load graph:\n{e}", text_color="red")
        return error_label