'''
This file launches the noise cancelling app.
(e.g click the play button while this file is open)
'''

from ui.app import App

 # This is the main guard. it only runs when main.py is called
if __name__ == "__main__":
    # Runs the app
    app = App()
    app.mainloop()
