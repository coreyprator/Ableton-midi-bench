-- Create a view for cumulative absolute onset error timeline with onset_err_ms and abs_onset_err_ms
IF OBJECT_ID('dbo.vw_onset_cumabs_timeline', 'V') IS NOT NULL
    DROP VIEW dbo.vw_onset_cumabs_timeline;
GO

CREATE VIEW dbo.vw_onset_cumabs_timeline AS
SELECT
    sort_time,
    onset_err_ms,
    abs_onset_err_ms,
    SUM(CAST(abs_onset_err_ms AS float)) OVER (
        ORDER BY sort_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cum_abs_onset_err_ms,
    SUM(CAST(onset_err_ms AS float)) OVER (
        ORDER BY sort_time
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cum_onset_err_ms
FROM dbo.vw_per_note_comparison
WHERE alignment_status = 'matched';
GO

-- To preview the data:
SELECT  * FROM dbo.vw_onset_cumabs_timeline ORDER BY sort_time;