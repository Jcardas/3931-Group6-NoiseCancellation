'''
The app
'''

import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
import processing
import os

# Color palette
COLOR_BUTTON = "#4A90E2"
COLOR_BUTTON_HOVER = "#7CAEE6"
COLOR_BACKGROUND = "#E3E3E3"
COLOR_CARD_BACKGROUND = "#FFFFFF"
COLOR_TEXT = "#000000"


class NoiseCancellerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Noise Canceller (CTk Version)")
        self.geometry("650x520")
        ctk.set_appearance_mode("light")
        self.configure(fg_color=COLOR_BACKGROUND)

        self.input_file = None
        self.noise_file = None

        self._build_ui()

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        main_frame.pack(expand=True, fill="both")

        row_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BACKGROUND)
        row_frame.pack(pady=40)

        # INPUT FILE CARD
        self.input_card = ctk.CTkFrame(row_frame, width=250, height=250, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.input_card.pack(side="left", padx=20)
        self.input_card.pack_propagate(False)

        input_inner = ctk.CTkFrame(self.input_card, fg_color=COLOR_CARD_BACKGROUND)
        input_inner.pack(expand=True)
        
        img = PhotoImage(file="Assets/file.png")
        img_label = ctk.CTkLabel(input_inner, image=img, text="")
        img_label.image = img  # Keep a reference
        img_label.pack(pady=10)

        self.input_label = ctk.CTkLabel(input_inner, text="Input Audio File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=18))
        self.input_label.pack(pady=10)

        ctk.CTkButton(self.input_card, text="Select File", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=self._select_input_file).pack(side="bottom", pady=10)

        # NOISE FILE CARD
        self.noise_card = ctk.CTkFrame(row_frame, width=250, height=250, fg_color=COLOR_CARD_BACKGROUND, border_width=2, border_color=COLOR_CARD_BACKGROUND)
        self.noise_card.pack(side="left", padx=20)
        self.noise_card.pack_propagate(False)

        noise_inner = ctk.CTkFrame(self.noise_card, fg_color=COLOR_CARD_BACKGROUND)
        noise_inner.pack(expand=True)
        
  
        img_label2 = ctk.CTkLabel(noise_inner, image=img, text="")
        img_label2.image = img  # Keep a reference
        img_label2.pack(pady=10)

        self.noise_label = ctk.CTkLabel(noise_inner, text="Noise Sample File", text_color=COLOR_TEXT, font=ctk.CTkFont(size=18))
        self.noise_label.pack(pady=10)

        ctk.CTkButton(self.noise_card, text="Select Noise", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=self._select_noise_file).pack(side="bottom", pady=10)

        # PROCESS BUTTON
        bottom_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_BACKGROUND)
        bottom_frame.pack(pady=20)

        ctk.CTkButton(bottom_frame, text="Cancel Noise", fg_color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER,
                      command=self._process_files).pack()

    # ===========================
    # FILE SELECTION
    # ===========================
    def _select_input_file(self):
        file = filedialog.askopenfilename(title="Select Input Audio (.wav)", filetypes=[("Audio Files", "*.wav")])
        if file:
            self.input_file = file
            self.input_label.configure(text=os.path.basename(file))
            self.input_card.configure(border_color=COLOR_BUTTON)
            messagebox.showinfo("Selected", f"Input Audio: {os.path.basename(file)}")

    def _select_noise_file(self):
        file = filedialog.askopenfilename(title="Select Noise Sample (.wav)", filetypes=[("Audio Files", "*.wav")])
        if file:
            self.noise_file = file
            self.noise_label.configure(text=os.path.basename(file))
            self.noise_card.configure(border_color=COLOR_BUTTON)
            messagebox.showinfo("Selected", f"Noise Sample: {os.path.basename(file)}")

    # ===========================
    # PROCESSING
    # ===========================
    def _process_files(self):
        if not self.input_file:
            messagebox.showerror("Error", "Please select an input audio file.")
            return
        if not self.noise_file:
            messagebox.showerror("Error", "Please select a noise sample file.")
            return

        try:
            output_path = processing.cancel_noise(
                input_path=self.input_file,
                noise_path=self.noise_file
            )
            messagebox.showinfo("Success", f"Noise cancelled!\nSaved to: {output_path}")
        except Exception as e:
            messagebox.showerror("Processing Error", str(e))


if __name__ == "__main__":
    app = NoiseCancellerApp()
    app.mainloop()