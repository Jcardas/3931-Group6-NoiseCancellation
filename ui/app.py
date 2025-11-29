'''
This is the main app window for the Noise Canceller.
This class will instantiate the other UI pages as needed.
'''

import customtkinter as ctk
from tkinter import messagebox
import functionality.processing as processing

# Import the pages
from ui.file_selection_page import FileSelectionPage
from ui.output_editor_page import OutputEditorPage
from ui.theme import COLOR_BACKGROUND

# --- Main Application Class ---
class App(ctk.CTk):
    '''
    The main application class for the Noise Canceller GUI.
    It encapsulates all UI elements and application logic.
    This class is the CONTROLLER. It manages which view (page) is currently active.
    '''
    def __init__(self):
        '''
        Initializes the main application window and its components.
        '''
        super().__init__()

        # --- Window Setup ---
        self.title("Noise Canceller")
        self.geometry("750x520")
        ctk.set_appearance_mode("light")
        self.configure(fg_color=COLOR_BACKGROUND)

        # --- State Variables ---
        # These variables will store the paths to the selected audio files.
        self.input_file = None
        self.noise_file = None
        self.output_file = None
        self.processing_results = None # Will hold the dict from processing

        # --- Container for Pages ---
        # This frame will hold the different pages of the application.
        container = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # --- Dictionary to hold the pages ---
        self.pages = {}

        # Create an instance of the file selection page
        page = FileSelectionPage(parent=container, controller=self)
        self.pages[FileSelectionPage] = page
        page.grid(row=0, column=0, sticky="nsew")

        # Create an instance of the output editor page
        page = OutputEditorPage(parent=container, controller=self)
        self.pages[OutputEditorPage] = page
        page.grid(row=0, column=0, sticky="nsew")

        # --- Show the initial page ---
        self.show_page(FileSelectionPage)

    def show_page(self, page_class):
        '''
        Raises the specified page to the top of the view.
        :param page_class: The class of the page to show.
        '''
        page = self.pages[page_class]
        # If the page has an 'on_show' method, call it.
        if hasattr(page, "on_show"):
            page.on_show()

        page.tkraise()

    def process_files(self, use_highpass=False):
        '''
        Validates that both files have been selected and calls the processing function.
        Displays success or error messages to the user.
        This method is called FROM the FileSelectionPage.
        '''
        # --- Call Processing Logic ---
        try:
            # Pass the file paths to the backend processing function
            results = processing.cancel_noise(
                input_path=self.input_file,
                noise_path=self.noise_file,
                use_highpass=use_highpass
            )
            # Store the results in the controller
            self.processing_results = results

            # Show success message with the output file path
            messagebox.showinfo("Success", f"Noise cancelled!\nSaved to: {self.processing_results["output_path"]}")

            self.show_page(OutputEditorPage)


        except Exception as e:
            # Show a detailed error message if something goes wrong
            messagebox.showerror("Processing Error", str(e))
