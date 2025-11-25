'''
This is the page where the user can view and modify the output (cleaned)
audio file. 

The processed audio is displayed in frequency domain using matplotlib

It should have sliders to affect the strength and location of the filter.
'''

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
    '''
    A frame that contains the UI for the output of the noise
    cancellation.
    '''
    def __init__(self, parent, controller):
        '''
        Initializes the page.

        :param parent: The parent widget (the main app's container frame).
        :param controller: The main App instance, used to call back to for processing.
        '''

        super().__init__(parent, fg_color=COLOR_BACKGROUND)
        self.controller = controller
        self.graph_elements = None # To hold a reference to the graph and its components
        self.animation_job = None
        self.playback_start_time = 0.0
        self.paused_time = 0.0
        self.is_playing = False

        # Separate each section into a row to build the ui

        # --- Back button ---
        def button_event():
            self.controller.show_page(FileSelectionPage)

        backButton = ctk.CTkButton(self, text='<-', width=30, height=30, hover_color=COLOR_BUTTON_HOVER, command=button_event)
        backButton.place(x=10, y=10)

        # --- Row Frame holds the card, controls, and graph ---
        row_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        row_frame.pack(pady=40, expand=True)
        
        # --- Left Panel Frame (Card + Controls) ---
        left_panel = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        left_panel.pack(side="left", padx=20, expand=True, fill="both")

        # A new frame to group the card and controls, which we can then center
        center_group = ctk.CTkFrame(left_panel, fg_color=COLOR_BACKGROUND)
        center_group.pack(expand=True) # This centers the group in the left_panel

        # --- Output File Card ---
        self.input_card = ctk.CTkFrame(center_group, width=150, height=150, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.input_card.pack(side="top")
        self.input_card.pack_propagate(False)

        input_inner = ctk.CTkFrame(self.input_card, fg_color=COLOR_CARD_BACKGROUND)
        input_inner.pack(expand=True)

        self.file_icon = PhotoImage(file="Assets/file.png")
        img_label = ctk.CTkLabel(input_inner, image=self.file_icon, text="")
        img_label.pack(pady=10)

        self.input_label = ctk.CTkLabel(input_inner, text="Output Audio File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.input_label.pack(pady=10)

        # --- Controls Frame ---
        controls_frame = ctk.CTkFrame(center_group, fg_color=COLOR_BACKGROUND)
        controls_frame.pack(side="top", pady=10)

        # Load icons
        self.play_icon = PhotoImage(file="Assets/play.png").subsample(2, 2) 
        self.pause_icon = PhotoImage(file="Assets/pause.png").subsample(2, 2)
        self.restart_icon = PhotoImage(file="Assets/restart.png").subsample(2, 2)

        self.play_pause_button = ctk.CTkButton(controls_frame, image=self.play_icon, text="", width=20,
                                    command=self.toggle_playback)
        self.play_pause_button.pack(side="left", padx=5)
        
        restart_button = ctk.CTkButton(controls_frame, image=self.restart_icon, text="", width=20, 
                                    command=self.stop_playback)
        restart_button.pack(side="left", padx=5)

        # --- Graph Frame ---
        # This frame will hold the graph widget
        self.graph_frame = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        self.graph_frame.pack(side="left", padx=20, expand=True, fill="both")

    def on_show(self):
        '''
        Called when the page is raised to the top.
        Generates and displays the graph.
        '''
        self.stop_playback() # Stop any previous playback
        # Destroy the old graph widget if it exists
        if self.graph_elements:
            self.graph_elements["canvas_widget"].destroy()

        if self.controller.processing_results:
            # Update the card title with the output file name
            self.input_label.configure(text=os.path.basename(self.controller.processing_results["output_path"]))

            # Call the function from graphing.py to create the graph
            self.graph_elements = create_live_freq_domain_graphs(self.graph_frame, self.controller.processing_results["stft_freq"])
            self.graph_elements["canvas_widget"].pack(expand=True, fill="both")

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

            if start_sample >= len(audio_data): # If at the end, reset
                self.paused_time = 0
                start_sample = 0

            # Play the audio from the correct sample
            sd.play(audio_data[start_sample:], sample_rate)

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
        # Total elapsed time is the paused time plus the current playing time
        elapsed_time = self.paused_time + (time.time() - self.playback_start_time)

        # Find the closest time index in the STFT data
        time_vector = results["stft_time"]
        time_index = np.searchsorted(time_vector, elapsed_time)

        if time_index < len(time_vector):
            # Get the frequency data for this time slice
            original_mag = results["original_stft_mag_db"][:, time_index]
            cleaned_mag = results["cleaned_stft_mag_db"][:, time_index]
            noise_mag = results["noise_stft_mag_db"] # Noise profile is constant over time


            # Update the plot lines
            self.graph_elements["line1"].set_ydata(original_mag)
            self.graph_elements["line2"].set_ydata(cleaned_mag)
            self.graph_elements["line3"].set_ydata(noise_mag)


            # Redraw the canvas
            self.graph_elements["canvas"].draw()

            # Schedule the next update
            self.animation_job = self.after(30, self.update_plot) # ~33 FPS
        else:
            self.stop_playback() # Audio finished, so reset
