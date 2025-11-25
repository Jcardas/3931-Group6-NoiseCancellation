'''
This is the page where the user can view and modify the output (cleaned)
audio file. 

The processed audio is displayed in frequency domain using matplotlib

It should have sliders to affect the strength and location of the filter.
'''

import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
from .theme import *  # Import all theme constants
from ui.file_selection_page import FileSelectionPage
from functionality.graphing import create_freq_domain_graph


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
        self.graph_widget = None # To hold a reference to the graph

        # Separate each section into a row to build the ui

        # --- Back button ---
        def button_event():
            self.controller.show_page(FileSelectionPage)

        backButton = ctk.CTkButton(self, text='<-', width=30, height=30, hover_color=COLOR_BUTTON_HOVER, command=button_event)
        backButton.place(x=10, y=10)

        # --- Row Frame holds the card and graph ---
        row_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        row_frame.pack(pady=40, expand=True)

        # --- Output File Card ---
        self.input_card = ctk.CTkFrame(row_frame, width=150, height=150, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.input_card.pack(side="left", padx=20)
        self.input_card.pack_propagate(False)

        input_inner = ctk.CTkFrame(self.input_card, fg_color=COLOR_CARD_BACKGROUND)
        input_inner.pack(expand=True)

        img = PhotoImage(file="Assets/file.png")
        img_label = ctk.CTkLabel(input_inner, image=img, text="")
        img_label.image = img
        img_label.pack(pady=10)

        self.input_label = ctk.CTkLabel(input_inner, text="Output Audio File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=16))
        self.input_label.pack(pady=10)

        # --- Graph Frame ---
        # This frame will hold the graph widget
        self.graph_frame = ctk.CTkFrame(row_frame, fg_color=COLOR_BACKGROUND)
        self.graph_frame.pack(side="left", padx=20, expand=True, fill="both")

    def on_show(self):
        '''
        Called when the page is raised to the top.
        Generates and displays the graph.
        '''
        # Destroy the old graph widget if it exists
        if self.graph_widget:
            self.graph_widget.destroy()

        if self.controller.output_file:
            # Call the function from graphing.py to create the graph
            self.graph_widget = create_freq_domain_graph(self.graph_frame, self.controller.output_file)
            self.graph_widget.pack(expand=True, fill="both")
