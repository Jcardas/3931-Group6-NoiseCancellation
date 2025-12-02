"""
This is the main app window for the Noise Canceller.
This class will instantiate the other UI pages as needed.
"""

import customtkinter as ctk
from tkinter import messagebox
from scipy.io import wavfile
import functionality.processing as processing

import sys
import sounddevice as sd

# Import the pages
from ui.file_selection_page import FileSelectionPage
from ui.output_editor_page import OutputEditorPage
from ui.theme import COLOR_BACKGROUND


# --- Main Application Class ---
class App(ctk.CTk):
    """
    The main application class for the Noise Canceller GUI.
    It encapsulates all UI elements and application logic.
    This class is the CONTROLLER. It manages which view (page) is currently active.
    """

    def __init__(self):
        """
        Initializes the main application window and its components.
        """
        super().__init__()

        # --- Window Setup ---
        self.title("Noise Canceller")
        self.geometry("1200x720")
        self.minsize(1200, 720)
        ctk.set_appearance_mode("light")
        self.configure(fg_color=COLOR_BACKGROUND)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- State Variables ---
        # These variables will store the paths to the selected audio files.
        self.input_file = None
        self.noise_file = None
        self.output_file = None
        self.processing_results = None  # Will hold the dict from processing
        self.current_page_class = FileSelectionPage

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

    def on_closing(self):
        """
        Handles cleanup when the application window is closed.
        """
        sd.stop()
        self.quit()
        self.destroy()
        sys.exit()

    def show_page(self, page_class):
        """
        Raises the specified page to the top of the view.
        :param page_class: The class of the page to show.
        """
        # If leaving the OutputEditorPage, prompt to save if there are unsaved changes
        if (
            self.current_page_class == OutputEditorPage
            and page_class != OutputEditorPage
            and self.processing_results
        ):

            response = messagebox.askyesno(
                "Save Changes", "Do you want to save the cleaned audio before leaving?"
            )

            if response:
                self.save_files(alert_on_success=True)

        page = self.pages[page_class]
        self.current_page_class = page_class
        # If the page has an 'on_show' method, call it.
        if hasattr(page, "on_show"):
            page.on_show()

        page.tkraise()

    def process_files(self, M=256, alpha=1.05, beta=0.001):
        """
        Validates that both files have been selected and calls the processing function.
        Displays success or error messages to the user.
        This method is called FROM the FileSelectionPage.
        """
        # --- Call Processing Logic ---
        try:
            # Pass the file paths and parameters to the backend processing function
            results = processing.cancel_noise(
                input_path=self.input_file,
                noise_path=self.noise_file,
                M=M,
                alpha=alpha,
                beta=beta,
            )
            # Store the results in the controller
            self.processing_results = results

            self.show_page(OutputEditorPage)

        except Exception as e:
            # Show a detailed error message if something goes wrong
            messagebox.showerror("Processing Error", str(e))

    def save_files(self, alert_on_success=True):
        """
        Saves the processed output file to the user's Downloads folder.
        This method is called FROM the OutputEditorPage.
        """
        try:
            output_path = self.processing_results["output_path"]
            sample_rate = self.processing_results["sample_rate"]

            # Read the cleaned audio data
            cleaned_data_int = self.processing_results["cleaned_data_int_final"]

            # Save to Downloads folder
            wavfile.write(output_path, sample_rate, cleaned_data_int)

            if alert_on_success:
                # Show success message with the output file path
                messagebox.showinfo(
                    "Success",
                    f"Noise cancelled!\nSaved to: {self.processing_results['output_path']}",
                )
            self.processing_results = None  # Clear results after saving
        except Exception as e:
            # Show error message if saving fails
            messagebox.showerror("Save Error", str(e))
