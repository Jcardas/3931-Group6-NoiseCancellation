import customtkinter as ctk
import threading
import os
from tkinter import messagebox
from core.processing import NoiseCanceller
from core.audio_utils import save_audio
from ui.theme import *
from ui.pages.file_selection import FileSelectionPage
from ui.pages.output_editor import OutputEditorPage


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Noise Canceller")
        self.geometry("1200x720")

        # State
        self.input_path = None
        self.noise_path = None
        self.processing_results = None
        self.processor = NoiseCanceller()

        # Pages container
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self.init_pages()
        self.show_page("FileSelectionPage")

    def init_pages(self):
        # We inject 'self' as the controller
        for PageClass in [FileSelectionPage, OutputEditorPage]:
            page_name = PageClass.__name__
            page = PageClass(parent=self.container, controller=self)
            self.pages[page_name] = page
            page.grid(row=0, column=0, sticky="nsew")

    def show_page(self, page_name):
        page = self.pages[page_name]
        if hasattr(page, "on_show"):
            page.on_show()
        page.tkraise()

    def set_files(self, input_p, noise_p):
        self.input_path = input_p
        self.noise_path = noise_p

    def run_processing(self, M, alpha, beta):
        """Runs processing in a separate thread"""

        # Show loading state if you have a spinner, or disable buttons
        self.configure(cursor="watch")

        def task():
            try:
                data = self.processor.process(
                    self.input_path, self.noise_path, M, alpha, beta
                )
                self.after(0, lambda: self.on_processing_success(data))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self.on_processing_error(err_msg))

        threading.Thread(target=task, daemon=True).start()

    def on_processing_success(self, data):
        self.configure(cursor="")
        self.processing_results = data
        self.show_page("OutputEditorPage")

    def on_processing_error(self, error_msg):
        self.configure(cursor="")
        messagebox.showerror("Error", error_msg)

    def save_output(self):
        if not self.processing_results:
            return

        # Save to Downloads
        downloads = os.path.expanduser("~/Downloads")
        filename = f"cleaned_{os.path.basename(self.input_path)}"
        path = os.path.join(downloads, filename)

        try:
            save_audio(
                path,
                self.processing_results["sample_rate"],
                self.processing_results["cleaned_audio"],
            )
            messagebox.showinfo("Saved", f"File saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))


if __name__ == "__main__":
    app = App()
    app.mainloop()
