"""
Loader for MIDI files to DataFrame.
"""
from typing import Any
import pandas as pd
import pretty_midi


def load_notes(path: str) -> pd.DataFrame:
    """
    Load all notes from a MIDI file into a DataFrame.
    Columns: ["pitch","start","end","dur","vel","channel","program"]
    Sorted by ["start","pitch"].
    """
    midi = pretty_midi.PrettyMIDI(path)
    notes = []
    for inst in midi.instruments:
        for n in inst.notes:
            notes.append({
                "pitch": n.pitch,
                "start": n.start,
                "end": n.end,
                "dur": n.end - n.start,
                "vel": n.velocity,
                "channel": inst.channel if inst.channel is not None else 0,
                "program": inst.program
            })
    df = pd.DataFrame(notes)
    if not df.empty:
        df = df.sort_values(["start", "pitch"]).reset_index(drop=True)
    return df
