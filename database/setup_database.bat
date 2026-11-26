@echo off
setlocal
rem Is this a scam? -- builds the accounts database on Laragon's MySQL.
rem
rem How to use: open Laragon, click "Start All", then double-click this file.
rem It runs schema.sql, which creates the database isthisascam and its three
rem tables (users, scan_results, game_attempts). Running it again is safe:
rem nothing that already exists is dropped or changed.
rem
rem Made for Laragon 6.0.0, which ships MySQL 8.0.30 (root, no password).

cd /d "%~dp0"

set "MYSQL="
if exist "C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysql.exe" set "MYSQL=C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysql.exe"
if not defined MYSQL for /d %%D in ("C:\laragon\bin\mysql\mysql-*") do if exist "%%D\bin\mysql.exe" set "MYSQL=%%D\bin\mysql.exe"
if not defined MYSQL goto :nomysql

"%MYSQL%" -h 127.0.0.1 -P 3306 -u root -N -e "SELECT 1" >nul 2>&1
if errorlevel 1 goto :notrunning

echo Creating the database isthisascam from schema.sql ...
"%MYSQL%" -h 127.0.0.1 -P 3306 -u root < "schema.sql"
if errorlevel 1 goto :fail

echo.
echo Check:
"%MYSQL%" -h 127.0.0.1 -P 3306 -u root -t -e "SELECT VERSION() AS mysql_version; SELECT TABLE_NAME AS table_in_isthisascam FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'isthisascam' ORDER BY TABLE_NAME; SELECT COUNT(*) AS profile_picture_columns FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'isthisascam' AND TABLE_NAME = 'users' AND COLUMN_NAME LIKE 'avatar%%';"
echo.
echo Done. You should see 3 tables and 3 profile picture columns above.
echo The site's accounts now work at http://localhost/Final-Year-Project/web/Login.html
pause
exit /b 0

:nomysql
echo Could not find mysql.exe under C:\laragon\bin\mysql
goto :fail

:notrunning
echo MySQL is not running. Open Laragon, click "Start All", then run this file again.
goto :fail

:fail
echo.
echo Setup did not finish. Nothing was deleted.
pause
exit /b 1
