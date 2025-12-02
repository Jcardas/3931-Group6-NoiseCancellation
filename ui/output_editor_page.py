"""
This is the page where the user can view and play back the processed
audio file.

The processed audio is displayed in frequency domain using matplotlib
"""

import customtkinter as ctk
from tkinter import PhotoImage, messagebox
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

        # --- Left Panel: Audio Players & Settings ---
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

        # --- Filter Settings Frame ---
        self.settings_frame = ctk.CTkFrame(
            left_panel,
            fg_color=COLOR_CARD_BACKGROUND,
            border_width=2,
            border_color=COLOR_CARD_BACKGROUND,
        )
        self.settings_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(
            self.settings_frame,
            text="Filter Settings",
            font=("Arial", 14, "bold"),
            text_color=COLOR_TEXT,
        ).pack(pady=(10, 5))

        # Grid for inputs
        input_grid = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        input_grid.pack(pady=5, padx=10)

        # M Input
        ctk.CTkLabel(
            input_grid, text="M (Size):", text_color=COLOR_TEXT, width=60, anchor="w"
        ).grid(row=0, column=0, padx=5, pady=2)
        self.m_entry = ctk.CTkEntry(
            input_grid, width=60, fg_color=COLOR_BACKGROUND, text_color=COLOR_TEXT
        )
        self.m_entry.grid(row=0, column=1, padx=5, pady=2)

        # Alpha Input
        ctk.CTkLabel(
            input_grid,
            text="Alpha (Over-subtraction):",
            text_color=COLOR_TEXT,
            width=60,
            anchor="w",
        ).grid(row=1, column=0, padx=5, pady=2)
        self.alpha_entry = ctk.CTkEntry(
            input_grid, width=60, fg_color=COLOR_BACKGROUND, text_color=COLOR_TEXT
        )
        self.alpha_entry.grid(row=1, column=1, padx=5, pady=2)

        # Beta Input
        ctk.CTkLabel(
            input_grid,
            text="Beta (Flooring Factor):",
            text_color=COLOR_TEXT,
            width=60,
            anchor="w",
        ).grid(row=2, column=0, padx=5, pady=2)
        self.beta_entry = ctk.CTkEntry(
            input_grid, width=60, fg_color=COLOR_BACKGROUND, text_color=COLOR_TEXT
        )
        self.beta_entry.grid(row=2, column=1, padx=5, pady=2)

        # Update Button
        self.update_btn = ctk.CTkButton(
            self.settings_frame,
            text="Update Filter",
            fg_color=COLOR_ALT_GRAPH,  # Use a distinct color for action
            hover_color="#E02E2E",
            height=30,
            command=self.update_filter,
        )
        self.update_btn.pack(pady=10, padx=10, fill="x")

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
        self.save_button.pack(pady=10, side="bottom")

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
            height=80,  # Made slightly smaller to fit settings
            border_width=2,
            border_color=COLOR_CARD_BACKGROUND,
        )
        card.pack(pady=5, padx=5)
        card.pack_propagate(False)

        self.audio_cards[key] = card

        def on_click(event):
            self.select_audio(key)

        card.bind("<Button-1>", on_click)

        icon_label = ctk.CTkLabel(card, image=self.file_icon, text="")
        icon_label.pack(side="left", padx=10, anchor="center")
        icon_label.bind("<Button-1>", on_click)

        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, pady=10)
        text_frame.bind("<Button-1>", on_click)

        title_lbl = ctk.CTkLabel(
            text_frame, text=title, text_color="gray", font=("Arial", 12)
        )
        title_lbl.pack(anchor="w")
        title_lbl.bind("<Button-1>", on_click)

        name_label = ctk.CTkLabel(
            text_frame, text="...", text_color=COLOR_TEXT, font=("Arial", 14, "bold")
        )
        name_label.pack(anchor="w")
        name_label.bind("<Button-1>", on_click)
        self.name_labels[key] = name_label

    def select_audio(self, key):
        """Selects the audio source for playback and visualization."""
        if self.current_audio_key == key:
            return

        self.current_audio_key = key

        for k, card in self.audio_cards.items():
            if k == key:
                card.configure(border_color=COLOR_BUTTON)
            else:
                card.configure(border_color=COLOR_CARD_BACKGROUND)

        self._draw_graph_at(self.paused_time)

        if self.is_playing:
            sd.stop()
            self.start_playback_stream()

    def go_back(self):
        self.stop_playback()
        self.controller.unbind("<space>")
        self.controller.show_page(FileSelectionPage)

    def update_filter(self):
        """
        Reads values from inputs and re-runs the processing.
        """
        try:
            M = int(self.m_entry.get())
            alpha = float(self.alpha_entry.get())
            beta = float(self.beta_entry.get())

            if M <= 0 or alpha < 0 or beta < 0:
                raise ValueError("Values must be positive.")
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please check your filter settings.\nM must be an integer, Alpha/Beta must be numbers.",
            )
            return

        # Stop playback before updating
        self.stop_playback()

        # Trigger processing in the controller
        # This will recalculate and call on_show again to refresh the UI
        self.controller.process_files(M=M, alpha=alpha, beta=beta)

    def on_show(self):
        self.stop_playback()
        self.seek_slider.set(0)
        self.controller.bind("<space>", lambda event: self.toggle_playback())

        if self.controller.processing_results:
            res = self.controller.processing_results

            # Update labels
            self.name_labels["original_audio"].configure(
                text=os.path.basename(self.controller.input_file)
            )
            self.name_labels["noise_audio"].configure(
                text=os.path.basename(self.controller.noise_file)
            )
            self.name_labels["cleaned_audio"].configure(
                text=os.path.basename(res["output_path"])
            )

            # --- Fill Filter Settings from Results ---
            # This keeps the UI in sync with the actual data used
            params = res.get("parameters", {"M": 256, "alpha": 1.05, "beta": 0.001})

            self.m_entry.delete(0, "end")
            self.m_entry.insert(0, str(params["M"]))

            self.alpha_entry.delete(0, "end")
            self.alpha_entry.insert(0, str(params["alpha"]))

            self.beta_entry.delete(0, "end")
            self.beta_entry.insert(0, str(params["beta"]))

            # Default selection
            self.current_audio_key = "cleaned_audio"
            self.select_audio("cleaned_audio")

            # Re-init graph
            if self.graph_elements:
                self.graph_elements["canvas_widget"].destroy()

            self.graph_elements = create_live_freq_domain_graphs(
                self.graph_frame, res["stft_freq"]
            )
            self.graph_elements["canvas_widget"].pack(expand=True, fill="both")

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
        if not self.controller.processing_results:
            return

        if self.is_playing:
            self.paused_time += time.time() - self.playback_start_time
            sd.stop()
            self.is_playing = False
            if self.animation_job:
                self.after_cancel(self.animation_job)
                self.animation_job = None
            self.play_pause_btn.configure(image=self.play_icon)
        else:
            self.start_playback_stream()
            self.is_playing = True
            self.play_pause_btn.configure(image=self.pause_icon)
            self.update_plot()

    def start_playback_stream(self):
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
        self.seek_slider.set(0)
        self.play_pause_btn.configure(image=self.play_icon)

        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def on_seek(self, value):
        if not self.controller.processing_results:
            return
        results = self.controller.processing_results
        audio_data = results[self.current_audio_key]
        sample_rate = results["sample_rate"]
        duration = len(audio_data) / sample_rate
        new_time = value * duration
        self.paused_time = new_time
        self._draw_graph_at(new_time)
        if self.is_playing:
            sd.stop()
            self.start_playback_stream()

    def _draw_graph_at(self, elapsed_time):
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
        elapsed_time = self.paused_time + (time.time() - self.playback_start_time)
        audio_data = results[self.current_audio_key]
        sample_rate = results["sample_rate"]
        duration = len(audio_data) / sample_rate

        if elapsed_time < duration or self.current_audio_key == "noise_audio":
            self._draw_graph_at(elapsed_time)
            if duration > 0:
                self.seek_slider.set(elapsed_time / duration)
            self.animation_job = self.after(30, self.update_plot)
        else:
            self.stop_playback()
