'''
CustomTkinter GUI for the Noise Canceller application.

This module provides a modern, user-friendly interface for the noise cancellation
tool. It allows users to select an input audio file and a noise sample,
and then process them to remove background noise.
'''

import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
import functionality.processing as processing
import os

# --- Constants ---
COLOR_BUTTON = "#4A90E2"
COLOR_BUTTON_HOVER = "#7CAEE6"
COLOR_BACKGROUND = "#E3E3E3"
COLOR_CARD_BACKGROUND = "#FFFFFF"
COLOR_TEXT = "#000000"


# --- Main Application Class ---
class NoiseCancellerApp(ctk.CTk):
    '''
    The main application class for the Noise Canceller GUI.
    It encapsulates all UI elements and application logic.
    '''
    def __init__(self):
        '''
        Initializes the main application window and its components.
        '''
        super().__init__()

        # --- Window Setup ---
        self.title("Noise Canceller (CTk Version)")
        self.geometry("650x520")
        ctk.set_appearance_mode("light")
        self.configure(fg_color=COLOR_BACKGROUND)

        # --- State Variables ---
        # These variables will store the paths to the selected audio files.
        self.input_file = None
        self.noise_file = None

        # --- Build UI ---
        # This method creates and arranges all the widgets in the window.
        self._build_ui()

    def _build_ui(self):
        '''
        Constructs the user interface by creating and placing all widgets.
        '''
        # --- Main Container Frame ---
        # This frame acts as the main background and holds all other UI elements.
        main_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        main_frame.pack(expand=True, fill="both")

        # --- Row Frame for Cards ---
        # This frame holds the input and noise selection cards side-by-side.
        row_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BACKGROUND)
        row_frame.pack(pady=40)

        # --- Input File Card ---
        # A card for selecting the primary audio file to be processed.
        self.input_card = ctk.CTkFrame(row_frame, width=250, height=250, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.input_card.pack(side="left", padx=20)
        self.input_card.pack_propagate(False)  # Prevent card from resizing to fit content

        input_inner = ctk.CTkFrame(self.input_card, fg_color=COLOR_CARD_BACKGROUND)
        input_inner.pack(expand=True)
        
        # Load and display the upload icon
        img = PhotoImage(file="Assets/file.png")
        img_label = ctk.CTkLabel(input_inner, image=img, text="")
        img_label.image = img  # Keep a reference to prevent garbage collection
        img_label.pack(pady=10)

        # Label to display the selected file name
        self.input_label = ctk.CTkLabel(input_inner, text="Input Audio File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=18))
        self.input_label.pack(pady=10)

        # Button to open the file selection dialog
        ctk.CTkButton(self.input_card, text="Select File", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=lambda: self._select_file("input")).pack(side="bottom", pady=10)

        # --- Noise File Card ---
        # A card for selecting the noise sample audio file.
        self.noise_card = ctk.CTkFrame(row_frame, width=250, height=250, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.noise_card.pack(side="left", padx=20)
        self.noise_card.pack_propagate(False)  # Prevent card from resizing

        noise_inner = ctk.CTkFrame(self.noise_card, fg_color=COLOR_CARD_BACKGROUND)
        noise_inner.pack(expand=True)
        
        # Display the same upload icon
        img_label2 = ctk.CTkLabel(noise_inner, image=img, text="")
        img_label2.image = img  # Keep a reference
        img_label2.pack(pady=10)

        # Label to display the selected noise file name
        self.noise_label = ctk.CTkLabel(noise_inner, text="Noise Sample File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=18))
        self.noise_label.pack(pady=10)

        # Button to open the file selection dialog
        ctk.CTkButton(self.noise_card, text="Select Noise", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=lambda: self._select_file("noise")).pack(side="bottom", pady=10)

        # --- Process Button Frame ---
        # A separate frame at the bottom to hold the main action button.
        bottom_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BACKGROUND)
        bottom_frame.pack(pady=20)

        # The button that triggers the noise cancellation process
        ctk.CTkButton(bottom_frame, text="Cancel Noise", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=self._process_files).pack()
                    # self._process_files is defined below ↓

    # --- Event Handlers ---
    
    def _select_file(self, file_type):
        '''
        Handles the file selection for either input audio or noise sample.
        :param file_type: A string, either "input" or "noise", to determine which file is being selected.
        '''
        title_map = {
            "input": "Select Input Audio (.wav)",
            "noise": "Select Noise Sample (.wav)"
        }
        label_map = {
            "input": self.input_label,
            "noise": self.noise_label
        }
        card_map = {
            "input": self.input_card,
            "noise": self.noise_card
        }
        
        file = filedialog.askopenfilename(title=title_map[file_type], filetypes=[("Audio Files", "*.wav")])
        if file:
            if file_type == "input":
                self.input_file = file
            else: # file_type == "noise"
                self.noise_file = file
            
            label_map[file_type].configure(text=os.path.basename(file))
            card_map[file_type].configure(border_color=COLOR_BUTTON)
            messagebox.showinfo("Selected", f"{title_map[file_type].split('(')[0].strip()}: {os.path.basename(file)}")

    def _process_files(self):
        '''
        Validates that both files have been selected and calls the processing function.
        Displays success or error messages to the user.
        '''
        # --- Input Validation ---
        if not self.input_file:
            messagebox.showerror("Error", "Please select an input audio file.")
            return
        if not self.noise_file:
            messagebox.showerror("Error", "Please select a noise sample file.")
            return

        # --- Call Processing Logic ---
        try:
            # Pass the file paths to the backend processing function
            output_path = processing.cancel_noise(
                # This calls to processing.py cancel_noise() which returns the path to where the output is saved.
                # It passes in the input wav file, and the input noise file.
                input_path=self.input_file,
                noise_path=self.noise_file
            )
            # Show success message with the output file path
            messagebox.showinfo("Success", f"Noise cancelled!\nSaved to: {output_path}")
        except Exception as e:
            # Show a detailed error message if something goes wrong
            messagebox.showerror("Processing Error", str(e))


# --- Main Execution Block ---
if __name__ == "__main__":
    # This block runs when the script is executed directly.
    app = NoiseCancellerApp()
    app.mainloop()