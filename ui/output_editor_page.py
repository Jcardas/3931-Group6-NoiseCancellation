"""
This is the page where the user can view and play back the processed
audio file.

The processed audio is displayed in frequency domain using matplotlib
"""

import customtkinter as ctk
from tkinter import PhotoImage
import time
import numpy as np
import sounddevice as sd
import os
from .theme import *
from ui.file_selection_page import FileSelectionPage
from functionality.graphing import create_live_freq_domain_graphs


class OutputEditorPage(ctk.CTkFrame):
    """
    A page that displays the results of the audio processing, including
    the input, noise, and cleaned audio files, with playback controls
    and a live frequency domain graph.
    """

    def __init__(self, parent, controller):
        """
        Initializes the page.
        """
        super().__init__(parent, fg_color=COLOR_BACKGROUND)

        # Audio playback settings
        sd.default.latency = "high"
        sd.default.blocksize = 2048

        self.controller = controller
        self.graph_elements = None
        self.animation_job = None
        self.bg_cache = None

        # Playback State
        self.playback_start_time = 0.0
        self.paused_time = 0.0
        self.is_playing = False
        self.current_audio_key = "cleaned_audio"

        # --- UI Setup ---

        # --- Bottom Frame for Save Button ---
        # We pack this first (with side="bottom") to ensure it stays at the bottom
        # even when the main content expands.
        bottom_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        bottom_frame.pack(side="bottom", pady=20, fill="x")

        self.save_button = ctk.CTkButton(
            bottom_frame,
            text="Save Audio",
            font=("Arial", 14, "bold"),
            width=200,
            height=40,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            command=self.controller.save_files,
        )
        self.save_button.pack(pady=10)

        # --- Main Layout (Middle) ---
        row_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        row_frame.pack(pady=20, expand=True, fill="both", padx=40)

        # --- Left Panel: Audio Players ---
        left_panel = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        left_panel.pack(side="left", padx=(40, 20), fill="y")

        # Load Icons
        self.file_icon = PhotoImage(file="Assets/file.png")
        self.play_icon = PhotoImage(file="Assets/play.png").subsample(2, 2)
        self.pause_icon = PhotoImage(file="Assets/pause.png").subsample(2, 2)
        self.restart_icon = PhotoImage(file="Assets/restart.png").subsample(2, 2)

        # Storage for UI updates
        self.name_labels = {}
        self.play_buttons = {}

        # Create Rows
        self.create_player_row(left_panel, "Input Audio", "original_audio")
        self.create_player_row(left_panel, "Noise Sample", "noise_audio")
        self.create_player_row(left_panel, "Cleaned Output", "cleaned_audio")

        # Stop All Button
        ctk.CTkButton(
            left_panel,
            text="Stop All",
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            image=self.restart_icon,
            command=self.stop_playback,
        ).pack(pady=20)

        # --- Right Panel: Graph ---
        self.graph_frame = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        self.graph_frame.pack(side="left", expand=True, fill="both")

    def create_player_row(self, parent, title, key):
        """
        Creates a card with Icon (Left) and Text+Button (Right Column).
        The play button is placed BELOW the text.
        """
        card = ctk.CTkFrame(
            parent, fg_color=COLOR_CARD_BACKGROUND, width=300, height=140
        )
        card.pack(pady=10, padx=5)
        card.pack_propagate(False)

        # File icon
        icon_label = ctk.CTkLabel(card, image=self.file_icon, text="")
        icon_label.pack(side="left", padx=10, anchor="n", pady=15)

        # Column for Text and Button
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, pady=5)

        # Title
        ctk.CTkLabel(
            text_frame, text=title, text_color="gray", font=("Arial", 12)
        ).pack(anchor="w")

        # Filename
        name_label = ctk.CTkLabel(
            text_frame, text="...", text_color=COLOR_TEXT, font=("Arial", 14, "bold")
        )
        name_label.pack(anchor="w")
        self.name_labels[key] = name_label

        # Play Button
        btn = ctk.CTkButton(
            text_frame,
            text="",
            image=self.play_icon,
            width=40,
            height=30,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            command=lambda k=key: self.toggle_playback(k),
        )
        btn.pack(anchor="w", pady=(10, 0))
        self.play_buttons[key] = btn

        # Back button
        def button_event():
            self.controller.show_page(FileSelectionPage)

        backButton = ctk.CTkButton(
            self,
            text="<-",
            width=30,
            height=30,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            command=button_event,
        )
        backButton.place(x=10, y=10)

    def on_show(self):
        self.stop_playback()

        if self.controller.processing_results:
            res = self.controller.processing_results
            # Update filenames
            self.name_labels["original_audio"].configure(
                text=os.path.basename(self.controller.input_file)
            )
            self.name_labels["noise_audio"].configure(
                text=os.path.basename(self.controller.noise_file)
            )
            self.name_labels["cleaned_audio"].configure(
                text=os.path.basename(res["output_path"])
            )

            # Re-init graph
            if self.graph_elements:
                self.graph_elements["canvas_widget"].destroy()

            self.graph_elements = create_live_freq_domain_graphs(
                self.graph_frame, res["stft_freq"]
            )
            self.graph_elements["canvas_widget"].pack(expand=True, fill="both")

            # Graph animation setup
            for key in ["line1", "line2", "line3"]:
                self.graph_elements[key].set_animated(True)
                self.graph_elements[key].set_clip_on(True)

            self.bg_cache = None
            canvas = self.graph_elements["canvas"]

            def on_resize(event):
                self.bg_cache = None

            canvas.get_tk_widget().bind("<Configure>", on_resize)
            canvas.draw()
            self.bg_cache = canvas.copy_from_bbox(self.graph_elements["ax"].bbox)

    def toggle_playback(self, audio_key):
        if not self.controller.processing_results:
            return

        if self.current_audio_key != audio_key:
            self.stop_playback()
            self.current_audio_key = audio_key

        if self.is_playing:
            # PAUSE
            self.paused_time += time.time() - self.playback_start_time
            sd.stop()
            self.is_playing = False
            if self.animation_job:
                self.after_cancel(self.animation_job)
                self.animation_job = None

            self.play_buttons[self.current_audio_key].configure(image=self.play_icon)

        else:
            # PLAY
            results = self.controller.processing_results
            sample_rate = results["sample_rate"]
            audio_data = results[self.current_audio_key]

            start_sample = int(self.paused_time * sample_rate)

            if start_sample >= len(audio_data):
                self.paused_time = 0
                start_sample = 0

            data_toplay = np.ascontiguousarray(audio_data[start_sample:])
            sd.play(data_toplay, sample_rate)

            self.playback_start_time = time.time()
            self.is_playing = True

            self.play_buttons[self.current_audio_key].configure(image=self.pause_icon)
            self.update_plot()

    def stop_playback(self):
        sd.stop()
        self.is_playing = False
        self.paused_time = 0.0

        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

        for btn in self.play_buttons.values():
            btn.configure(image=self.play_icon)

    def update_plot(self):
        results = self.controller.processing_results
        elapsed_time = self.paused_time + (time.time() - self.playback_start_time)
        noise_mag = results["noise_stft_mag_db"]

        audio_data = results[self.current_audio_key]
        sample_rate = results["sample_rate"]
        duration = len(audio_data) / sample_rate

        if elapsed_time < duration or self.current_audio_key == "noise_audio":
            canvas = self.graph_elements["canvas"]
            ax = self.graph_elements["ax"]

            if self.bg_cache is None:
                canvas.draw()
                self.bg_cache = canvas.copy_from_bbox(ax.bbox)

            canvas.restore_region(self.bg_cache)

            # --- SELECTIVE DRAWING ---
            if self.current_audio_key == "original_audio":
                time_vector = results["stft_time"]
                time_index = np.searchsorted(time_vector, elapsed_time)
                if time_index < len(time_vector):
                    original_mag = results["original_stft_mag_db"][:, time_index]
                    self.graph_elements["line1"].set_ydata(original_mag)
                    ax.draw_artist(self.graph_elements["line1"])

            elif self.current_audio_key == "noise_audio":
                self.graph_elements["line3"].set_ydata(noise_mag)
                ax.draw_artist(self.graph_elements["line3"])

            elif self.current_audio_key == "cleaned_audio":
                time_vector = results["stft_time"]
                time_index = np.searchsorted(time_vector, elapsed_time)
                if time_index < len(time_vector):
                    original_mag = results["original_stft_mag_db"][:, time_index]
                    cleaned_mag = results["cleaned_stft_mag_db"][:, time_index]

                    self.graph_elements["line1"].set_ydata(original_mag)
                    self.graph_elements["line2"].set_ydata(cleaned_mag)
                    self.graph_elements["line3"].set_ydata(noise_mag)

                    ax.draw_artist(self.graph_elements["line1"])
                    ax.draw_artist(self.graph_elements["line2"])
                    ax.draw_artist(self.graph_elements["line3"])

            canvas.blit(ax.bbox)
            self.animation_job = self.after(30, self.update_plot)
        else:
            self.stop_playback()
