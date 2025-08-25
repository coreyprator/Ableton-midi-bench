"""
Greedy pitch-aware nearest-onset matcher.
"""
from typing import List, Tuple
import numpy as np
import pandas as pd

def match_notes(ref_df: pd.DataFrame, perf_df: pd.DataFrame) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """
    Match notes by pitch and nearest onset.
    Returns (matches, missed_idx, extra_idx)
    """
    matches = []
    used_perf = set()
    missed_idx = []
    for i, ref_row in ref_df.iterrows():
        pitch = ref_row["pitch"]
        ref_start = ref_row["start"]
        # Candidates: same pitch, not already matched
        candidates = perf_df[(perf_df["pitch"] == pitch) & (~perf_df.index.isin(used_perf))]
        if not candidates.empty:
            # Find nearest onset
            onset_diffs = np.abs(candidates["start"] - ref_start)
            j = candidates.index[onset_diffs.argmin()]
            matches.append((i, j))
            used_perf.add(j)
        else:
            missed_idx.append(i)
    extra_idx = [j for j in perf_df.index if j not in used_perf]
    return matches, missed_idx, extra_idx
