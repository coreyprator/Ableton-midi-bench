"""
Smoke test for midi_benchmark matcher and metrics.
"""
import pretty_midi
import numpy as np
import pandas as pd
from midi_benchmark import matcher, metrics

def make_tiny_midi():
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    # Two notes, C4 and D4
    inst.notes.append(pretty_midi.Note(velocity=64, pitch=60, start=0.0, end=1.0))
    inst.notes.append(pretty_midi.Note(velocity=70, pitch=62, start=1.0, end=2.0))
    midi.instruments.append(inst)
    return midi

def midi_to_df(midi):
    notes = []
    for inst in midi.instruments:
        for n in inst.notes:
            notes.append({
                "pitch": n.pitch,
                "start": n.start,
                "end": n.end,
                "dur": n.end - n.start,
                "vel": n.velocity,
                "channel": 0,  # pretty_midi.Instrument has no channel attribute
                "program": inst.program
            })
    df = pd.DataFrame(notes)
    if not df.empty:
        df = df.sort_values(["start", "pitch"]).reset_index(drop=True)
    return df

def test_match_and_metrics():
    ref_midi = make_tiny_midi()
    perf_midi = make_tiny_midi()
    ref_df = midi_to_df(ref_midi)
    perf_df = midi_to_df(perf_midi)
    matches, missed, extra = matcher.match_notes(ref_df, perf_df)
    per_note_df, summary = metrics.compute_metrics(ref_df, perf_df, matches)
    assert len(matches) == 2
    assert summary["matched"] == 2
    assert "onset_err_ms_mean" in summary
    assert "dur_ratio_mean" in summary
    assert "vel_err_mean" in summary
    print("Smoke test passed.")

if __name__ == "__main__":
    test_match_and_metrics()
