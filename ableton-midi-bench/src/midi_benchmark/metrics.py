"""
Metrics computation for MIDI note matching.
"""
from typing import List, Tuple
import numpy as np
import pandas as pd

def compute_metrics(
    ref_df: pd.DataFrame,
    perf_df: pd.DataFrame,
    matches: list[tuple[int, int]],
    onset_tols_ms: list[int] = [20, 40, 60]
) -> tuple[pd.DataFrame, dict]:
    """
    Compute per-note and summary metrics.
    """
    rows = []
    for i_ref, j_perf in matches:
        ref = ref_df.loc[i_ref]
        perf = perf_df.loc[j_perf]
        onset_err_ms = (perf["start"] - ref["start"]) * 1000
        ref_dur = ref["dur"]
        perf_dur = perf["dur"]
        dur_ratio = perf_dur / ref_dur if ref_dur != 0 else 0.0
        vel_err = perf["vel"] - ref["vel"]
        rows.append({
            "pitch": ref["pitch"],
            "ref_start_s": ref["start"],
            "perf_start_s": perf["start"],
            "onset_err_ms": onset_err_ms,
            "ref_dur_s": ref_dur,
            "perf_dur_s": perf_dur,
            "dur_ratio": dur_ratio,
            "ref_vel": ref["vel"],
            "perf_vel": perf["vel"],
            "vel_err": vel_err
        })
    per_note_df = pd.DataFrame(rows)
    summary = {}
    summary["ref_notes"] = len(ref_df)
    summary["perf_notes"] = len(perf_df)
    summary["matched"] = len(matches)
    summary["missed"] = summary["ref_notes"] - summary["matched"]
    summary["extra"] = summary["perf_notes"] - summary["matched"]
    summary["match_rate_%"] = 100 * summary["matched"] / summary["ref_notes"] if summary["ref_notes"] else 0.0
    # Onset error stats
    if not per_note_df.empty:
        summary["onset_err_ms_mean"] = float(np.mean(np.abs(per_note_df["onset_err_ms"])) if len(per_note_df) else 0)
        summary["onset_err_ms_median"] = float(np.median(np.abs(per_note_df["onset_err_ms"])) if len(per_note_df) else 0)
        summary["onset_err_ms_sd"] = float(np.std(per_note_df["onset_err_ms"]))
        summary["dur_ratio_mean"] = float(np.mean(per_note_df["dur_ratio"]))
        summary["dur_ratio_median"] = float(np.median(per_note_df["dur_ratio"]))
        summary["dur_ratio_sd"] = float(np.std(per_note_df["dur_ratio"]))
        summary["vel_err_mean"] = float(np.mean(per_note_df["vel_err"]))
        summary["vel_err_median"] = float(np.median(per_note_df["vel_err"]))
        summary["vel_err_sd"] = float(np.std(per_note_df["vel_err"]))
        for tol in onset_tols_ms:
            pct = 100 * np.mean(np.abs(per_note_df["onset_err_ms"]) <= tol) if len(per_note_df) else 0
            summary[f"timing_within_{tol}ms_%"] = pct
    else:
        for k in ["onset_err_ms_mean","onset_err_ms_median","onset_err_ms_sd",
                  "dur_ratio_mean","dur_ratio_median","dur_ratio_sd",
                  "vel_err_mean","vel_err_median","vel_err_sd"]:
            summary[k] = 0.0
        for tol in onset_tols_ms:
            summary[f"timing_within_{tol}ms_%"] = 0.0
    return per_note_df, summary
