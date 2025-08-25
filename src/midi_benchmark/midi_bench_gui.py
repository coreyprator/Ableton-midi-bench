"""
Ableton MIDI Benchmark GUI

Last updated: 2025-08-25

This script provides a graphical user interface for benchmarking and comparing MIDI files using musically meaningful metrics. It allows users to select reference and performance MIDI files, configure matching parameters, and view detailed per-note comparison results.

To launch the GUI from the command line, use:
    python -m midi_benchmark.midi_bench_gui

Ensure you run this from the src directory or that your PYTHONPATH includes the src folder, and that your virtual environment is activated.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import logging
import sys

# Setup logging
import pathlib
LOG_DIR = pathlib.Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = str(LOG_DIR / "midi_bench_gui.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

CONFIG_FILE = "midi_bench_gui_config.json"

class MidiBenchGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Ableton MIDI Benchmark")
        self.geometry("600x400")
        self.ref_path = tk.StringVar()
        self.perf_path = tk.StringVar()
        self.out_dir = tk.StringVar()
        self.onset_tol = tk.StringVar(value="20,40,60")
        self.max_onset_ms = tk.StringVar(value="200")
        self.split_note = tk.StringVar(value="B2")
        self.verbose = tk.BooleanVar(value=False)
        # self.create_menu()  # Removed because method does not exist
        self.load_config()
        self.create_widgets()

    def save_config(self):
        config = {
            "ref_path": self.ref_path.get(),
            "perf_path": self.perf_path.get(),
            "out_dir": self.out_dir.get(),
            "onset_tol": self.onset_tol.get(),
            "max_onset_ms": self.max_onset_ms.get(),
            "split_note": self.split_note.get(),
            "verbose": self.verbose.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        messagebox.showinfo("Config", "Configuration saved.")

    def open_log_file(self):
        import platform
        try:
            if platform.system() == "Windows":
                os.startfile(LOG_FILE)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", LOG_FILE])
            else:
                subprocess.Popen(["xdg-open", LOG_FILE])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log file: {e}")
    def browse_ref(self):
        path = filedialog.askopenfilename(title="Select Reference MIDI File", filetypes=[("MIDI files", "*.mid;*.midi"), ("All files", "*")])
        if path:
            self.ref_path.set(path)

    def browse_perf(self):
        path = filedialog.askopenfilename(title="Select Performance MIDI File", filetypes=[("MIDI files", "*.mid;*.midi"), ("All files", "*")])
        if path:
            self.perf_path.set(path)

    def browse_out(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.out_dir.set(path)

    def build_cli_command(self):
        # Use the current Python executable for portability
        python_exe = sys.executable
        cmd = [
            python_exe, "-m", "midi_benchmark.cli_compare", "compare",
            "--ref", self.ref_path.get(),
            "--perf", self.perf_path.get(),
            "--out", self.out_dir.get(),
            "--onset-tol-list", self.onset_tol.get(),
            "--max-onset-ms", self.max_onset_ms.get(),
            "--split-note", self.split_note.get()
        ]
        return cmd

    def run_comparison(self):
        try:
            cmd = self.build_cli_command()
            logging.info(f"Running comparison: {' '.join(cmd)}")
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=src_dir)
            per_note_path = os.path.join(self.out_dir.get(), "per_note_comparison.csv")
            if os.path.exists(per_note_path):
                if os.path.getsize(per_note_path) == 0:
                    logging.error(f"per_note_comparison.csv is empty: {per_note_path}")
                    messagebox.showerror("PandasGUI Error", "per_note_comparison.csv is empty. No data to display.\n\nSee log for details.")
                else:
                    self.launch_pandasgui(per_note_path)
                    logging.info("Comparison complete. To view results interactively, install pandasgui and open per_note_comparison.csv.")
                    messagebox.showinfo("Done", "Comparison complete. To view results interactively, install pandasgui and open per_note_comparison.csv.")
            else:
                logging.error("No data grid presented: per_note_comparison.csv not found.")
                messagebox.showinfo("Done", "Comparison complete, but per_note_comparison.csv not found.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Comparison failed. Return code: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}")
            self.show_error_dialog(
                f"Failed to run comparison.\n\nCommand: {' '.join(cmd)}\nReturn code: {e.returncode}\n\nStdout:\n{e.stdout}\n\nStderr:\n{e.stderr}\n\nSee midi_bench_gui.log for full details."
            )
        except Exception as e:
            logging.exception("Unexpected error running comparison.")
            self.show_error_dialog(f"Unexpected error: {e}\nSee midi_bench_gui.log for details.")

    def create_widgets(self):
        row = 0
        tk.Label(self, text="Reference MIDI file:").grid(row=row, column=0, sticky="e")
        tk.Entry(self, textvariable=self.ref_path, width=40).grid(row=row, column=1)
        tk.Button(self, text="Browse", command=self.browse_ref).grid(row=row, column=2)
        row += 1

        tk.Label(self, text="Performance MIDI file:").grid(row=row, column=0, sticky="e")
        tk.Entry(self, textvariable=self.perf_path, width=40).grid(row=row, column=1)
        tk.Button(self, text="Browse", command=self.browse_perf).grid(row=row, column=2)
        row += 1

        tk.Label(self, text="Output directory:").grid(row=row, column=0, sticky="e")
        tk.Entry(self, textvariable=self.out_dir, width=40).grid(row=row, column=1)
        tk.Button(self, text="Browse", command=self.browse_out).grid(row=row, column=2)
        row += 1

        tk.Label(self, text="Onset tolerance list (ms):").grid(row=row, column=0, sticky="e")
        tk.Entry(self, textvariable=self.onset_tol, width=20).grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(self, text="Max onset ms:").grid(row=row, column=0, sticky="e")
        tk.Entry(self, textvariable=self.max_onset_ms, width=20).grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(self, text="Bass/Harmony Split Note (e.g., B2, 47):").grid(row=row, column=0, sticky="e")
        tk.Entry(self, textvariable=self.split_note, width=20).grid(row=row, column=1, sticky="w")
        row += 1

        tk.Checkbutton(self, text="Verbose Logging", variable=self.verbose).grid(row=row, column=1, sticky="w")
        row += 1

        tk.Button(self, text="Run Comparison", command=self.run_comparison).grid(row=row, column=1, pady=10)
        row += 1

        tk.Button(self, text="Open Log File", command=self.open_log_file).grid(row=row, column=1, pady=5)
        row += 1

        tk.Button(self, text="Save Config", command=self.save_config).grid(row=row, column=0, pady=5)
        tk.Button(self, text="Load Config", command=self.load_config).grid(row=row, column=2, pady=5)
        row += 1

        tk.Button(self, text="Diagnose Last Error", command=self.diagnose_last_error).grid(row=row, column=1, pady=5)

    def diagnose_last_error(self):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Find the last error block
            error_lines = []
            for line in reversed(lines):
                if "ERROR" in line or "Traceback" in line:
                    error_lines.insert(0, line)
                    if "ERROR" in line:
                        break
            error_text = ''.join(error_lines).strip()
            suggestion = self.suggest_fix(error_text)
            self.show_error_dialog(f"Last error:\n\n{error_text}\n\nSuggested fix:\n{suggestion}")
        except Exception as e:
            self.show_error_dialog(f"Could not read log file: {e}")

    def suggest_fix(self, error_text):
        # Simple heuristics for common errors
        if "ModuleNotFoundError: No module named 'click'" in error_text:
            return "Install the missing package by running: pip install click"
        if "ModuleNotFoundError: No module named 'pretty_midi'" in error_text:
            return "Install the missing package by running: pip install pretty_midi"
        if "ModuleNotFoundError: No module named 'music21'" in error_text:
            return "Install the missing package by running: pip install music21"
        if "ModuleNotFoundError: No module named 'pandas'" in error_text:
            return "Install the missing package by running: pip install pandas"

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            self.ref_path.set(config.get("ref_path", ""))
            self.perf_path.set(config.get("perf_path", ""))
            self.out_dir.set(config.get("out_dir", ""))
            self.onset_tol.set(config.get("onset_tol", "20,40,60"))
            self.max_onset_ms.set(config.get("max_onset_ms", "200"))
            self.split_note.set(config.get("split_note", "B2"))
            self.verbose.set(config.get("verbose", False))

    # Removed duplicate, broken load_config method

    def show_error_dialog(self, error_text):
        # Show error in a scrollable, copyable dialog
        err_win = tk.Toplevel(self)
        err_win.title("Error Details (copy/paste supported)")
        err_win.geometry("600x400")
        txt = tk.Text(err_win, wrap="word")
        txt.insert("1.0", error_text)
        txt.config(state="normal")
        txt.pack(expand=True, fill="both")
        tk.Button(err_win, text="Close", command=err_win.destroy).pack(pady=5)

    def launch_pandasgui(self, csv_path):
        try:
            import pandas as pd
            from pandasgui import show
            df = pd.read_csv(csv_path)
            show(df)
        except ImportError:
            messagebox.showinfo(
                "PandasGUI Not Installed",
                "pandasgui is not installed. To view the results interactively, install pandasgui (pip install pandasgui) and open the CSV manually."
            )
        except Exception as e:
            messagebox.showerror(
                "Error Launching PandasGUI",
                f"Could not open CSV in pandasgui: {e}"
            )

if __name__ == "__main__":
    app = MidiBenchGUI()
    app.mainloop()
