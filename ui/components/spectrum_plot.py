import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np
from ui.theme import *


class SpectrumPlot(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        # Initialize the parent class (CTkFrame) to make this a valid UI widget
        super().__init__(master, **kwargs)

        # 1. Create Matplotlib Figure
        # Create a figure object (the container for the plot) with specific size and resolution
        self.fig = Figure(figsize=(7, 6), dpi=100)
        # Set the figure background color to match the application theme
        self.fig.patch.set_facecolor(COLOR_BACKGROUND)

        # Add a subplot (axes) to the figure. '111' means 1x1 grid, 1st subplot.
        self.ax = self.fig.add_subplot(111)

        # Run the setup function to configure labels, grids, and scales
        self.setup_axis()

        # 2. Create Canvas
        # The FigureCanvasTkAgg bridges Matplotlib (backend) and Tkinter (frontend)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        # Pack the canvas into the frame so it expands to fill available space
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 3. Initialization State
        # Dictionary to store the line objects (Original, Cleaned, Noise) for easy updates
        self.lines = {}
        # Variable to store the static background pixels for "blitting" optimization
        self.bg_cache = None

    def setup_axis(self):
        # Configure titles and labels with theme-appropriate colors
        self.ax.set_title("Live Frequency Spectrum", color=COLOR_TEXT)
        self.ax.set_ylabel("Magnitude (dB)", color=COLOR_TEXT)
        self.ax.set_xlabel("Frequency (Hz)", color=COLOR_TEXT)

        # Set the inner plot background color
        self.ax.set_facecolor(COLOR_CARD_BACKGROUND)

        # Use Logarithmic scale for X-axis (standard for audio analysis)
        self.ax.set_xscale("log")

        # Fix the Y-axis range (-80dB to 20dB) so the graph doesn't jump around
        self.ax.set_ylim(-80, 20)

        # Add a dotted grid for readability
        self.ax.grid(True, color=COLOR_GRAPH, linestyle=":")
        self.ax.tick_params(colors=COLOR_TEXT)

        # Define a custom function to format X-axis labels (e.g., 1000 -> 1kHz)
        def freq_formatter(x, pos):
            if x >= 1000:
                return f"{int(x/1000)}kHz"
            return f"{int(x)}Hz"

        # Apply the custom formatter to the X-axis
        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(freq_formatter))

    def init_plot(self, frequency_data):
        """Initialize lines with frequency data (x-axis)"""

        # 1. Clear Previous Lines
        # If this function is called again (e.g., filter update), remove old lines to prevent stacking
        if self.lines:
            for line in self.lines.values():
                line.remove()
            self.lines = {}

        # 2. Create Dummy Data
        # Initialize lines with -100dB (silence) so they are invisible/at bottom initially
        dummy_y = np.full_like(frequency_data, -100)

        # 3. Plot Lines
        # Plot the three distinct lines and store their references in the dictionary
        # The trailing comma (line,) unpacks the list returned by plot()
        (self.lines["original"],) = self.ax.plot(
            frequency_data, dummy_y, color=COLOR_GRAPH, label="Original"
        )
        (self.lines["cleaned"],) = self.ax.plot(
            frequency_data, dummy_y, color=COLOR_ALT_GRAPH, label="Cleaned"
        )
        (self.lines["noise"],) = self.ax.plot(
            frequency_data, dummy_y, color=COLOR_NOISE_GRAPH, label="Noise"
        )

        # Show legend and perform the initial draw
        self.ax.legend()
        self.canvas.draw()

        # 4. Cache Background (Blitting)
        # Copy the rendered background (grid, labels, title) into memory.
        # This allows us to redraw ONLY the lines later, saving massive CPU power.
        self.bg_cache = self.canvas.copy_from_bbox(self.ax.bbox)

    def update_db(self, original_db, cleaned_db, noise_db):
        """Fast update using blitting"""
        # If plot hasn't been initialized (cached), skip update to prevent errors
        if self.bg_cache is None:
            return

        # 1. Restore Background
        # Paste the cached background image over the plot, effectively erasing the old lines
        self.canvas.restore_region(self.bg_cache)

        # 2. Update Data
        # Update the Y-values of the lines with the new decibel data
        self.lines["original"].set_ydata(original_db)
        self.lines["cleaned"].set_ydata(cleaned_db)
        self.lines["noise"].set_ydata(noise_db)

        # 3. Redraw Artists
        # Efficiently redraw only the dynamic line elements
        self.ax.draw_artist(self.lines["original"])
        self.ax.draw_artist(self.lines["cleaned"])
        self.ax.draw_artist(self.lines["noise"])

        # 4. Blit
        # Update the screen with the newly drawn changes inside the bounding box
        self.canvas.blit(self.ax.bbox)
