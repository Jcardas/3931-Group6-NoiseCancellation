'''
This is the page where the user uploads an input audio file, and a noise file
'''
import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
from .theme import * # Import all theme constants
import os

class FileSelectionPage(ctk.CTkFrame):
    '''
    A frame that contains the UI for selecting input and noise audio files.
    '''
    def __init__(self, parent, controller):
        '''
        Initializes the file selection page.
        :param parent: The parent widget (the main app's container frame).
        :param controller: The main App instance, used to call back to for processing.
        '''
        super().__init__(parent, fg_color=COLOR_BACKGROUND)
        self.controller = controller

        # --- Row Frame for Cards ---
        row_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        row_frame.pack(pady=40, expand=True)

        # --- Input File Card ---
        self.input_card = ctk.CTkFrame(row_frame, width=250, height=250, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.input_card.pack(side="left", padx=20)
        self.input_card.pack_propagate(False)

        input_inner = ctk.CTkFrame(self.input_card, fg_color=COLOR_CARD_BACKGROUND)
        input_inner.pack(expand=True)
        
        img = PhotoImage(file="Assets/file.png")
        img_label = ctk.CTkLabel(input_inner, image=img, text="")
        img_label.image = img
        img_label.pack(pady=10)

        self.input_label = ctk.CTkLabel(input_inner, text="Input Audio File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=18))
        self.input_label.pack(pady=10)

        ctk.CTkButton(self.input_card, text="Select File", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=lambda: self._select_file("input")).pack(side="bottom", pady=10)

        # --- Noise File Card ---
        self.noise_card = ctk.CTkFrame(row_frame, width=250, height=250, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.noise_card.pack(side="left", padx=20)
        self.noise_card.pack_propagate(False)

        noise_inner = ctk.CTkFrame(self.noise_card, fg_color=COLOR_CARD_BACKGROUND)
        noise_inner.pack(expand=True)
        
        img_label2 = ctk.CTkLabel(noise_inner, image=img, text="")
        img_label2.image = img
        img_label2.pack(pady=10)

        self.noise_label = ctk.CTkLabel(noise_inner, text="Noise Sample File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=18))
        self.noise_label.pack(pady=10)

        ctk.CTkButton(self.noise_card, text="Select Noise", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=lambda: self._select_file("noise")).pack(side="bottom", pady=10)

        # --- Process Button Frame ---
        bottom_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        bottom_frame.pack(pady=20, side="bottom")

        ctk.CTkButton(bottom_frame, text="Cancel Noise", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=self._process_files).pack()

    def _select_file(self, file_type):
        '''
        Handles the file selection and updates the UI.
        '''
        title_map = {"input": "Select Input Audio (.wav)", "noise": "Select Noise Sample (.wav)"}
        label_map = {"input": self.input_label, "noise": self.noise_label}
        card_map = {"input": self.input_card, "noise": self.noise_card}
        
        file = filedialog.askopenfilename(title=title_map[file_type], filetypes=[("Audio Files", "*.wav")])
        if file:
            if file_type == "input":
                self.controller.input_file = file
            else:
                self.controller.noise_file = file
            
            label_map[file_type].configure(text=os.path.basename(file))
            card_map[file_type].configure(border_color=COLOR_BUTTON)
            messagebox.showinfo("Selected", f"{title_map[file_type].split('(')[0].strip()}: {os.path.basename(file)}")

    def _process_files(self):
        '''
        Validates files and calls the main controller to start processing.
        '''
        if not self.controller.input_file:
            messagebox.showerror("Error", "Please select an input audio file.")
            return
        if not self.controller.noise_file:
            messagebox.showerror("Error", "Please select a noise sample file.")
            return
        
        # Call the process method on the main App controller
        self.controller.process_files()