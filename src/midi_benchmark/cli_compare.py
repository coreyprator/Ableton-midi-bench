"""
CLI for midi-bench compare.
"""
import sys
import click
import pandas as pd
from . import loader, matcher, metrics, report
from tabulate import tabulate
import os

def trim_df(df: pd.DataFrame, start: float = None, end: float = None) -> pd.DataFrame:
    if start is not None:
        df = df[df["start"] >= start]
    if end is not None:
        df = df[df["start"] <= end]
    return df.reset_index(drop=True)

@click.group()
def main():
    pass

@main.command()
@click.option('--ref', required=True, type=click.Path(exists=True), help='Reference MIDI file')
@click.option('--perf', required=True, type=click.Path(exists=True), help='Performance MIDI file')
@click.option('--out', required=True, type=click.Path(), help='Output directory')
@click.option('--onset-tol-list', default="20,40,60", help='Comma-separated onset tolerances in ms')
@click.option('--max-onset-ms', type=int, default=None, help='Maximum allowed onset error (ms) for matching')
@click.option('--trim-start', type=float, default=None, help='Trim start (seconds)')
@click.option('--trim-end', type=float, default=None, help='Trim end (seconds)')
@click.option('--split-note', default="B2", help='Bass/Harmony split note (e.g., B2, 47)')
def compare(ref, perf, out, onset_tol_list, max_onset_ms, trim_start, trim_end, split_note):
    import logging
    import os
    log_to_main_log = os.environ.get("MIDI_BENCH_LOG_TO_MAIN_LOG", "0") in ("1", "True", "true", "yes")
    log_handlers = []
    if log_to_main_log:
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "midi_bench_gui.log")
        log_handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    log_handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', handlers=log_handlers)
    # Suppress matplotlib DEBUG logs (especially findfont)
    try:
        import logging as pylogging
        pylogging.getLogger('matplotlib').setLevel(pylogging.WARNING)
    except Exception:
        pass
    try:
        ref_df = loader.load_notes(ref, split_note=split_note)
        logging.info(f"Loaded ref_df: shape={ref_df.shape}\n{ref_df.head()}")
        perf_df = loader.load_notes(perf, split_note=split_note)
        logging.info(f"Loaded perf_df: shape={perf_df.shape}\n{perf_df.head()}")
        if trim_start is not None or trim_end is not None:
            ref_df = trim_df(ref_df, trim_start, trim_end)
            perf_df = trim_df(perf_df, trim_start, trim_end)
            logging.info(f"After trim, ref_df: shape={ref_df.shape}")
            logging.info(f"After trim, perf_df: shape={perf_df.shape}")
        onset_tols = [int(x) for x in onset_tol_list.split(",") if x.strip()]
        matches, missed, extra = matcher.match_notes(ref_df, perf_df, max_onset_ms=max_onset_ms)
        logging.info(f"Matches: {len(matches)}, Missed: {len(missed)}, Extra: {len(extra)}")
        per_note_df, summary = metrics.compute_metrics(ref_df, perf_df, matches, onset_tols)
        logging.info(f"per_note_df shape: {per_note_df.shape}\n{per_note_df.head()}")
        logging.info(f"Summary: {summary}")
        report.save_csvs(per_note_df, summary, out)
        report.make_plots(per_note_df, out)
        print(tabulate([summary], headers="keys", floatfmt=".2f"))
        sys.exit(0)
    except Exception as e:
        import traceback
        logging.error(f"Error in compare: {e}\n{traceback.format_exc()}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
