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

        # --- Add musical time columns ---
        # Assume 4/4, 120bpm if not available
        try:
            tempo = midi.get_tempo_changes()[1][0] if len(midi.get_tempo_changes()[1]) > 0 else 120.0
        except Exception:
            tempo = 120.0
        try:
            time_sig = midi.time_signature_changes[0] if midi.time_signature_changes else None
            beats_per_bar = time_sig.numerator if time_sig else 4
        except Exception:
            beats_per_bar = 4
        # Compute beat_absolute
        df["beat_absolute"] = df["start"] * (tempo / 60.0)
        df["bar_index"] = (df["beat_absolute"] // beats_per_bar).astype(int)
        df["beat_in_bar"] = df["beat_absolute"] % beats_per_bar
        df["bar_beat_label"] = df["bar_index"].astype(str) + ":" + df["beat_in_bar"].round(3).astype(str)
    return df
