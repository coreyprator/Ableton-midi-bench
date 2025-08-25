"""
Greedy pitch-aware nearest-onset matcher.
"""
from typing import List, Tuple
import numpy as np
import pandas as pd

def match_notes(ref_df: pd.DataFrame, perf_df: pd.DataFrame, max_onset_ms: int = None) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """
    Match notes by pitch and nearest onset, with optional max onset error (ms).
    Enforces Baseline vs. Harmony matching: only match notes if both are in the same part (bass/harmony).
    Returns (matches, missed_idx, extra_idx)
    """
    import logging
    matches = []
    missed_idx = []
    # Track used performance notes per (beat, part) to prevent double-matching in chords
    used_perf_by_beat_part = set()
    def get_beat_measure(start_s, tempo=120.0):
        beats_per_sec = tempo / 60.0
        beat = start_s * beats_per_sec
        measure = int(beat // 4) + 1
        beat_in_measure = int(beat % 4) + 1
        return (measure, beat_in_measure)

    # Try to get tempo from ref_df if present
    tempo = 120.0
    if hasattr(ref_df, 'midi_tempo'):
        tempo = getattr(ref_df, 'midi_tempo', 120.0)
    elif hasattr(ref_df, 'tempo'):
        tempo = getattr(ref_df, 'tempo', 120.0)

    for i, ref_row in ref_df.iterrows():
        pitch = ref_row["pitch"]
        ref_start = ref_row["start"]
        ref_part = ref_row.get("part", None)
        ref_measure, ref_beat = get_beat_measure(ref_start, tempo)
        # Only consider candidates in the same part (bass/harmony)
        candidates = perf_df[(perf_df["pitch"] == pitch)]
        if ref_part is not None:
            if "part" in candidates.columns:
                candidates = candidates[candidates["part"] == ref_part]
            else:
                logging.warning(f"[matcher] perf_df missing 'part' column for pitch {pitch}, skipping match.")
                candidates = candidates.iloc[0:0]  # Empty
        # Filter out performance notes already matched for this (measure, beat, part)
        filtered_candidates = []
        for idx, cand in candidates.iterrows():
            perf_measure, perf_beat = get_beat_measure(cand["start"], tempo)
            perf_part = cand.get("part", None)
            key = (perf_measure, perf_beat, perf_part)
            if key not in used_perf_by_beat_part:
                filtered_candidates.append((idx, cand, perf_measure, perf_beat, perf_part))
        if filtered_candidates:
            # Find candidate with nearest onset
            onset_diffs = [abs(cand[1]["start"] - ref_start) for cand in filtered_candidates]
            min_idx = int(np.argmin(onset_diffs))
            idx_perf, cand, perf_measure, perf_beat, perf_part = filtered_candidates[min_idx]
            min_diff = onset_diffs[min_idx]
            min_diff_ms = min_diff * 1000
            if max_onset_ms is not None and min_diff_ms > max_onset_ms:
                missed_idx.append(i)
            else:
                matches.append((i, idx_perf))
                used_perf_by_beat_part.add((perf_measure, perf_beat, perf_part))
        else:
            missed_idx.append(i)
    # Extra performance notes are those not matched at all
    matched_perf_indices = set(j for _, j in matches)
    extra_idx = [j for j in perf_df.index if j not in matched_perf_indices]
    return matches, missed_idx, extra_idx
