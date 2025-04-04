import tkinter as tk
from tkinter import ttk
import platform

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, height=500, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(self, height=height, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self._update_scrollregion)

        # ✅ Bind mousewheel when mouse enters/leaves the canvas area
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        print("[DEBUG] delta:", event.delta)  # You should now see this
        system = platform.system()
        if system == "Darwin":
            self.canvas.yview_scroll(-1 * event.delta, "units")  # delta is already small
        else:
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
