import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np
from ui.theme import *


class SpectrumPlot(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Create Figure
        self.fig = Figure(figsize=(7, 6), dpi=100)
        self.fig.patch.set_facecolor(COLOR_BACKGROUND)
        self.ax = self.fig.add_subplot(111)
        self.setup_axis()

        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Lines
        self.lines = {}
        self.bg_cache = None

    def setup_axis(self):
        self.ax.set_title("Live Frequency Spectrum", color=COLOR_TEXT)
        self.ax.set_ylabel("Magnitude (dB)", color=COLOR_TEXT)
        self.ax.set_xlabel("Frequency (Hz)", color=COLOR_TEXT)
        self.ax.set_facecolor(COLOR_CARD_BACKGROUND)
        self.ax.set_xscale("log")
        self.ax.set_ylim(-80, 20)
        self.ax.grid(True, color=COLOR_GRAPH, linestyle=":")
        self.ax.tick_params(colors=COLOR_TEXT)

        def freq_formatter(x, pos):
            if x >= 1000:
                return f"{int(x/1000)}kHz"
            return f"{int(x)}Hz"

        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(freq_formatter))

    def init_plot(self, frequency_data):
        """Initialize lines with frequency data (x-axis)"""

        if self.lines:
            for line in self.lines.values():
                line.remove()
            self.lines = {}

        dummy_y = np.full_like(frequency_data, -100)

        (self.lines["original"],) = self.ax.plot(
            frequency_data, dummy_y, color=COLOR_GRAPH, label="Original"
        )
        (self.lines["cleaned"],) = self.ax.plot(
            frequency_data, dummy_y, color=COLOR_ALT_GRAPH, label="Cleaned"
        )
        (self.lines["noise"],) = self.ax.plot(
            frequency_data, dummy_y, color=COLOR_NOISE_GRAPH, label="Noise"
        )

        self.ax.legend()
        self.canvas.draw()

        # Cache background for blitting (optimization)
        self.bg_cache = self.canvas.copy_from_bbox(self.ax.bbox)

    def update_db(self, original_db, cleaned_db, noise_db):
        """Fast update using blitting"""
        if self.bg_cache is None:
            return

        self.canvas.restore_region(self.bg_cache)

        self.lines["original"].set_ydata(original_db)
        self.lines["cleaned"].set_ydata(cleaned_db)
        self.lines["noise"].set_ydata(noise_db)

        self.ax.draw_artist(self.lines["original"])
        self.ax.draw_artist(self.lines["cleaned"])
        self.ax.draw_artist(self.lines["noise"])

        self.canvas.blit(self.ax.bbox)
