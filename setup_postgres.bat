@echo off
echo ====================================================
echo   Website Monitor PostgreSQL Setup Helper (Windows)
echo ====================================================
echo.

REM Check if PostgreSQL is installed
where psql >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PostgreSQL is not installed or not in your PATH!
    echo Please install PostgreSQL from https://www.postgresql.org/download/windows/
    echo After installation, make sure it's in your PATH and run this script again.
    echo.
    echo You may need to restart your computer after installation.
    pause
    exit /B 1
)

echo PostgreSQL is installed.
echo.

echo --------------------------------------------------
echo Would you like to set up the database with default credentials?
echo This will:
echo 1. Create a PostgreSQL user 'postgres' with password 'postgres'
echo 2. Create a database 'website_monitor'
echo 3. Configure the application to use these credentials
echo.
set /p answer="Proceed? (y/n): "

if /i "%answer%" NEQ "y" (
    echo Setup cancelled. You can manually configure the database settings in config.json
    pause
    exit /B 0
)

REM Create the database
echo Creating 'website_monitor' database...
psql -U postgres -c "CREATE DATABASE website_monitor;" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Database created successfully.
) else (
    echo Database may already exist or there was a problem.
)

REM Verify the connection works
echo Verifying database connection...
psql -U postgres -d website_monitor -c "SELECT 1" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Database connection successful!
) else (
    echo Could not connect to the database.
    echo Please check your PostgreSQL configuration.
    echo You may need to update the pg_hba.conf file to allow password authentication.
    pause
    exit /B 1
)

echo --------------------------------------------------
echo PostgreSQL setup completed successfully!
echo.
echo Next steps:
echo 1. Run the Python setup script: python setup_db.py
echo 2. Start the application: python src\main.py
echo ====================================================
pause