"""
Visualizes the output audio in frequency domain
using matplotlib.

Provides functions for displaying the graph.
"""

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
    """
    Creates a figure with two subplots for live frequency visualization.

    :param master: The parent customtkinter widget.
    :param stft_freq: The array of frequency bins from the STFT.
    :return: A dictionary containing the canvas widget, figure, axes, and line objects.
    """
    try:
        # 1. Initialize Figure
        # Create a single subplot with specific size (7x6 inches)
        fig, ax = plt.subplots(1, 1, figsize=(7, 6))
        # Set the background color of the figure to match the UI theme
        fig.patch.set_facecolor(COLOR_BACKGROUND)
        # Adjust spacing to prevent labels from being cut off
        fig.tight_layout(pad=4.0)

        # 2. Setup Initial Data
        # Create a dummy array of -100 dB (silence) to initialize the graph lines
        # This ensures the lines exist before the first update loop runs
        initial_data = np.full_like(stft_freq, -100)

        # 3. Create Plot Lines
        # Plot the "Original Signal" line and store the object (line1) to update later
        (line1,) = ax.plot(
            stft_freq, initial_data, color=COLOR_GRAPH, label="Original Signal"
        )
        # Plot the "Cleaned Signal" line
        (line2,) = ax.plot(
            stft_freq, initial_data, color=COLOR_ALT_GRAPH, label="Cleaned Signal"
        )
        # Plot the "Noise Signal" line
        (line3,) = ax.plot(
            stft_freq,
            initial_data,
            color=COLOR_NOISE_GRAPH,
            label="Noise Signal (Average)",
        )

        # 4. Configure Axis Styling
        ax.set_title("Live Frequency Spectrum", color=COLOR_TEXT)
        # Use Logarithmic scale for X-axis (standard for audio frequencies)
        ax.set_xscale("log")
        ax.set_ylabel("Magnitude (dB)", color=COLOR_TEXT)
        ax.set_xlabel("Frequency (Hz)", color=COLOR_TEXT)
        # Set inner graph background color
        ax.set_facecolor(COLOR_CARD_BACKGROUND)
        # Add a grid with dotted lines
        ax.grid(True, color=COLOR_GRAPH, linestyle=":")
        # Color the tick numbers (axis values) to match the text theme
        ax.tick_params(colors=COLOR_TEXT)
        # Fix the Y-axis range from -80dB (silence) to 20dB (loud)
        ax.set_ylim(-80, 20)

        # 5. Custom X-Axis Formatting
        # Define a function to convert raw Hz numbers into "k" format (e.g., 1000 -> 1 k)
        def freq_formatter(x, pos):
            if x >= 1000:
                return f"{int(x/1000)} k"
            return f"{int(x)}"

        # Apply the formatter to the X-axis
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(freq_formatter))

        # Show the legend to identify the 3 lines
        ax.legend()

        # 6. Embed in Tkinter
        # Create the canvas widget that holds the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()

        # Set the canvas background color to blend with the app
        canvas.get_tk_widget().configure(bg=COLOR_BACKGROUND)

        # 7. Return Handles
        # Return a dictionary containing the plot objects.
        # This allows the main loop to access 'line1', 'line2', etc.,
        # and update their data using .set_ydata() without redrawing the whole figure.
        return {
            "canvas_widget": canvas.get_tk_widget(),
            "fig": fig,
            "ax": ax,
            "line1": line1,
            "line2": line2,
            "line3": line3,
            "canvas": canvas,
        }

    except Exception as e:
        # Error Handling: If graphing fails, return a red error label instead of crashing
        print(f"Error creating graph: {e}")
        error_label = ctk.CTkLabel(
            master, text=f"Could not load graph:\n{e}", text_color="red"
        )
        return error_label
