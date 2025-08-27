ALTER VIEW dbo.note_comparison AS
SELECT 

    CASE
      WHEN p.start_s IS NULL THEN 'missed'
      WHEN r.start_s IS NULL THEN 'stray'
      WHEN p.start_s - r.start_s > 0.25 THEN 'late'
      WHEN p.start_s - r.start_s < -0.25 THEN 'early'
      ELSE 'on time'
    END AS timing_status,

    p.start_s - r.start_s AS Time_delta,

    ROUND(r.beat_in_bar * 2, 0) / 2.0 AS ref_bar_beat,
    r.note_name + CAST(r.octave AS varchar) AS Ref_note,
    ROUND(p.beat_in_bar * 2, 0) / 2.0 AS perf_bar_beat,
    p.note_name + CAST(p.octave AS varchar) AS Perf_note,
    CASE WHEN r.pitch <= 47 THEN 'bass' ELSE 'harmony' END AS ref_part,
    r.start_s AS ref_start,
    p.start_s AS perf_start,
    r.bar_index AS ref_bar,
    p.bar_index AS perf_bar,
    r.beat_in_bar AS ref_beat


FROM dbo.reference_notes r
FULL OUTER JOIN dbo.performance_notes p
  ON p.bar_index = r.bar_index 
  AND ROUND(p.beat_in_bar * 2, 0) / 2.0 = ROUND(r.beat_in_bar * 2, 0) / 2.0
  AND CASE WHEN r.pitch <= 47 THEN 'bass' ELSE 'harmony' END = CASE WHEN p.pitch <= 47 THEN 'bass' ELSE 'harmony' END
  AND p.pitch = r.pitch


/*


SELECT
  COUNT(CASE WHEN timing_status = 'on time' THEN 1 END) AS on_time_count,
  COUNT(CASE WHEN timing_status = 'missed' THEN 1 END) AS missed_count,
  COUNT(CASE WHEN timing_status = 'stray' THEN 1 END) AS stray_count,
  COUNT(CASE WHEN timing_status = 'early' THEN 1 END) AS early_count,
  COUNT(CASE WHEN timing_status = 'late' THEN 1 END) AS late_count,
  AVG(Time_delta) AS avg_time_delta
FROM dbo.note_comparison


select * from note_comparison order by ISNULL(ref_bar,perf_bar), ISNULL(ref_beat,perf_bar_beat), Ref_note, ref_part


SELECT TOP 10 pitch, start_s, end_s, dur_s, note_name, octave
FROM dbo.reference_notes ORDER BY start_s;



*/

-- Row counts
SELECT 'reference_notes' AS table_name, COUNT(*) AS rows FROM dbo.reference_notes
UNION ALL
SELECT 'performance_notes', COUNT(*) FROM dbo.performance_notes;

-- Quick peek
SELECT TOP 10 * FROM dbo.reference_notes ORDER BY start_s, pitch;
SELECT TOP 10 * FROM dbo.performance_notes ORDER BY start_s, pitch;

-- Latest source metadata
SELECT TOP 5 source_filename, source_file_mtime, COUNT(*) AS rows
FROM dbo.reference_notes
GROUP BY source_filename, source_file_mtime
ORDER BY source_file_mtime DESC;

/*
CREATE INDEX IX_ref_start_pitch ON dbo.reference_notes (start_s, pitch);
CREATE INDEX IX_perf_start_pitch ON dbo.performance_notes (start_s, pitch);
CREATE INDEX IX_ref_barbeat ON dbo.reference_notes (bar_index, beat_in_bar);
CREATE INDEX IX_perf_barbeat ON dbo.performance_notes (bar_index, beat_in_bar);
*/

/*
CREATE OR ALTER VIEW dbo.vw_notes_min
AS
SELECT
  'ref' AS src, pitch, start_s, end_s, dur_s, velocity, bar_index, beat_in_bar, source_filename
FROM dbo.reference_notes
UNION ALL
SELECT
  'perf', pitch, start_s, end_s, dur_s, velocity, bar_index, beat_in_bar, source_filename
FROM dbo.performance_notes;
*/

select * from dbo.vw_notes_min order by start_s, pitch;
