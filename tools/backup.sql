-- Template used by backup_db.ps1
-- Tokens: {{DB_NAME}}, {{BAK_PATH}}
-- NOTE: BACKUP DATABASE is supported on SQL Server Express. LocalDB support can vary by version.
-- If you hit issues on LocalDB, consider migrating the DB to .\SQLEXPRESS or using a bacpac export.

USE master;
GO
BACKUP DATABASE [{{DB_NAME}}]
TO DISK = N'{{BAK_PATH}}'
WITH INIT, COPY_ONLY, NAME = N'{{DB_NAME}} full backup';
GO
