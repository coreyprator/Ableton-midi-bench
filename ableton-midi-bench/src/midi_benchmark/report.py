"""
Reporting utilities: save CSVs and make plots.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

def save_csvs(per_note_df: pd.DataFrame, summary_dict: dict, out_dir: str) -> None:
    """
    Save per-note and summary CSVs to out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)
    per_note_df.to_csv(os.path.join(out_dir, "per_note_comparison.csv"), index=False)
    pd.DataFrame([summary_dict]).to_csv(os.path.join(out_dir, "summary.csv"), index=False)

def make_plots(per_note_df: pd.DataFrame, out_dir: str) -> None:
    """
    Make and save plots to out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)
    # Histogram of onset_err_ms
    plt.figure()
    per_note_df["onset_err_ms"].hist(bins=30)
    plt.xlabel("Onset Error (ms)")
    plt.ylabel("Count")
    plt.title("Onset Error Histogram")
    plt.savefig(os.path.join(out_dir, "onset_hist.png"))
    plt.close()
    # Cumulative mean absolute onset error
    plt.figure()
    abs_err = per_note_df["onset_err_ms"].abs().expanding().mean()
    plt.plot(abs_err.values)
    plt.xlabel("Note Index")
    plt.ylabel("Cumulative Mean Absolute Onset Error (ms)")
    plt.title("Cumulative Mean Absolute Onset Error Over Notes")
    plt.savefig(os.path.join(out_dir, "onset_cumabs_timeline.png"))
    plt.close()
