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

        # --- Main Layout (Middle) ---
        row_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        row_frame.pack(side="left", pady=20, expand=True, fill="both", padx=40)

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
        self.audio_cards = {}  # Store card frames to update borders

        # Create Rows
        self.create_player_row(left_panel, "Input Audio", "original_audio")
        self.create_player_row(left_panel, "Noise Sample", "noise_audio")
        self.create_player_row(left_panel, "Cleaned Output", "cleaned_audio")

        # Save Button
        self.save_button = ctk.CTkButton(
            left_panel,
            text="Save Cleaned Audio",
            font=("Arial", 14, "bold"),
            width=200,
            height=40,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            command=self.controller.save_files,
        )
        self.save_button.pack(pady=10)

        # --- Right Panel: Graph ---
        self.graph_frame = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        self.graph_frame.pack(side="left", expand=True, fill="both")

        # --- Playback Controls (Bottom of Graph) ---
        self.controls_frame = ctk.CTkFrame(self.graph_frame, fg_color=COLOR_BACKGROUND)
        self.controls_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        # Play/Pause Button
        self.play_pause_btn = ctk.CTkButton(
            self.controls_frame,
            text="",
            image=self.play_icon,
            width=40,
            height=30,
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            command=self.toggle_playback,
        )
        self.play_pause_btn.pack(side="left", padx=(0, 10))

        # Scrubber Slider
        self.seek_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=1,
            command=self.on_seek,
            fg_color=COLOR_DISABLED,
            progress_color=COLOR_BUTTON,
            height=20,
        )
        self.seek_slider.pack(side="left", fill="x", expand=True)
        self.seek_slider.set(0)

    def create_player_row(self, parent, title, key):
        """
        Creates a clickable card for selecting the audio source.
        """
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_CARD_BACKGROUND,
            width=300,
            height=100,
            border_width=2,
            border_color=COLOR_CARD_BACKGROUND,  # Default invisible border
        )
        card.pack(pady=10, padx=5)
        card.pack_propagate(False)

        # Store reference
        self.audio_cards[key] = card

        # Click handler
        def on_click(event):
            self.select_audio(key)

        # Bind click to card
        card.bind("<Button-1>", on_click)

        # File icon
        icon_label = ctk.CTkLabel(card, image=self.file_icon, text="")
        icon_label.pack(side="left", padx=10, anchor="center")
        icon_label.bind("<Button-1>", on_click)

        # Column for Text
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, pady=20)
        text_frame.bind("<Button-1>", on_click)

        # Title
        title_lbl = ctk.CTkLabel(
            text_frame, text=title, text_color="gray", font=("Arial", 12)
        )
        title_lbl.pack(anchor="w")
        title_lbl.bind("<Button-1>", on_click)

        # Filename
        name_label = ctk.CTkLabel(
            text_frame, text="...", text_color=COLOR_TEXT, font=("Arial", 14, "bold")
        )
        name_label.pack(anchor="w")
        name_label.bind("<Button-1>", on_click)
        self.name_labels[key] = name_label

    def select_audio(self, key):
        """
        Selects the audio source for playback and visualization.
        """
        if self.current_audio_key == key:
            return  # Already selected

        self.current_audio_key = key

        # 1. Visual Feedback (Border Highlight)
        for k, card in self.audio_cards.items():
            if k == key:
                card.configure(border_color=COLOR_BUTTON)
            else:
                card.configure(border_color=COLOR_CARD_BACKGROUND)

        # 2. Update Graph
        self._draw_graph_at(self.paused_time)

        # 3. Handle Playback Transition
        if self.is_playing:
            # If playing, seamlessly switch to the new audio at the same timestamp
            sd.stop()
            self.start_playback_stream()

    def go_back(self):
        """
        Handles navigating back to the selection page.
        """
        self.stop_playback()
        # Unbind spacebar to prevent issues on other pages
        self.controller.unbind("<space>")
        self.controller.show_page(FileSelectionPage)

    def on_show(self):
        self.stop_playback()
        self.seek_slider.set(0)  # Reset slider

        # Bind Spacebar for Play/Pause
        self.controller.bind("<space>", lambda event: self.toggle_playback())

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

            # Highlight the default selected audio (cleaned)
            self.current_audio_key = "cleaned_audio"  # Ensure state matches visual
            self.select_audio("cleaned_audio")

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

    def toggle_playback(self, event=None):
        """
        Toggles between Play and Pause states.
        Arguments: event is optional (for spacebar binding)
        """
        if not self.controller.processing_results:
            return

        if self.is_playing:
            # PAUSE
            self.paused_time += time.time() - self.playback_start_time
            sd.stop()
            self.is_playing = False
            if self.animation_job:
                self.after_cancel(self.animation_job)
                self.animation_job = None

            self.play_pause_btn.configure(image=self.play_icon)

        else:
            # PLAY
            self.start_playback_stream()
            self.is_playing = True
            self.play_pause_btn.configure(image=self.pause_icon)
            self.update_plot()

    def start_playback_stream(self):
        """
        Helper to start the sounddevice stream from the current paused_time.
        """
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

    def stop_playback(self):
        sd.stop()
        self.is_playing = False
        self.paused_time = 0.0
        self.seek_slider.set(0)  # Reset slider on stop
        self.play_pause_btn.configure(image=self.play_icon)

        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def on_seek(self, value):
        """
        Called when the user drags the slider.
        """
        if not self.controller.processing_results:
            return

        # 1. Calculate the new time based on slider value (0.0 to 1.0)
        results = self.controller.processing_results
        audio_data = results[self.current_audio_key]
        sample_rate = results["sample_rate"]
        duration = len(audio_data) / sample_rate

        new_time = value * duration
        self.paused_time = new_time

        # 2. Update the graph visuals immediately
        self._draw_graph_at(new_time)

        # 3. If currently playing, restart playback from the new position
        if self.is_playing:
            sd.stop()
            self.start_playback_stream()

    def _draw_graph_at(self, elapsed_time):
        """
        Helper function to draw the graph lines at a specific elapsed time.
        Used by both the animation loop and the scrubber.
        """
        if not self.graph_elements:
            return

        results = self.controller.processing_results
        noise_mag = results["noise_stft_mag_db"]

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

    def update_plot(self):
        results = self.controller.processing_results

        # Calculate current progress
        elapsed_time = self.paused_time + (time.time() - self.playback_start_time)

        audio_data = results[self.current_audio_key]
        sample_rate = results["sample_rate"]
        duration = len(audio_data) / sample_rate

        if elapsed_time < duration or self.current_audio_key == "noise_audio":
            # Update visuals
            self._draw_graph_at(elapsed_time)

            # Update Slider Position
            # We check if duration > 0 to avoid division by zero
            if duration > 0:
                self.seek_slider.set(elapsed_time / duration)

            self.animation_job = self.after(30, self.update_plot)
        else:
            self.stop_playback()
