'''
Contains the GUI (tKinter) code.

Responsibilities:
  - Layout and styling of the application window
  - Handling user interaction (buttons, file dialogs)
  - Calling functions in processing.py to do the actual audio work
'''
import tkinter as tk
from tkinter import filedialog, messagebox
from tkmacosx import Button as macButton # For better button styling on macOS

# This helps determine what operating system we're on
from sys import platform

if platform == "darwin":  # macOS
    Button = macButton
else:
    Button = tk.Button
    


import processing

# Color palette
COLOR_BUTTON = "#4A90E2"  # Blue for buttons/active states
COLOR_BUTTON2 = "#1EB73F"  # Darker blue for hover/active
COLOR_BACKGROUND = "#EFEFEF"  # Light grey background
COLOR_CARD_BACKGROUND = "#FFFFFF"  # White for boxes
COLOR_TEXT = "#000000"  # Black text


class NoiseCancellerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Noise Canceller")
        self.root.geometry("600x500")  # Adjusted size
        self.root.resizable(True, True)
        self.root.minsize(600, 500)
        self.root.configure(bg=COLOR_BACKGROUND)

        self.input_file = None
        self.noise_file = None
        
        self._build_ui()
        
        
    
    def _build_ui(self):
        main_frame = tk.Frame(self.root, bg=COLOR_BACKGROUND)
        main_frame.pack(expand=True)
      
      # Image for the upload icons
        self.upload_icon = tk.PhotoImage(file="Assets/file.png")

        row_frame = tk.Frame(main_frame, bg=COLOR_BACKGROUND)
        row_frame.pack(expand=True)
        
        ## -- Audio Boxes -- ##
        
        # Input Audio Box
        self.input_card = tk.Frame(row_frame, bg=COLOR_CARD_BACKGROUND, height=250, width=250, highlightthickness=2, highlightbackground=COLOR_CARD_BACKGROUND)
        self.input_card.pack(side="left", padx=20)
        self.input_card.pack_propagate(False)

        input_inner = tk.Frame(self.input_card, bg=COLOR_CARD_BACKGROUND)
        input_inner.pack(expand=True)
        tk.Label(input_inner, image=self.upload_icon, bg=COLOR_CARD_BACKGROUND).pack(pady=5)
        self.input_label_var = tk.StringVar(value="Input Audio File")
        self.input_label = tk.Label(input_inner, textvariable=self.input_label_var, font=("TkDefaultFont", 18))
        self.input_label.pack(pady=5)
        Button(self.input_card, text="Select File", bg=COLOR_BUTTON, fg=COLOR_TEXT, relief="flat", highlightbackground="white",
                    command=self._select_input_file).pack(side="bottom", pady=10)
        
        # Noise Audio Box
        self.noise_card = tk.Frame(row_frame, bg=COLOR_CARD_BACKGROUND, height=250, width=250, highlightthickness=2, highlightbackground=COLOR_CARD_BACKGROUND)
        self.noise_card.pack(side="left", padx=20)
        self.noise_card.pack_propagate(False)

        noise_inner = tk.Frame(self.noise_card, bg=COLOR_CARD_BACKGROUND)
        noise_inner.pack(expand=True)
        tk.Label(noise_inner, image=self.upload_icon, bg=COLOR_CARD_BACKGROUND).pack(pady=5)
        self.noise_label_var = tk.StringVar(value="Noise Sample File")
        self.noise_label = tk.Label(noise_inner, textvariable=self.noise_label_var, font=("TkDefaultFont", 18))
        self.noise_label.pack(pady=5)
        Button(self.noise_card, text="Select Noise", bg=COLOR_BUTTON, fg=COLOR_TEXT, relief="flat", highlightbackground="white",
                    command=self._select_noise_file).pack(side="bottom", pady=10)
        
        # Cancel Noise Box (Tkinter has an issue with button styling, so this box is a workaround)
        cancel_card = tk.Frame(main_frame, bg="white", height=20, width=100)
        cancel_card.pack(side="bottom", pady=20)
        cancel_card.pack_propagate(False)

        Button(cancel_card, text="Cancel Noise", bg=COLOR_BUTTON2, fg=COLOR_TEXT, relief="flat", highlightbackground=COLOR_BACKGROUND,
                    command=self._process_files).pack(expand=True)
      
    ## -- FILE SELECTION HANDLERS -- ##
    def _select_input_file(self):
        file = filedialog.askopenfilename(
            title="Select Input Audio",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.flac *.aac")]
        )
        if file:
            self.input_file = file
            self.input_label_var.set(file.split("/")[-1])
            self.input_card.configure(highlightbackground=COLOR_BUTTON)
            messagebox.showinfo("Selected", f"Input Audio:\n{file}")

    def _select_noise_file(self):
        file = filedialog.askopenfilename(
            title="Select Noise Sample",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.flac *.aac")]
        )
        if file:
            self.noise_file = file
            self.noise_label_var.set(file.split("/")[-1])
            self.noise_card.configure(highlightbackground=COLOR_BUTTON)
            messagebox.showinfo("Selected", f"Noise Sample:\n{file}")
            
    ## -- PROCESSING HANDLER -- ##
    def _process_files(self):
        if not self.input_file:
            messagebox.showerror("Please select an input audio file.")
            return
        if not self.noise_file:
            messagebox.showerror("Please select a noise sample file.")
            return
        try:
            output_path = processing.cancel_noise(
                input_path=self.input_file,
                noise_path=self.noise_file
            )

            messagebox.showinfo("ERR", f"Noise not cancelled!\nNot saved to:{output_path} \n(ERR: Not implemented yet!)")

        except Exception as e:
            messagebox.showerror("Processing Error (Processing not implemented)", str(e))