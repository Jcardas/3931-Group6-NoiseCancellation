import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk

# Color palette
COLOR_BUTTON = "#4A90E2"  # Blue for buttons/active states
COLOR_BACKGROUND = "#C3C3C3"  # Light grey background
COLOR_CARD_BACKGROUND = "#FFFFFF"  # White for boxes


# The Main Application Class
class AudioUploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Noise Canceller")
        self.root.geometry("600x500")  # Adjusted size
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BACKGROUND)

        # --- Define Audio File Types ---
        self.audio_types = [
            ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.aac"),
            ("All Files", "*.*")
        ]

        self._create_main_ui()

    def _create_main_ui(self):
        """Creates and displays the main UI as per the image."""

        main_frame = tk.Frame(self.root, bg=COLOR_BACKGROUND)
        main_frame.pack(expand=True, fill="both", padx=30, pady=30)

if __name__ == "__main__":
    # Use the theme
    root = tk.Tk()
    root.tk.call("source", "tkThemes/forest-dark.tcl")
    style = ttk.Style(root)
    style.theme_use("forest-dark")
    
    app = AudioUploaderApp(root)
    root.mainloop()
