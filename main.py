import tkinter as tk
from tkinter import ttk

from gui import NoiseCancellerGUI   # Import the GUI class

def main():
    root = tk.Tk()

    # Load custom ttk theme
    try:
        root.tk.call("source", "tkThemes/forest-dark.tcl")
        style = ttk.Style(root)
        style.theme_use("forest-dark")
    except Exception:
        print("Warning: Theme not found. Using default Tk theme.")

    # Instantiate the GUI
    app = NoiseCancellerGUI(root)

    # Start the Tkinter event loop
    root.mainloop()

# Main guard
if __name__ == "__main__":
    main()