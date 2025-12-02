"""
This is the page where the user can view and modify the output (cleaned)
audio file.

The processed audio is displayed in frequency domain using matplotlib
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
import time
import numpy as np
import sounddevice as sd
import os
from .theme import *  # Import all theme constants
from ui.file_selection_page import FileSelectionPage
from functionality.graphing import create_live_freq_domain_graphs


class OutputEditorPage(ctk.CTkFrame):
    """
    A frame that contains the UI for the output of the noise
    cancellation.
    """

    def __init__(self, parent, controller):
        """
        Initializes the page.

        :param parent: The parent widget (the main app's container frame).
        :param controller: The main App instance, used to call back to for processing.
        """

        super().__init__(parent, fg_color=COLOR_BACKGROUND)

        sd.default.latency = "high"  # Set higher latency for more stable playback
        sd.default.blocksize = 2048  # Set blocksize for lower CPU usage

        self.controller = controller
        self.graph_elements = (
            None  # To hold a reference to the graph and its components
        )
        self.animation_job = None
        self.playback_start_time = 0.0
        self.paused_time = 0.0
        self.is_playing = False

        # Separate each section into a row to build the ui

        # --- Back button ---
        def button_event():
            self.controller.show_page(FileSelectionPage)

        backButton = ctk.CTkButton(
            self,
            text="<-",
            width=30,
            height=30,
            hover_color=COLOR_BUTTON_HOVER,
            command=button_event,
        )
        backButton.place(x=10, y=10)

        # --- Row Frame holds the card, controls, and graph ---
        row_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        row_frame.pack(pady=40, expand=True)

        # --- Left Panel Frame (Card + Controls) ---
        left_panel = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        left_panel.pack(side="left", padx=20, expand=True, fill="both")

        # A new frame to group the card and controls, which we can then center
        center_group = ctk.CTkFrame(left_panel, fg_color=COLOR_BACKGROUND)
        center_group.pack(expand=True)  # This centers the group in the left_panel

        # --- Output File Card ---
        self.input_card = ctk.CTkFrame(
            center_group,
            width=150,
            height=150,
            fg_color=COLOR_CARD_BACKGROUND,
            border_width=2,
            border_color=COLOR_CARD_BACKGROUND,
        )
        self.input_card.pack(side="top")
        self.input_card.pack_propagate(False)

        input_inner = ctk.CTkFrame(self.input_card, fg_color=COLOR_CARD_BACKGROUND)
        input_inner.pack(expand=True)

        self.file_icon = PhotoImage(file="Assets/file.png")
        img_label = ctk.CTkLabel(input_inner, image=self.file_icon, text="")
        img_label.pack(pady=10)

        self.input_label = ctk.CTkLabel(
            input_inner,
            text="Output Audio File",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(size=12),
        )
        self.input_label.pack(pady=10)

        # --- Controls Frame ---
        controls_frame = ctk.CTkFrame(center_group, fg_color=COLOR_BACKGROUND)
        controls_frame.pack(side="top", pady=10)

        # Load icons
        self.play_icon = PhotoImage(file="Assets/play.png").subsample(2, 2)
        self.pause_icon = PhotoImage(file="Assets/pause.png").subsample(2, 2)
        self.restart_icon = PhotoImage(file="Assets/restart.png").subsample(2, 2)

        self.play_pause_button = ctk.CTkButton(
            controls_frame,
            image=self.play_icon,
            text="",
            width=20,
            command=self.toggle_playback,
        )
        self.play_pause_button.pack(side="left", padx=5)

        restart_button = ctk.CTkButton(
            controls_frame,
            image=self.restart_icon,
            text="",
            width=20,
            command=self.stop_playback,
        )
        restart_button.pack(side="left", padx=5)

        # --- Graph Frame ---
        # This frame will hold the graph widget
        self.graph_frame = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        self.graph_frame.pack(side="left", padx=20, expand=True, fill="both")

    def on_show(self):
        self.stop_playback()
        if self.graph_elements:
            self.graph_elements["canvas_widget"].destroy()

        if self.controller.processing_results:
            self.input_label.configure(
                text=os.path.basename(self.controller.processing_results["output_path"])
            )

            self.graph_elements = create_live_freq_domain_graphs(
                self.graph_frame, self.controller.processing_results["stft_freq"]
            )
            self.graph_elements["canvas_widget"].pack(expand=True, fill="both")

            # This forces lines to cut off exactly at the axis border, so they can't smear the text.
            for key in ["line1", "line2", "line3"]:
                self.graph_elements[key].set_animated(True)
                self.graph_elements[key].set_clip_on(True)

            self.bg_cache = None
            canvas = self.graph_elements["canvas"]

            # If the window resizes, we MUST invalidate the cache, or it will glitch.
            def on_resize(event):
                self.bg_cache = None

            # Bind the resize event to the canvas widget
            canvas.get_tk_widget().bind("<Configure>", on_resize)

            # Initial draw
            canvas.draw()
            # Cache only the plot area (ax.bbox), which is safer than the whole figure
            self.bg_cache = canvas.copy_from_bbox(self.graph_elements["ax"].bbox)

    def toggle_playback(self):
        if not self.controller.processing_results:
            return

        if self.is_playing:
            # --- Pause Logic ---
            self.paused_time += time.time() - self.playback_start_time
            sd.stop()
            self.is_playing = False
            if self.animation_job:
                self.after_cancel(self.animation_job)
                self.animation_job = None
            self.play_pause_button.configure(image=self.play_icon)
        else:
            # --- Play/Resume Logic ---
            results = self.controller.processing_results
            sample_rate = results["sample_rate"]
            audio_data = results["cleaned_audio"]

            # Calculate the starting sample based on paused time
            start_sample = int(self.paused_time * sample_rate)

            if start_sample >= len(audio_data):  # If at the end, reset
                self.paused_time = 0
                start_sample = 0

            # Ensures data is contiguous in memory for sounddevice before playing
            data_toplay = np.ascontiguousarray(audio_data[start_sample:])
            sd.play(data_toplay, sample_rate)

            self.playback_start_time = time.time()
            self.is_playing = True
            self.play_pause_button.configure(image=self.pause_icon)
            self.update_plot()

    def stop_playback(self):
        sd.stop()
        self.is_playing = False
        self.paused_time = 0.0
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.play_pause_button.configure(image=self.play_icon)

    def update_plot(self):
        results = self.controller.processing_results
        elapsed_time = self.paused_time + (time.time() - self.playback_start_time)

        time_vector = results["stft_time"]
        time_index = np.searchsorted(time_vector, elapsed_time)

        if time_index < len(time_vector):
            original_mag = results["original_stft_mag_db"][:, time_index]
            cleaned_mag = results["cleaned_stft_mag_db"][:, time_index]
            noise_mag = results["noise_stft_mag_db"]

            self.graph_elements["line1"].set_ydata(original_mag)
            self.graph_elements["line2"].set_ydata(cleaned_mag)
            self.graph_elements["line3"].set_ydata(noise_mag)

            canvas = self.graph_elements["canvas"]
            ax = self.graph_elements["ax"]

            # --- FIX 3: Robust Blitting Logic ---
            if self.bg_cache is None:
                # If cache is missing (due to resize), redraw everything once to rebuild it
                canvas.draw()
                self.bg_cache = canvas.copy_from_bbox(ax.bbox)
            else:
                # 1. Restore the white background inside the axes
                canvas.restore_region(self.bg_cache)

                # 2. Draw the lines (now clipped safely inside)
                ax.draw_artist(self.graph_elements["line1"])
                ax.draw_artist(self.graph_elements["line2"])
                ax.draw_artist(self.graph_elements["line3"])

                # 3. Blit ONLY the axes box (fastest method)
                canvas.blit(ax.bbox)

            self.animation_job = self.after(30, self.update_plot)
        else:
            self.stop_playback()
