"""Tkinter/ttk desktop interface.

The GUI only collects the user's choices and talks to the registry
(available_targets, ConversionRequest, execute) - it contains no conversion logic.
"""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from . import available_targets, supported_pairs
from .app_logging import setup_logging


class ConverterApp(ttk.Frame):
    def __init__(self, root: tk.Tk):
        super().__init__(root, padding=12)
        self.root = root
        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.format_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Wybierz plik wejściowy.")

        self._build()
        for var in (self.source_var, self.output_var, self.format_var):
            var.trace_add("write", lambda *_: self._update_state())
        self._update_state()

    def _build(self) -> None:
        self.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Plik wejściowy:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self.source_var, state="readonly").grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(self, text="Wybierz…", command=self._choose_source).grid(row=0, column=2)

        ttk.Label(self, text="Katalog zapisu:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self.output_var, state="readonly").grid(row=1, column=1, sticky="ew", padx=6)
        ttk.Button(self, text="Wybierz…", command=self._choose_output).grid(row=1, column=2)

        ttk.Label(self, text="Format docelowy:").grid(row=2, column=0, sticky="w", pady=4)
        self.format_box = ttk.Combobox(self, textvariable=self.format_var, state="disabled", width=12)
        self.format_box.grid(row=2, column=1, sticky="w", padx=6)

        self.convert_button = ttk.Button(self, text="Konwertuj")
        self.convert_button.grid(row=3, column=0, columnspan=3, pady=(12, 6))

        ttk.Label(self, textvariable=self.status_var, wraplength=480, justify="left").grid(
            row=4, column=0, columnspan=3, sticky="w"
        )

    def _choose_source(self) -> None:
        path = filedialog.askopenfilename(title="Wybierz plik do konwersji")
        if not path:
            return
        source = Path(path)
        self.source_var.set(str(source))
        if not self.output_var.get():
            self.output_var.set(str(source.parent))

        targets = available_targets(source)
        self.format_box["values"] = targets
        self.format_var.set(targets[0] if len(targets) == 1 else "")
        self.format_box.configure(state="readonly" if targets else "disabled")
        self._update_state()

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Wybierz katalog zapisu", mustexist=True)
        if path:
            self.output_var.set(str(Path(path)))

    def _update_state(self) -> None:
        """Enable 'Konwertuj' only for a complete, supported selection and describe what is missing."""
        source = self.source_var.get()
        ready = False
        if not source:
            message = "Wybierz plik wejściowy."
        elif not self.format_box["values"]:
            sources = sorted({src for src, _ in supported_pairs()})
            message = (
                f"Pliki {Path(source).suffix or 'bez rozszerzenia'} nie są obsługiwane. "
                f"Wybierz plik: {', '.join(sources)}."
            )
        elif not self.format_var.get():
            message = "Wybierz format docelowy."
        elif not self.output_var.get():
            message = "Wybierz katalog zapisu."
        else:
            message = "Gotowe do konwersji."
            ready = True
        self.status_var.set(message)
        self.convert_button.configure(state="normal" if ready else "disabled")


def run() -> None:
    setup_logging()
    root = tk.Tk()
    root.title("Konwerter plików")
    root.minsize(560, 0)
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
