"""
Loader for MIDI files to DataFrame.
"""
from typing import Any
import pandas as pd
import pretty_midi
import re

def load_notes(path: str, split_note: str = "B2") -> pd.DataFrame:
    """
    Load all notes from a MIDI file into a DataFrame.
    Columns: ["pitch","start","end","dur","vel","channel","program"]
    Sorted by ["start","pitch"].
    Adds 'part' (bass/harmony) and 'color' columns if possible.
    """
    midi = pretty_midi.PrettyMIDI(path)
    notes = []
    # Helper to convert note name to midi number
    def note_name_to_midi(note):
        if isinstance(note, int):
            return note
        match = re.match(r"([A-Ga-g]#?)(-?\d+)", note)
        if match:
            name, octave = match.groups()
            name = name.upper()
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            midi_num = note_names.index(name) + (int(octave) + 1) * 12
            return midi_num
        try:
            return int(note)
        except Exception:
            return 47  # default B2
    split_midi = note_name_to_midi(split_note)
    for inst in midi.instruments:
        for n in inst.notes:
            # Try to get color if present (Ableton Live 11+)
            color = None
            if hasattr(n, 'color'):
                color = n.color
            notes.append({
                "pitch": n.pitch,
                "start": n.start,
                "end": n.end,
                "dur": n.end - n.start,
                "vel": n.velocity,
                "channel": 0,  # pretty_midi.Instrument has no channel attribute
                "program": inst.program,
                "part": "bass" if n.pitch <= split_midi else "harmony",
                "color": color
            })
    df = pd.DataFrame(notes)
    if not df.empty:
        df = df.sort_values(["start", "pitch"]).reset_index(drop=True)
    return df
