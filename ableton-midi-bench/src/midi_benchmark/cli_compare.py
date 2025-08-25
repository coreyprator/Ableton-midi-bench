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
@click.option('--trim-start', type=float, default=None, help='Trim start (seconds)')
@click.option('--trim-end', type=float, default=None, help='Trim end (seconds)')
def compare(ref, perf, out, onset_tol_list, trim_start, trim_end):
    try:
        ref_df = loader.load_notes(ref)
        perf_df = loader.load_notes(perf)
        if trim_start is not None or trim_end is not None:
            ref_df = trim_df(ref_df, trim_start, trim_end)
            perf_df = trim_df(perf_df, trim_start, trim_end)
        onset_tols = [int(x) for x in onset_tol_list.split(",") if x.strip()]
        matches, missed, extra = matcher.match_notes(ref_df, perf_df)
        per_note_df, summary = metrics.compute_metrics(ref_df, perf_df, matches, onset_tols)
        report.save_csvs(per_note_df, summary, out)
        report.make_plots(per_note_df, out)
        print(tabulate([summary], headers="keys", floatfmt=".2f"))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
