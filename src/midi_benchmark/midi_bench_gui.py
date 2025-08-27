# src/midi_benchmark/midi_bench_gui.py
"""
Ableton MIDI Benchmark GUI
"""

from __future__ import annotations
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import logging
import sys
from pathlib import Path

# Direct-to-SQL helpers
from .sql_load import insert_notes_df  # expects dict-like cfg
# NOTE: PandasGUI intentionally not called (kept disabled)

USE_PANDASGUI = False

CONFIG_KEYS = [
    "reference_midi", "performance_midi", "output_dir",
    "onset_tolerances_ms", "max_onset_ms", "split_note",
    "verbose", "write_direct_sql",
    "sql_server", "sql_database", "odbc_driver",
    "encrypt", "trust_server_certificate",
    "truncate_before_load", "load_reference", "load_performance",
    "mars",
]

DEFAULT_CONFIG = {
    "reference_midi": "",
    "performance_midi": "",
    "output_dir": "",
    "onset_tolerances_ms": "20,40,60",
    "max_onset_ms": 200,
    "split_note": "B2",
    "verbose": False,
    "write_direct_sql": True,
    "sql_server": r"(localdb)\MSSQLLocalDB",
    "sql_database": "ableton-midi-bench",
    "odbc_driver": "ODBC Driver 17 for SQL Server",
    "encrypt": False,                   # LocalDB: keep False
    "trust_server_certificate": False,
    "truncate_before_load": True,
    "load_reference": True,
    "load_performance": True,
    "mars": True,
}

def _default_config_path() -> Path:
    # Windows -> %APPDATA%\AbletonMidiBench\config.json
    # mac/linux -> ~/.config/ableton-midi-bench/config.json
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        cfg_dir = base / "AbletonMidiBench"
    else:
        cfg_dir = Path.home() / ".config" / "ableton-midi-bench"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "config.json"

LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "midi_bench_gui.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"),
              logging.StreamHandler()]
)

class MidiBenchGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ableton MIDI Benchmark")
        self.geometry("720x460")
        self.resizable(False, False)

        # Tk variables
        self.var_load_ref = tk.BooleanVar(value=True)
        self.var_load_perf = tk.BooleanVar(value=True)
        self.var_truncate = tk.BooleanVar(value=True)
        self.var_ref_path = tk.StringVar()
        self.var_perf_path = tk.StringVar()
        self.var_out_dir = tk.StringVar()
        self.var_onset_tol = tk.StringVar(value="20,40,60")
        self.var_max_onset_ms = tk.StringVar(value="200")
        self.var_split_note = tk.StringVar(value="B2")
        self.var_verbose = tk.BooleanVar(value=False)
        self.var_direct_sql = tk.BooleanVar(value=True)
        self.var_sql_server = tk.StringVar(value=r"(localdb)\MSSQLLocalDB")
        self.var_sql_db = tk.StringVar(value="ableton-midi-bench")
        self.var_odbc_driver = tk.StringVar(value="ODBC Driver 17 for SQL Server")
        self.var_encrypt = tk.BooleanVar(value=False)
        self.var_trust_cert = tk.BooleanVar(value=False)
        self.var_mars = tk.BooleanVar(value=True)

        self.create_widgets()

        # Auto-load last config (no user action required)
        self._config_path = _default_config_path()
        self.load_config(self._config_path if self._config_path.exists() else DEFAULT_CONFIG)

    # ---------------- UI ----------------
    def create_widgets(self):
        row = 0
        # Reference
        tk.Checkbutton(self, text="Load Reference MIDI", variable=self.var_load_ref).grid(row=row, column=0, sticky="w", padx=(8,2))
        tk.Label(self, text="Reference MIDI file:").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_ref_path, width=44).grid(row=row, column=2, sticky="w")
        tk.Button(self, text="Browse", command=self.browse_ref).grid(row=row, column=3, padx=4)
        row += 1

        # Performance
        tk.Checkbutton(self, text="Load Performance MIDI", variable=self.var_load_perf).grid(row=row, column=0, sticky="w", padx=(8,2))
        tk.Label(self, text="Performance MIDI file:").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_perf_path, width=44).grid(row=row, column=2, sticky="w")
        tk.Button(self, text="Browse", command=self.browse_perf).grid(row=row, column=3, padx=4)
        row += 1

        # Output dir
        tk.Label(self, text="Output directory:").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_out_dir, width=44).grid(row=row, column=2, sticky="w")
        tk.Button(self, text="Browse", command=self.browse_out).grid(row=row, column=3, padx=4)
        row += 1

        # Matching parameters
        tk.Label(self, text="Onset tolerance list (ms):").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_onset_tol, width=22).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Label(self, text="Max onset ms:").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_max_onset_ms, width=22).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Label(self, text="Bass/Harmony Split Note (e.g., B2, 47):").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_split_note, width=22).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Checkbutton(self, text="Verbose Logging", variable=self.var_verbose).grid(row=row, column=2, sticky="w")
        row += 1

        # SQL options
        tk.Checkbutton(self, text="Write directly to SQL Server (skip CSV)", variable=self.var_direct_sql).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Label(self, text="SQL Server/Instance:").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_sql_server, width=30).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Label(self, text="SQL Database:").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_sql_db, width=30).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Label(self, text="ODBC Driver:").grid(row=row, column=1, sticky="e")
        tk.Entry(self, textvariable=self.var_odbc_driver, width=30).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Checkbutton(self, text="Encrypt (yes/no)", variable=self.var_encrypt).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Checkbutton(self, text="TrustServerCertificate (yes/no)", variable=self.var_trust_cert).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Checkbutton(self, text="MARS (multiple active result sets)", variable=self.var_mars).grid(row=row, column=2, sticky="w")
        row += 1

        tk.Checkbutton(self, text="Replace (truncate) tables before load", variable=self.var_truncate).grid(row=row, column=2, sticky="w")
        row += 1

        # Action buttons
        tk.Button(self, text="Run Comparison", command=self.run_comparison).grid(row=row, column=2, pady=10)
        row += 1

        tk.Button(self, text="Open Log File", command=self.open_log_file).grid(row=row, column=2, pady=4)
        tk.Button(self, text="Save Config", command=self.save_config_standard).grid(row=row, column=1, pady=4)
        tk.Button(self, text="Reload Last Config", command=self.reload_last_config).grid(row=row, column=3, pady=4)

    # ------------- File pickers -------------
    def browse_ref(self):
        path = filedialog.askopenfilename(title="Select Reference MIDI File",
                                          filetypes=[("MIDI files", "*.mid;*.midi"), ("All files", "*.*")])
        if path:
            self.var_ref_path.set(path)

    def browse_perf(self):
        path = filedialog.askopenfilename(title="Select Performance MIDI File",
                                          filetypes=[("MIDI files", "*.mid;*.midi"), ("All files", "*.*")])
        if path:
            self.var_perf_path.set(path)

    def browse_out(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.var_out_dir.set(path)

    # ------------- Config I/O -------------
    def _collect_config(self) -> dict:
        return {
            "reference_midi": self.var_ref_path.get(),
            "performance_midi": self.var_perf_path.get(),
            "output_dir": self.var_out_dir.get(),
            "onset_tolerances_ms": self.var_onset_tol.get(),
            "max_onset_ms": int(self.var_max_onset_ms.get() or "200"),
            "split_note": self.var_split_note.get(),
            "verbose": self.var_verbose.get(),
            "write_direct_sql": self.var_direct_sql.get(),
            "sql_server": self.var_sql_server.get(),
            "sql_database": self.var_sql_db.get(),
            "odbc_driver": self.var_odbc_driver.get(),
            "encrypt": bool(self.var_encrypt.get()),
            "trust_server_certificate": bool(self.var_trust_cert.get()),
            "truncate_before_load": bool(self.var_truncate.get()),
            "load_reference": bool(self.var_load_ref.get()),
            "load_performance": bool(self.var_load_perf.get()),
            "mars": bool(self.var_mars.get()),
        }

    def save_config_standard(self):
        cfg = self._collect_config()
        path = self._config_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            messagebox.showinfo("Config", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Config", f"Failed to save config:\n{e}")

    def reload_last_config(self):
        self.load_config(self._config_path)

    def load_config(self, path_or_dict):
        try:
            if isinstance(path_or_dict, dict):
                config = path_or_dict
            else:
                path = Path(path_or_dict)
                if not path.exists():
                    config = DEFAULT_CONFIG
                else:
                    with open(path, "r", encoding="utf-8") as f:
                        config = json.load(f)
            # apply
            self.var_ref_path.set(config.get("reference_midi", ""))
            self.var_perf_path.set(config.get("performance_midi", ""))
            self.var_out_dir.set(config.get("output_dir", ""))
            self.var_onset_tol.set(config.get("onset_tolerances_ms", "20,40,60"))
            self.var_max_onset_ms.set(str(config.get("max_onset_ms", 200)))
            self.var_split_note.set(config.get("split_note", "B2"))
            self.var_verbose.set(bool(config.get("verbose", False)))
            self.var_direct_sql.set(bool(config.get("write_direct_sql", True)))
            self.var_sql_server.set(config.get("sql_server", r"(localdb)\MSSQLLocalDB"))
            self.var_sql_db.set(config.get("sql_database", "ableton-midi-bench"))
            self.var_odbc_driver.set(config.get("odbc_driver", "ODBC Driver 17 for SQL Server"))
            self.var_encrypt.set(bool(config.get("encrypt", False)))
            self.var_trust_cert.set(bool(config.get("trust_server_certificate", False)))
            self.var_truncate.set(bool(config.get("truncate_before_load", True)))
            self.var_load_ref.set(bool(config.get("load_reference", True)))
            self.var_load_perf.set(bool(config.get("load_performance", True)))
            self.var_mars.set(bool(config.get("mars", True)))
        except Exception as e:
            logging.exception("Failed to load config.")
            messagebox.showerror("Config", f"Failed to load config:\n{e}")

    # ------------- Actions -------------
    def open_log_file(self):
        try:
            if sys.platform.startswith("win"):
                os.startfile(LOG_FILE)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(LOG_FILE)])
            else:
                subprocess.Popen(["xdg-open", str(LOG_FILE)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log file: {e}")

    def run_comparison(self):
        # Must load at least one
        if not self.var_load_ref.get() and not self.var_load_perf.get():
            messagebox.showinfo("Nothing to load", "Enable Reference and/or Performance.")
            return

        # SQL path
        if self.var_direct_sql.get():
            from .loader import load_notes  # local import to keep GUI snappy
            cfg = {
                "server": self.var_sql_server.get(),
                "database": self.var_sql_db.get(),
                "odbc_driver": self.var_odbc_driver.get(),
                "encrypt": bool(self.var_encrypt.get()),
                "trust_server_certificate": bool(self.var_trust_cert.get()),
                "mars": bool(self.var_mars.get()),
            }
            truncate = bool(self.var_truncate.get())

            try:
                n_ref = n_perf = 0
                if self.var_load_ref.get():
                    ref_df = load_notes(self.var_ref_path.get(), split_note=self.var_split_note.get())
                    logging.info("Reference DataFrame head:\n%s\n\nColumns: %s",
                                 ref_df.head(), list(ref_df.columns))
                    n_ref = insert_notes_df(ref_df, "dbo.reference_notes", self.var_ref_path.get(), cfg, truncate=truncate)

                if self.var_load_perf.get():
                    perf_df = load_notes(self.var_perf_path.get(), split_note=self.var_split_note.get())
                    logging.info("Performance DataFrame head:\n%s\n\nColumns: %s",
                                 perf_df.head(), list(perf_df.columns))
                    n_perf = insert_notes_df(perf_df, "dbo.performance_notes", self.var_perf_path.get(), cfg, truncate=truncate)

                messagebox.showinfo("SQL Load", f"Loaded to SQL — reference: {n_ref}, performance: {n_perf}")
                return
            except Exception as e:
                logging.exception("Direct SQL load failed.")
                # keep this robust: don't assume specific columns exist
                try:
                    logging.error("Ref head (safe): %s", 'N/A' if not self.var_load_ref.get() else ref_df.head().to_dict(orient="records"))
                    logging.error("Perf head (safe): %s", 'N/A' if not self.var_load_perf.get() else perf_df.head().to_dict(orient="records"))
                except Exception:
                    pass
                messagebox.showerror("SQL Error", f"Direct SQL load failed:\n{e}")
                return

        # CLI/CSV fallback (if desired)
        cmd = self.build_cli_command()
        logging.info("Running comparison: %s", " ".join(cmd))
        src_dir = Path(__file__).resolve().parents[1]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=src_dir)
            per_note_path = Path(self.var_out_dir.get()) / "per_note_comparison.csv"
            if per_note_path.exists():
                if USE_PANDASGUI:
                    try:
                        import pandas as pd
                        from pandasgui import show
                        show(pd.read_csv(per_note_path))
                    except Exception as e:
                        logging.error("PandasGUI error: %s", e)
                messagebox.showinfo("Done", "Comparison complete.")
            else:
                messagebox.showinfo("Done", "Comparison complete (no per_note_comparison.csv found).")
        except subprocess.CalledProcessError as e:
            logging.error("CLI failed rc=%s\nstdout:\n%s\nstderr:\n%s", e.returncode, e.stdout, e.stderr)
            self.show_error_dialog(f"Failed to run comparison.\n\nCommand: {' '.join(cmd)}\nReturn code: {e.returncode}\n\nStdout:\n{e.stdout}\n\nStderr:\n{e.stderr}")
        except Exception as e:
            logging.exception("Unexpected error running comparison.")
            self.show_error_dialog(f"Unexpected error: {e}")

    def build_cli_command(self):
        python_exe = sys.executable
        cmd = [python_exe, "-m", "midi_benchmark.cli_compare", "compare"]
        if self.var_load_ref.get():
            cmd += ["--ref", self.var_ref_path.get()]
        if self.var_load_perf.get():
            cmd += ["--perf", self.var_perf_path.get()]
        cmd += [
            "--out", self.var_out_dir.get(),
            "--onset-tol-list", self.var_onset_tol.get(),
            "--max-onset-ms", self.var_max_onset_ms.get(),
            "--split-note", self.var_split_note.get(),
        ]
        return cmd

    def show_error_dialog(self, text: str):
        w = tk.Toplevel(self)
        w.title("Error Details (copy/paste supported)")
        w.geometry("640x420")
        t = tk.Text(w, wrap="word")
        t.insert("1.0", text)
        t.config(state="normal")
        t.pack(expand=True, fill="both")
        tk.Button(w, text="Close", command=w.destroy).pack(pady=6)

if __name__ == "__main__":
    app = MidiBenchGUI()
    app.mainloop()
