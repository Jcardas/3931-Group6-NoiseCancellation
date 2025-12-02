"""
This is the page where the user can view and play back the processed
audio file.
"""

import customtkinter as ctk
from tkinter import PhotoImage, messagebox
import time
import numpy as np
import sounddevice as sd
import os
from ..theme import *
from ui.pages.file_selection import FileSelectionPage
from ui.components.spectrum_plot import SpectrumPlot


class OutputEditorPage(ctk.CTkFrame):
    """
    A page that displays the results, playback controls, and
    the live frequency domain graph using the SpectrumPlot component.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BACKGROUND)

        # Audio playback settings
        sd.default.latency = "high"
        sd.default.blocksize = 2048

        self.controller = controller
        self.animation_job = None

        # Playback State
        self.playback_start_time = 0.0
        self.paused_time = 0.0
        self.is_playing = False
        self.current_audio_key = "cleaned_audio"

        # --- UI Setup ---

        # Back Button
        self.back_button = ctk.CTkButton(
            self,
            text="<-",
            width=30,
            height=30,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            command=self.go_back,
        )
        self.back_button.place(x=10, y=10)

        # --- Main Layout ---
        row_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        row_frame.pack(side="left", pady=20, expand=True, fill="both", padx=40)

        # --- Left Panel ---
        left_panel = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        left_panel.pack(side="left", padx=(40, 20), fill="y")

        # Load Icons
        self.file_icon = PhotoImage(file="Assets/file.png")
        self.play_icon = PhotoImage(file="Assets/play.png").subsample(2, 2)
        self.pause_icon = PhotoImage(file="Assets/pause.png").subsample(2, 2)

        self.audio_cards = {}
        self.name_labels = {}

        # Create Rows
        self.create_player_row(left_panel, "Input Audio", "original_audio")
        self.create_player_row(left_panel, "Noise Sample", "noise_audio")
        self.create_player_row(left_panel, "Cleaned Output", "cleaned_audio")

        # --- Filter Settings ---
        self.settings_frame = ctk.CTkFrame(
            left_panel, fg_color=COLOR_CARD_BACKGROUND, border_width=2
        )
        self.settings_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(
            self.settings_frame,
            text="Filter Settings",
            font=("Arial", 14, "bold"),
            text_color=COLOR_TEXT,
        ).pack(pady=(10, 5))

        input_grid = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        input_grid.pack(pady=5)

        # Inputs (M, Alpha, Beta)
        self.create_setting_input(input_grid, "M (Size):", 0, "256", "m_entry")
        self.create_setting_input(
            input_grid, "Alpha (Over-subtraction):", 1, "1.05", "alpha_entry"
        )
        self.create_setting_input(
            input_grid, "Beta (Flooring Factor):", 2, "0.001", "beta_entry"
        )

        ctk.CTkButton(
            self.settings_frame,
            text="Update Filter",
            fg_color=COLOR_ALT_GRAPH,
            hover_color="#E02E2E",
            height=30,
            command=self.update_filter,
        ).pack(pady=10, padx=10, fill="x")

        # Save Button
        ctk.CTkButton(
            left_panel,
            text="Save Cleaned Audio",
            font=("Arial", 14, "bold"),
            height=40,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            command=self.controller.save_output,
        ).pack(pady=10, side="bottom")

        # --- Right Panel: Graph ---
        self.graph_frame = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        self.graph_frame.pack(side="left", expand=True, fill="both")

        # INSTANTIATE NEW COMPONENT
        self.spectrum_plot = SpectrumPlot(self.graph_frame)
        self.spectrum_plot.pack(expand=True, fill="both")

        # Controls
        self.controls_frame = ctk.CTkFrame(self.graph_frame, fg_color=COLOR_BACKGROUND)
        self.controls_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.play_pause_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.play_icon,
            width=40,
            height=30,
            fg_color=COLOR_BUTTON,
            command=self.toggle_playback,
        )
        self.play_pause_btn.pack(side="left", padx=(0, 10))

        self.seek_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=1,
            command=self.on_seek,
            fg_color=COLOR_DISABLED,
            progress_color=COLOR_BUTTON,
        )
        self.seek_slider.pack(side="left", fill="x", expand=True)
        self.seek_slider.set(0)

    def create_setting_input(self, parent, label, row, default, attr_name):
        ctk.CTkLabel(parent, text=label, text_color=COLOR_TEXT).grid(
            row=row, column=0, padx=5, pady=2
        )
        entry = ctk.CTkEntry(
            parent, width=60, fg_color=COLOR_BACKGROUND, text_color=COLOR_TEXT
        )
        entry.insert(0, default)
        entry.grid(row=row, column=1, padx=5, pady=2)
        setattr(self, attr_name, entry)

    def create_player_row(self, parent, title, key):
        card = ctk.CTkFrame(
            parent, fg_color=COLOR_CARD_BACKGROUND, width=300, height=80, border_width=2
        )
        card.pack(pady=5, padx=5)
        card.pack_propagate(False)
        self.audio_cards[key] = card

        card.bind("<Button-1>", lambda e: self.select_audio(key))

        ctk.CTkLabel(card, image=self.file_icon, text="").pack(side="left", padx=10)

        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            text_frame, text=title, text_color="gray", font=("Arial", 12)
        ).pack(anchor="w")
        self.name_labels[key] = ctk.CTkLabel(
            text_frame, text="...", text_color=COLOR_TEXT, font=("Arial", 14, "bold")
        )
        self.name_labels[key].pack(anchor="w")

        # Pass click events to children
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e: self.select_audio(key))
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e: self.select_audio(key))

    def select_audio(self, key):
        self.current_audio_key = key
        for k, card in self.audio_cards.items():
            card.configure(
                border_color=COLOR_BUTTON if k == key else COLOR_CARD_BACKGROUND
            )

        self.update_graph_to_time(self.paused_time)

        if self.is_playing:
            sd.stop()
            self.start_playback_stream()

    def go_back(self):
        self.stop_playback()
        self.controller.unbind("<space>")
        self.controller.show_page("FileSelectionPage")  # Pass string name

    def update_filter(self):
        try:
            M = int(self.m_entry.get())
            alpha = float(self.alpha_entry.get())
            beta = float(self.beta_entry.get())
            if M <= 0:
                raise ValueError
            self.stop_playback()
            self.controller.run_processing(M, alpha, beta)
        except ValueError:
            messagebox.showerror("Error", "Invalid Input")

    def on_show(self):
        self.stop_playback()
        self.seek_slider.set(0)
        self.controller.bind("<space>", lambda event: self.toggle_playback())

        res = self.controller.processing_results
        if not res:
            return

        params = getattr(self.controller, "current_parameters", {})
        if params:
            self.m_entry.delete(0, "end")
            self.m_entry.insert(0, str(params.get("M", 256)))

            self.alpha_entry.delete(0, "end")
            self.alpha_entry.insert(0, str(params.get("alpha", 1.05)))

            self.beta_entry.delete(0, "end")
            self.beta_entry.insert(0, str(params.get("beta", 0.001)))

        # Update Labels
        self.name_labels["original_audio"].configure(
            text=os.path.basename(self.controller.input_path)
        )
        self.name_labels["noise_audio"].configure(
            text=os.path.basename(self.controller.noise_path)
        )
        self.name_labels["cleaned_audio"].configure(text="Cleaned Output.wav")

        # Init Graph Component
        self.spectrum_plot.init_plot(res["stft_freq"])
        self.select_audio("cleaned_audio")

    def toggle_playback(self, event=None):
        if self.is_playing:
            self.paused_time += time.time() - self.playback_start_time
            self.stop_playback(reset=False)
        else:
            self.start_playback_stream()
            self.is_playing = True
            self.play_pause_btn.configure(image=self.pause_icon)
            self.update_animation()

    def start_playback_stream(self):
        res = self.controller.processing_results
        rate = res["sample_rate"]
        data = res[self.current_audio_key]
        start = int(self.paused_time * rate)

        if start >= len(data):
            self.paused_time = 0
            start = 0

        sd.play(np.ascontiguousarray(data[start:]), rate)
        self.playback_start_time = time.time()

    def stop_playback(self, reset=True):
        sd.stop()
        self.is_playing = False
        if reset:
            self.paused_time = 0
            self.seek_slider.set(0)
        self.play_pause_btn.configure(image=self.play_icon)
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def on_seek(self, value):
        res = self.controller.processing_results
        if not res:
            return
        duration = len(res[self.current_audio_key]) / res["sample_rate"]
        self.paused_time = value * duration
        self.update_graph_to_time(self.paused_time)
        if self.is_playing:
            sd.stop()
            self.start_playback_stream()

    def update_graph_to_time(self, t):
        res = self.controller.processing_results
        if not res:
            return

        # Find index in STFT time array
        idx = np.searchsorted(res["stft_time"], t)
        if idx >= len(res["stft_time"]):
            idx = len(res["stft_time"]) - 1

        # Update Component
        self.spectrum_plot.update_db(
            res["original_mag_db"][:, idx],
            res["cleaned_mag_db"][:, idx],
            res["noise_mag_db"][:, 0],  # Noise profile is constant (average)
        )

    def update_animation(self):
        if not self.is_playing:
            return

        res = self.controller.processing_results
        elapsed = self.paused_time + (time.time() - self.playback_start_time)
        duration = len(res[self.current_audio_key]) / res["sample_rate"]

        if elapsed < duration:
            self.update_graph_to_time(elapsed)
            self.seek_slider.set(elapsed / duration)
            self.animation_job = self.after(30, self.update_animation)
        else:
            self.stop_playback()
