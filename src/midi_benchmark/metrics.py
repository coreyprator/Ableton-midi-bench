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
    def midi_to_note_name(pitch):
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (int(pitch) // 12) - 1
        name = note_names[int(pitch) % 12]
        return f"{name}{octave}"

    def get_beat_measure(start_s, tempo, ppq=480):
        # Assumes 4/4, returns (beat, measure, measure.beat string)
        if tempo <= 0:
            return (None, None, None)
        beats_per_sec = tempo / 60.0
        beat = start_s * beats_per_sec
        measure = int(beat // 4) + 1
        beat_in_measure = int(beat % 4) + 1  # always 1-4 in 4/4
        measure_beat = f"{measure}.{beat_in_measure}"
        return (beat_in_measure, measure, measure_beat)

    # Try to get tempo from ref_df if present
    tempo = 120.0
    if hasattr(ref_df, 'midi_tempo'):
        tempo = getattr(ref_df, 'midi_tempo', 120.0)
    elif hasattr(ref_df, 'tempo'):
        tempo = getattr(ref_df, 'tempo', 120.0)

    # Chord detection helper
    def detect_chord(pitches):
        # Require music21 for chord detection; raise error if not available
        try:
            from music21 import chord as m21chord
        except ImportError:
            raise ImportError("music21 is required for chord detection. Please install it with 'pip install music21'.")
        c = m21chord.Chord(pitches)
        return c.pitchedCommonName

    # Group reference notes by start time for chord detection
    ref_groups = ref_df.groupby("start")
    start_to_chord = {}
    for start, group in ref_groups:
        pitches = list(group["pitch"])
        chord_name = detect_chord(pitches)
        start_to_chord[start] = chord_name

    rows = []
    matched_perf_indices = set(j for _, j in matches)
    matched_ref_indices = set(i for i, _ in matches)
    # Build a lookup for performance notes by (measure, beat)
    perf_lookup = {}
    for idx, perf in perf_df.iterrows():
        perf_beat, perf_measure, perf_measure_beat = get_beat_measure(perf["start"], tempo)
        perf_lookup[(perf_measure, perf_beat)] = (idx, perf)

    import logging
    logging.info(f"[metrics.py] Entering ref_df.iterrows() loop with {len(ref_df)} rows.")
    for i_ref, ref in ref_df.iterrows():
        if i_ref < 5:
            logging.info(f"[metrics.py] ref_df row {i_ref}: {ref.to_dict()}")
        ref_beat, ref_measure, ref_measure_beat = get_beat_measure(ref["start"], tempo)
        ref_note_name = midi_to_note_name(ref["pitch"])
        chord = start_to_chord.get(ref["start"], "")
        # Try to find a performance note at the same measure/beat
        match = perf_lookup.get((ref_measure, ref_beat))
        alignment_status = "missing"
        misplayed_note = False
        onset_err_ms = None
        perf_note_name = None
        perf_start_s = None
        perf_dur_s = None
        perf_vel = None
        vel_err = None
        dur_ratio = None
        perf_measure_beat = None
        perf_measure = None
        perf_beat = None
        ref_part = ref["part"] if "part" in ref else None
        ref_color = ref["color"] if "color" in ref else None
        perf_part = None
        perf_color = None
        perf_pitch = None
        if match:
            idx_perf, perf = match
            perf_part = perf["part"] if "part" in perf else None
            perf_color = perf["color"] if "color" in perf else None
            perf_pitch = perf["pitch"] if match and perf is not None else None
            # ENFORCE: Only accept match if ref_part == perf_part
            if ref_part is not None and perf_part is not None and ref_part != perf_part:
                match = None
                perf_note_name = None
                perf_start_s = None
                perf_dur_s = None
                perf_vel = None
                vel_err = None
                dur_ratio = None
                perf_beat = None
                perf_measure = None
                perf_measure_beat = None
                perf_color = None
                alignment_status = "missing"
                misplayed_note = False
                onset_err_ms = None
            else:
                perf_note_name = midi_to_note_name(perf["pitch"])
                perf_start_s = perf["start"]
                perf_dur_s = perf["dur"]
                perf_vel = perf["vel"]
                perf_beat, perf_measure, perf_measure_beat = get_beat_measure(perf["start"], tempo)
                onset_err_ms = (perf_start_s - ref["start"]) * 1000
                dur_ratio = perf_dur_s / ref["dur"] if ref["dur"] else None
                vel_err = perf_vel - ref["vel"] if perf_vel is not None else None
                if perf_note_name == ref_note_name:
                    alignment_status = "aligned"
                else:
                    alignment_status = "misplayed"
                    misplayed_note = True
        else:
            # Try to find a performance note at the nearest measure/beat
            min_dist = float('inf')
            nearest = None
            for (m, b), (idx_perf, perf) in perf_lookup.items():
                dist = abs((m - ref_measure) * 4 + (b - ref_beat))
                if dist < min_dist:
                    min_dist = dist
                    nearest = (idx_perf, perf, m, b)
            if nearest and min_dist >= 1:
                idx_perf, perf, m, b = nearest
                perf_part = perf["part"] if "part" in perf else None
                perf_color = perf["color"] if "color" in perf else None
                perf_note_name = midi_to_note_name(perf["pitch"])
                perf_start_s = perf["start"]
                perf_dur_s = perf["dur"]
                perf_vel = perf["vel"]
                perf_beat, perf_measure, perf_measure_beat = get_beat_measure(perf["start"], tempo)
                onset_err_ms = (perf_start_s - ref["start"]) * 1000
                dur_ratio = perf_dur_s / ref["dur"] if ref["dur"] else None
                vel_err = perf_vel - ref["vel"] if perf_vel is not None else None
                if (m < ref_measure) or (m == ref_measure and b < ref_beat):
                    alignment_status = "early"
                else:
                    alignment_status = "late"
            else:
                alignment_status = "missing"
        logging.info(f"[metrics.py] Appending row for ref idx {i_ref}: alignment_status={alignment_status}, perf_note_name={perf_note_name}, onset_err_ms={onset_err_ms}")
        rows.append({
            "pitch": ref["pitch"],
            "ref_start_s": ref["start"],
            "perf_start_s": perf_start_s,
            "onset_err_ms": onset_err_ms,
            "ref_dur_s": ref["dur"],
            "perf_dur_s": perf_dur_s,
            "dur_ratio": dur_ratio,
            "ref_vel": ref["vel"],
            "perf_vel": perf_vel,
            "vel_err": vel_err,
            "ref_note_name": ref_note_name,
            "perf_note_name": perf_note_name,
            "ref_beat": ref_beat,
            "ref_measure": ref_measure,
            "ref_measure_beat": ref_measure_beat,
            "perf_beat": perf_beat,
            "perf_measure": perf_measure,
            "perf_measure_beat": perf_measure_beat,
            "chord": chord,
            "alignment_status": alignment_status,
            "misplayed_note": misplayed_note,
            "missed_note": alignment_status == "missing",
            "ref_part": ref_part,
            "perf_part": perf_part,
            "ref_color": ref_color,
            "perf_color": perf_color,
            "perf_pitch": perf_pitch
        })
    import logging
    logging.info(f"[metrics.py] rows before DataFrame: count={len(rows)}")
    for i, row in enumerate(rows):
        logging.info(f"[metrics.py] Row {i}: {row}")
    if len(rows) > 0:
        logging.info(f"[metrics.py] First row: {rows[0]}")
        if len(rows) > 1:
            logging.info(f"[metrics.py] Second row: {rows[1]}")
        if len(rows) == 1:
            logging.warning("[metrics.py] Only one row constructed for per_note_df! This may indicate a bug in matching or row construction.")
    else:
        logging.warning("[metrics.py] No rows constructed for per_note_df!")
    per_note_df = pd.DataFrame(rows)
    logging.info(f"[metrics.py] per_note_df after row construction: shape={per_note_df.shape}\n{per_note_df.head(10)}")
    # Reorder columns as specified
    col_order = [
        "ref_note_name", "perf_note_name", "chord", "ref_measure_beat", "ref_start_s", "perf_start_s", "onset_err_ms",
        "ref_dur_s", "perf_dur_s", "dur_ratio", "ref_vel", "perf_vel", "vel_err",
        "ref_beat", "ref_measure", "pitch", "perf_beat", "perf_measure", "perf_measure_beat",
        "alignment_status", "misplayed_note", "missed_note",
        "ref_part", "perf_part", "ref_color", "perf_color", "perf_pitch"
    ]
    # Only keep columns that exist in the DataFrame (in case of missing columns)
    col_order = [c for c in col_order if c in per_note_df.columns]
    per_note_df = per_note_df[col_order]
    # Remove any blank rows (all NaN or empty)
    per_note_df = per_note_df.dropna(how="all").reset_index(drop=True)
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
