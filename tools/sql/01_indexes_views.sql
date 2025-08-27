-- Create indexes for fast note lookup
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'IX_ref_start_pitch')
    CREATE INDEX IX_ref_start_pitch ON dbo.reference_notes([start], pitch);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'IX_perf_start_pitch')
    CREATE INDEX IX_perf_start_pitch ON dbo.performance_notes([start], pitch);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'IX_ref_barbeat')
    CREATE INDEX IX_ref_barbeat ON dbo.reference_notes(bar_beat_label);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'IX_perf_barbeat')
    CREATE INDEX IX_perf_barbeat ON dbo.performance_notes(bar_beat_label);
GO

-- Create or alter view for minimal note info
IF OBJECT_ID('dbo.vw_notes_min', 'V') IS NOT NULL
    DROP VIEW dbo.vw_notes_min;
GO
CREATE VIEW dbo.vw_notes_min AS
SELECT n.id, n.pitch, n.[start], n.[end], n.dur, n.bar_beat_label, n.provenance_path, n.provenance_loaded_at
FROM dbo.reference_notes n
UNION ALL
SELECT n.id, n.pitch, n.[start], n.[end], n.dur, n.bar_beat_label, n.provenance_path, n.provenance_loaded_at
FROM dbo.performance_notes n;
GO
