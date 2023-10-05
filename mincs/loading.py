import tkinter as tk
import threading
import time
from PIL import Image, ImageTk
from itertools import cycle

class LoadingWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Opening minTS Control System...")
        self.geometry("500x500")
        self.iconbitmap("C:/Users/ramir/minTS_logo.ico")

        self.closed = False

        self.image_label = tk.Label(self)
        self.image_label.pack()

        self.loading_text = tk.StringVar()
        self.loading_text.set("Loading minCS...")
        self.text_label = tk.Label(self, textvariable=self.loading_text, font=("Arial", 16, "bold italic"))
        self.text_label.pack(side=tk.TOP)

        self.load_gif("logo.gif")
        self.animate_loading_text()

        # Set a timer to close the window after 3 seconds
        self.after(3000, self.close)

    def load_gif(self, gif_path):
        self.frames = []
        im = Image.open(gif_path)
        max_size = (450, 450)
        im.thumbnail(max_size, Image.LANCZOS)

        for i in range(im.n_frames):
            im.seek(i)
            rgba_frame = im.convert("RGBA")
            frame = ImageTk.PhotoImage(rgba_frame, format="RGBA")
            self.frames.append(frame)

        self.current_frame = 0
        self.update_gif()

    def update_gif(self):
        self.image_label.config(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.after(30, self.update_gif)

    def animate_loading_text(self):
        dot_anim = cycle(['', '.', '..', '...'])

        def update_text():
            self.loading_text.set(f"Loading minCS{next(dot_anim)}")
            self.after(500, update_text)

        update_text()

    def close(self):
        if not self.closed:
            self.closed = True
            self.destroy()