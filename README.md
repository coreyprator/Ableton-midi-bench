<<<<<<< HEAD
# Ableton MIDI Bench

A Windows-friendly Python tool to benchmark MIDI performance accuracy against a reference clip exported from Ableton Live.

## 1) Install

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## 2) Ableton export checklist
- Place your reference clip on its own MIDI track.
- If groove matters, right-click the clip and Commit the groove.
- Select the clip and use File → Export MIDI Clip…
- Save to `data/reference_*.mid`
- Do the same for your recorded take to `data/performance_*.mid`

## 3) Run examples

```powershell
midi-bench compare ^
  --ref data/reference_melody.mid ^
  --perf data/performance_melody_take1.mid ^
  --out runs/melody_take1 ^
  --onset-tol-list "20,40,60"
```

## 4) Outputs
- runs/<name>/per_note_comparison.csv (CSV with header and data, no comment lines)
- runs/<name>/summary.csv
- runs/<name>/onset_hist.png
- runs/<name>/onset_cumabs_timeline.png

## 5) Interpreting results

- **Match rate**: Percent of reference notes you hit with correct pitch.
- **Onset error stats**: Onset error is the difference between the performed note's start time and the reference note's start time. Negative means early, positive means late. Lower is better.
- **Onset Error Histogram**: Shows the distribution of onset errors (in ms) for each matched note. X-axis is onset error in milliseconds; Y-axis is the count of notes with that error. This helps visualize your timing accuracy and consistency.
- **Onset error as a fraction of a whole note**: The CSV includes `onset_whole_note_frac`, which is the onset error in seconds divided by the duration of a whole note (based on reference tempo). For example, if a quarter note is 0.5s, a whole note is 2.0s, so a 0.5s late note is 0.25 of a whole note (a quarter note late). This gives a musical sense of how far off you are.
- **Cumulative mean absolute onset error**: This is a running average of the absolute onset error as you progress through the notes. For each note n, it is the mean of the absolute onset errors for notes 1 to n. The curve can go up or down: if you play later notes with smaller errors, the running mean can decrease. It reflects your average accuracy up to each note, not a total that only increases.
- **Duration ratio**: Near 1.0 means you sustain like the reference.
- **Velocity error**: Near 0 means similar dynamics.
- **Timing within buckets**: Shows the percent of notes within certain timing error thresholds (e.g., 20ms, 40ms, 60ms) for a quick feel for tightness.

## 6) Tips for Girl from Ipanema
- Export the comping with groove committed if you want grading on the bossa feel.
- Loop 4–8 bars in Live, record a take, export, run midi-bench, compare runs over time.

## 7) Roadmap
- Section labels by bar range
- Swing ratio analysis
- Track filtering by instrument program or channel
- Optional .als parsing in a future version
=======
# Ableton-midi-bench
A Windows-friendly Python tool to benchmark MIDI performance accuracy against a reference clip exported from Ableton Live.
>>>>>>> c42f9d35bf8435afe87aafb62d87c134264c1e94
