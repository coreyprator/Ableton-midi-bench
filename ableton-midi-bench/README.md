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
- runs/<name>/per_note_comparison.csv
- runs/<name>/summary.csv
- runs/<name>/onset_hist.png
- runs/<name>/onset_cumabs_timeline.png

## 5) Interpreting results
- Match rate is the percent of reference notes you hit with correct pitch.
- Onset error stats are in ms. Lower is better.
- Duration ratio near 1.0 means you sustain like the reference.
- Velocity error near 0 means similar dynamics.
- Timing within buckets give quick feel for tightness.

## 6) Tips for Girl from Ipanema
- Export the comping with groove committed if you want grading on the bossa feel.
- Loop 4–8 bars in Live, record a take, export, run midi-bench, compare runs over time.

## 7) Roadmap
- Section labels by bar range
- Swing ratio analysis
- Track filtering by instrument program or channel
- Optional .als parsing in a future version
