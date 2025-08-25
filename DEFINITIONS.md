# Definitions: Ableton MIDI Bench Outputs

## per_note_comparison.csv Columns

- **pitch**: MIDI note number (e.g., 60 = Middle C)
- **ref_start_s**: Start time (seconds) of the reference note
- **perf_start_s**: Start time (seconds) of the performed note
- **onset_err_ms**: Difference in start time between performance and reference, in milliseconds (positive = late, negative = early)
- **ref_dur_s**: Duration (seconds) of the reference note
- **perf_dur_s**: Duration (seconds) of the performed note
- **dur_ratio**: Performed duration divided by reference duration (1.0 = same length)
- **ref_vel**: Velocity (loudness) of the reference note (0–127)
- **perf_vel**: Velocity (loudness) of the performed note (0–127)
- **vel_err**: Difference in velocity (performed - reference)

## summary.csv Columns

- **ref_notes**: Number of notes in the reference MIDI
- **perf_notes**: Number of notes in the performed MIDI
- **matched**: Number of reference notes matched to a performed note (by pitch and nearest onset)
- **missed**: Reference notes with no matching performed note
- **extra**: Performed notes with no matching reference note
- **match_rate_%**: Percentage of reference notes matched
- **onset_err_ms_mean**: Mean absolute onset error (ms)
- **onset_err_ms_median**: Median absolute onset error (ms)
- **onset_err_ms_sd**: Standard deviation of onset error (ms)
- **dur_ratio_mean**: Mean duration ratio
- **dur_ratio_median**: Median duration ratio
- **dur_ratio_sd**: Standard deviation of duration ratio
- **vel_err_mean**: Mean velocity error
- **vel_err_median**: Median velocity error
- **vel_err_sd**: Standard deviation of velocity error
- **timing_within_20ms_%**: Percent of matched notes with onset error ≤ 20 ms
- **timing_within_40ms_%**: Percent of matched notes with onset error ≤ 40 ms
- **timing_within_60ms_%**: Percent of matched notes with onset error ≤ 60 ms

## Plots

- **onset_hist.png**: Histogram of onset errors (ms) — shows the distribution of timing errors between reference and performance.
- **onset_cumabs_timeline.png**: Line plot of cumulative mean absolute onset error over note index — shows how average timing accuracy evolves throughout the performance.
