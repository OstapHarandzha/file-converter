"""Tkinter/ttk desktop interface.

The GUI only collects the user's choices and talks to the registry
(available_targets, ConversionRequest, execute) - it contains no conversion logic.
"""
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import ConversionError, ConversionRequest, available_targets, execute, supported_pairs
from .app_logging import LOG_FILE, setup_logging

POLL_MS = 100


class ConverterApp(ttk.Frame):
    def __init__(self, root: tk.Tk):
        super().__init__(root, padding=12)
        self.root = root
        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.format_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Wybierz plik wejściowy.")
        self.results: queue.Queue = queue.Queue()

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
        self.source_button = ttk.Button(self, text="Wybierz…", command=self._choose_source)
        self.source_button.grid(row=0, column=2)

        ttk.Label(self, text="Katalog zapisu:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=self.output_var, state="readonly").grid(row=1, column=1, sticky="ew", padx=6)
        self.output_button = ttk.Button(self, text="Wybierz…", command=self._choose_output)
        self.output_button.grid(row=1, column=2)

        ttk.Label(self, text="Format docelowy:").grid(row=2, column=0, sticky="w", pady=4)
        self.format_box = ttk.Combobox(self, textvariable=self.format_var, state="disabled", width=12)
        self.format_box.grid(row=2, column=1, sticky="w", padx=6)

        self.convert_button = ttk.Button(self, text="Konwertuj", command=self._convert)
        self.convert_button.grid(row=3, column=0, columnspan=3, pady=(12, 6))

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        self.progress.grid_remove()

        ttk.Label(self, textvariable=self.status_var, wraplength=480, justify="left").grid(
            row=5, column=0, columnspan=3, sticky="w"
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

    def _convert(self) -> None:
        request = ConversionRequest(
            source=Path(self.source_var.get()),
            target_format=self.format_var.get(),
            output_dir=Path(self.output_var.get()),
        )
        self._set_busy(True)
        self.status_var.set(f"Konwertowanie: {request.source.name} -> {request.target_format}…")
        threading.Thread(target=self._worker, args=(request,), daemon=True).start()
        self.after(POLL_MS, self._poll)

    def _worker(self, request: ConversionRequest) -> None:
        """Runs in a background thread - must not touch any widget."""
        try:
            self.results.put((True, execute(request)))
        except Exception as error:
            self.results.put((False, error))

    def _poll(self) -> None:
        try:
            ok, value = self.results.get_nowait()
        except queue.Empty:
            self.after(POLL_MS, self._poll)
            return
        self._set_busy(False)
        if ok:
            self.status_var.set(f"Zapisano: {value}")
            messagebox.showinfo("Konwersja zakończona", f"Zapisano plik:\n{value}", parent=self.root)
        elif isinstance(value, ConversionError):
            self.status_var.set(f"Błąd: {value.message}")
            messagebox.showerror("Błąd konwersji", str(value), parent=self.root)
        else:
            self.status_var.set(f"Nieoczekiwany błąd: {value}")
            messagebox.showerror(
                "Nieoczekiwany błąd", f"{value}\n\nSzczegóły w pliku {LOG_FILE}", parent=self.root
            )

    def _set_busy(self, busy: bool) -> None:
        """Lock the controls while a conversion runs so the user cannot start a second one."""
        state = "disabled" if busy else "normal"
        self.source_button.configure(state=state)
        self.output_button.configure(state=state)
        if busy:
            self.format_box.configure(state="disabled")
            self.convert_button.configure(state="disabled")
            self.progress.grid()
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress.grid_remove()
            self.format_box.configure(state="readonly" if self.format_box["values"] else "disabled")
            self._update_state()


def run() -> None:
    setup_logging()
    root = tk.Tk()
    root.title("Konwerter plików")
    root.minsize(560, 0)
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
