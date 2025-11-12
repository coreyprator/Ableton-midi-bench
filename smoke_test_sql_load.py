# smoke_test_sql_load.py
from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
import sys
import traceback

import pandas as pd
import pretty_midi

from src.midi_benchmark.sql_load import insert_notes_df, build_conn_str, ensure_tables


# ---------- config ----------
REF_MIDI  = Path("data/reference_melody.mid")
PERF_MIDI = Path("data/performance_comping take 2025-08-25 0817.mid")

SQL_CFG = {
    "odbc_driver": os.environ.get("MIDI_BENCH_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"),
    "server": os.environ.get("MIDI_BENCH_SQL_SERVER", ""),
    "database": os.environ.get("MIDI_BENCH_SQL_DATABASE", ""),
    # legacy keys kept for compatibility; sql_load.build_conn_str expects booleans
    "encrypt": os.environ.get("MIDI_BENCH_ENCRYPT", "false").lower() in ("1", "true", "yes"),
    "trusted_connection": True,
}
# ----------------------------


def midi_to_df(midi_path: Path) -> pd.DataFrame:
    """
    Minimal, reliable extraction: start_s, end_s, dur_s, pitch, velocity, channel, program, track_name.
    """
    pm = pretty_midi.PrettyMIDI(str(midi_path))
    rows = []
    for ti, inst in enumerate(pm.instruments):
        prog = inst.program if not inst.is_drum else 0
        tname = inst.name or ""
        ch = 9 if inst.is_drum else 0  # pretty_midi doesn't expose channel reliably; default 0 (MIDI channel often irrelevant here)
        for n in inst.notes:
            start = float(n.start)
            end   = float(n.end)
            dur   = max(0.0, end - start)
            rows.append({
                "track_index": ti,
                "track_name": tname,
                "is_drum": 1 if inst.is_drum else 0,
                "channel": ch,
                "program": prog,
                "pitch": int(n.pitch),
                "velocity": int(n.velocity),
                "start_s": start,
                "end_s": end,
                "dur_s": dur,
                # optional musical fields left out (NULL in SQL)
            })
    df = pd.DataFrame(rows)
    if df.empty:
        print(f"[WARN] No notes found in {midi_path}")
    return df


def run():
    print("Building connection string:", build_conn_str(SQL_CFG))

    # Prepare reference
    print(f"Loading reference MIDI: {REF_MIDI}")
    ref_df = midi_to_df(REF_MIDI)
    print(f"Reference rows: {len(ref_df)}")
    print(ref_df.head(10).to_string(index=False))

    # Prepare performance
    print(f"\nLoading performance MIDI: {PERF_MIDI}")
    perf_df = midi_to_df(PERF_MIDI)
    print(f"Performance rows: {len(perf_df)}")
    print(perf_df.head(10).to_string(index=False))

    # Insert
    print("\nInserting into SQL...")
    ref_rows = insert_notes_df(
        ref_df,
        table="dbo.reference_notes",
        source_filename=str(REF_MIDI),
        cfg=SQL_CFG,
        truncate=True,  # overwrite reference for repeatable runs
    )
    perf_rows = insert_notes_df(
        perf_df,
        table="dbo.performance_notes",
        source_filename=str(PERF_MIDI),
        cfg=SQL_CFG,
        truncate=True,  # overwrite performance for repeatable runs
    )
    print(f"[DONE] Inserted reference: {ref_rows} rows; performance: {perf_rows} rows.")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print("\n[ERROR] Direct-to-SQL smoke test failed.")
        print("Type:", type(e).__name__)
        print("Message:", e)
        traceback.print_exc()
        sys.exit(1)
