USE [ableton-midi-bench];
GO

IF COL_LENGTH('dbo.reference_notes','source_file_name') IS NULL
    ALTER TABLE dbo.reference_notes ADD
        source_file_name  nvarchar(300) NULL,
        source_file_mtime datetime2(3)  NULL;

IF COL_LENGTH('dbo.performance_notes','source_file_name') IS NULL
    ALTER TABLE dbo.performance_notes ADD
        source_file_name  nvarchar(300) NULL,
        source_file_mtime datetime2(3)  NULL;

-- Helpful for filtering by session/file
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_ref_source_mtime' AND object_id=OBJECT_ID('dbo.reference_notes'))
    CREATE INDEX IX_ref_source_mtime ON dbo.reference_notes (source_file_mtime, source_file_name);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_perf_source_mtime' AND object_id=OBJECT_ID('dbo.performance_notes'))
    CREATE INDEX IX_perf_source_mtime ON dbo.performance_notes (source_file_mtime, source_file_name);
