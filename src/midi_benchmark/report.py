"""
Reporting utilities: save CSVs and make plots.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

# Suppress matplotlib DEBUG logs (especially findfont)
import logging as pylogging
pylogging.getLogger('matplotlib').setLevel(pylogging.WARNING)


def save_csvs(per_note_df: pd.DataFrame, summary_dict: dict, out_dir: str) -> None:
    # DIAGNOSTIC LOGGING: Log the input DataFrame and summary dict
    import logging
    logging.warning("[DIAG] save_csvs called: per_note_df shape=%s, columns=%s", per_note_df.shape, list(per_note_df.columns))
    try:
        logging.warning("[DIAG] per_note_df.head(10):\n%s", per_note_df.head(10).to_string())
    except Exception as e:
        logging.warning("[DIAG] Could not print per_note_df.head(10): %s", e)
    logging.warning("[DIAG] summary_dict keys: %s", list(summary_dict.keys()))
    try:
        logging.warning("[DIAG] summary_dict sample: %s", {k: summary_dict[k] for k in list(summary_dict)[:10]})
    except Exception as e:
        logging.warning("[DIAG] Could not print summary_dict sample: %s", e)
    """
    Save per-note and summary CSVs to out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)
    # Rainbow CSV header for per_note_comparison.csv
    # Desired column order
    ordered_cols = [
        "ref_note_name", "perf_note_name", "chord", "ref_measure_beat", "ref_start_s", "perf_start_s", "onset_err_ms",
        "ref_dur_s", "perf_dur_s", "dur_ratio", "ref_vel", "perf_vel", "vel_err",
        "ref_beat", "ref_measure", "pitch", "perf_beat", "perf_measure", "perf_measure_beat",
        "alignment_status", "misplayed_note", "missed_note",
        "ref_part", "perf_part", "ref_color", "perf_color", "perf_pitch"
    ]
    per_note_definitions = [
        ("ref_note_name", "Reference note name (e.g., C4)"),
        ("perf_note_name", "Performed note name (e.g., D#4)"),
        ("ref_beat", "Reference beat in measure (1-4, 4/4 assumed)"),
        ("ref_measure", "Reference measure number (starting at 1)"),
        ("ref_measure_beat", "Reference measure.beat (e.g., 1.4 for measure 1 beat 4)"),
        ("pitch", "MIDI note number (e.g., 60 = Middle C)"),
        ("ref_start_s", "Reference note start time (seconds)"),
        ("perf_start_s", "Performed note start time (seconds)"),
        ("onset_err_ms", "Onset error (ms, + = late, - = early)"),
        ("onset_whole_note_frac", "Onset error as a fraction of a whole note (e.g., 0.25 = quarter note late)"),
        ("ref_dur_s", "Reference note duration (seconds)"),
        ("perf_dur_s", "Performed note duration (seconds)"),
        ("dur_ratio", "Performed/Reference duration ratio"),
        ("ref_vel", "Reference note velocity (0-127)"),
        ("perf_vel", "Performed note velocity (0-127)"),
        ("vel_err", "Velocity error (performed - reference)"),
        ("perf_beat", "Performed beat in measure (1-4, 4/4 assumed)"),
        ("perf_measure", "Performed measure number (starting at 1)"),
        ("perf_measure_beat", "Performed measure.beat (e.g., 2.3 for measure 2 beat 3)"),
        ("chord", "Chord or Roman numeral (per measure, reference, if available)"),
    ("alignment_status", "Alignment status: 'aligned', 'early', 'late', or 'missing' (musically meaningful alignment)"),
    ("misplayed_note", "True if perf_note_name != ref_note_name, else False"),
    ("missed_note", "True if the reference note was not matched to any performance note"),
    ("ref_part", "Reference part: 'bass' or 'harmony' (split by user-defined note)"),
    ("perf_part", "Performed part: 'bass' or 'harmony' (split by user-defined note)"),
    ("ref_color", "Reference note color (if available from Ableton)"),
    ("perf_color", "Performed note color (if available from Ableton)")
    ]
    # Remove any blank rows (all NaN or empty) before writing
    import logging
    # Log the raw per_note_df before cleaning
    import logging
    logging.info(f"Raw per_note_df before cleaning: shape={per_note_df.shape}\n{per_note_df.head(10)}")
    # Remove any blank rows (all NaN or all empty strings)
    per_note_df_clean = per_note_df.dropna(how="all").replace(r'^\s*$', pd.NA, regex=True).dropna(how="all").reset_index(drop=True)
    # Consolidate verbose flag: if logging is enabled, all logs are written, else none
    verbose = os.environ.get("MIDI_BENCH_VERBOSE", "0") in ("1", "True", "true", "yes")
    save_verbose_log = verbose  # Only write verbose log if verbose is enabled
    verbose_log_path = os.path.join(out_dir, "per_note_verbose.log")
    # Purge the verbose log before writing
    if save_verbose_log:
        with open(verbose_log_path, "w", encoding="utf-8") as f:
            f.write("")
    def write_verbose(msg):
        if save_verbose_log:
            with open(verbose_log_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        if verbose:
            print(msg)
    if per_note_df_clean.empty:
        logging.warning("per_note_comparison.csv DataFrame is EMPTY. No rows to write.")
        write_verbose("[MIDI_BENCH_VERBOSE] per_note_comparison.csv DataFrame is EMPTY. No rows to write.")
    else:
        logging.info(f"Writing per_note_comparison.csv: shape={per_note_df_clean.shape}\n{per_note_df_clean.head()}")
        write_verbose(f"[MIDI_BENCH_VERBOSE] Writing per_note_comparison.csv: shape={per_note_df_clean.shape}")
        row_count = 0
        for idx, row in per_note_df_clean.iterrows():
            write_verbose(f"[MIDI_BENCH_VERBOSE] Row {idx}: {row.to_dict()}")
            row_count += 1
        write_verbose(f"[MIDI_BENCH_VERBOSE] Total rows written: {row_count}")
        if row_count == 1:
            logging.warning("[MIDI_BENCH_VERBOSE] Only one row written to per_note_comparison.csv. This may indicate a bug in metrics or matching.")
    # Ensure all columns in ordered_cols exist in the DataFrame
    for col in ordered_cols:
        if col not in per_note_df_clean.columns:
            per_note_df_clean[col] = None
    per_note_path = os.path.join(out_dir, "per_note_comparison.csv")
    per_note_df_clean[ordered_cols].to_csv(per_note_path, index=False, encoding="utf-8")

    # Rainbow CSV header for summary.csv (one per line)
    summary_definitions = [
        ("ref_notes", "Number of notes in the reference MIDI"),
        ("perf_notes", "Number of notes in the performed MIDI"),
        ("matched", "Number of reference notes matched to a performed note"),
        ("missed", "Reference notes with no matching performed note"),
        ("extra", "Performed notes with no matching reference note"),
        ("match_rate_%", "Percentage of reference notes matched"),
        ("onset_err_ms_mean", "Mean absolute onset error (ms)"),
        ("onset_err_ms_median", "Median absolute onset error (ms)"),
        ("onset_err_ms_sd", "Standard deviation of onset error (ms)"),
        ("dur_ratio_mean", "Mean duration ratio"),
        ("dur_ratio_median", "Median duration ratio"),
        ("dur_ratio_sd", "Standard deviation of duration ratio"),
        ("vel_err_mean", "Mean velocity error"),
        ("vel_err_median", "Median velocity error"),
        ("vel_err_sd", "Standard deviation of velocity error"),
        ("timing_within_20ms_%", "Percent of matched notes with onset error ≤ 20 ms"),
        ("timing_within_40ms_%", "Percent of matched notes with onset error ≤ 40 ms"),
        ("timing_within_60ms_%", "Percent of matched notes with onset error ≤ 60 ms")
    ]
    summary_path = os.path.join(out_dir, "summary.csv")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("label,definition,value\n")
        for col, desc in summary_definitions:
            val = summary_dict.get(col, "")
            f.write(f"{col},\"{desc}\",{val}\n")

def make_plots(per_note_df: pd.DataFrame, out_dir: str) -> None:
    """
    Make and save plots to out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)
    if per_note_df.empty or "onset_err_ms" not in per_note_df.columns:
        return
    # Histogram of onset_err_ms with secondary x-axis for whole note fractions
    fig, ax1 = plt.subplots()
    n, bins, patches = ax1.hist(per_note_df["onset_err_ms"], bins=30)
    ax1.set_xlabel("Onset Error (ms)")
    ax1.set_ylabel("Count")
    ax1.set_title("Onset Error Histogram")

    # Secondary x-axis: whole note fraction
    # Get tempo from per_note_df if available, else default to 120
    tempo = 120.0
    if hasattr(per_note_df, 'midi_tempo'):
        tempo = getattr(per_note_df, 'midi_tempo', 120.0)
    elif hasattr(per_note_df, 'tempo'):
        tempo = getattr(per_note_df, 'tempo', 120.0)
    sec_per_beat = 60.0 / tempo if tempo > 0 else 0.5
    sec_per_whole = sec_per_beat * 4
    def ms_to_whole_note_frac(ms):
        return ms / 1000.0 / sec_per_whole if sec_per_whole > 0 else 0.0
    def whole_note_frac_to_ms(frac):
        return frac * sec_per_whole * 1000.0
    ax2 = ax1.secondary_xaxis('top', functions=(ms_to_whole_note_frac, whole_note_frac_to_ms))
    ax2.set_xlabel("Onset Error (fraction of whole note)")
    plt.savefig(os.path.join(out_dir, "onset_hist.png"))
    plt.close()
    # Cumulative mean absolute and signed onset error, with secondary y-axis for whole note fractions
    fig, ax1 = plt.subplots()
    abs_err = per_note_df["onset_err_ms"].abs().expanding().mean()
    signed_err = per_note_df["onset_err_ms"].expanding().mean()
    idx = range(1, len(abs_err) + 1)
    l1 = ax1.plot(idx, abs_err.values, label="Mean Absolute Onset Error", color="tab:blue")
    l2 = ax1.plot(idx, signed_err.values, label="Mean Onset Error (signed)", color="tab:orange")
    ax1.set_xlabel("Note Index")
    ax1.set_ylabel("Onset Error (ms)")
    ax1.set_title("Cumulative Mean Onset Error Over Notes")
    # Secondary y-axis: whole note fraction
    tempo = 120.0
    if hasattr(per_note_df, 'midi_tempo'):
        tempo = getattr(per_note_df, 'midi_tempo', 120.0)
    elif hasattr(per_note_df, 'tempo'):
        tempo = getattr(per_note_df, 'tempo', 120.0)
    sec_per_beat = 60.0 / tempo if tempo > 0 else 0.5
    sec_per_whole = sec_per_beat * 4
    def ms_to_whole_note_frac(ms):
        return ms / 1000.0 / sec_per_whole if sec_per_whole > 0 else 0.0
    def whole_note_frac_to_ms(frac):
        return frac * sec_per_whole * 1000.0
    ax2 = ax1.secondary_yaxis('right', functions=(ms_to_whole_note_frac, whole_note_frac_to_ms))
    ax2.set_ylabel("Onset Error (fraction of whole note)")
    # Add legend
    lines = l1 + l2
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="upper right")
    plt.savefig(os.path.join(out_dir, "onset_cumabs_timeline.png"))
    plt.close()
