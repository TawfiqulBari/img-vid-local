@echo off
REM ============================================================================
REM Image-to-Video Generator - Build and Package Script
REM ============================================================================
REM
REM This script must be run from Windows (not WSL)
REM Run this from the project root directory
REM
REM ============================================================================

echo.
echo ============================================================================
echo Image-to-Video Generator - Build and Package
echo ============================================================================
echo.

cd /d "%~dp0"

REM ============================================================================
REM Step 1: Build C# Application
REM ============================================================================

echo Step 1: Building C# Application...
echo.

cd VideoGenerator

echo Restoring NuGet packages...
dotnet restore
if %errorlevel% neq 0 (
    echo ERROR: Failed to restore packages
    pause
    exit /b 1
)

echo Building Release configuration...
dotnet build --configuration Release --no-restore
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ✓ Build completed successfully
echo.

cd ..

REM ============================================================================
REM Step 2: Create Release Directory Structure
REM ============================================================================

echo Step 2: Creating release directory structure...
echo.

if not exist "release" mkdir release
if not exist "release\bin" mkdir release\bin
if not exist "release\docs" mkdir release\docs
if not exist "release\scripts" mkdir release\scripts
if not exist "release\backend" mkdir release\backend
if not exist "release\portable" mkdir release\portable

REM ============================================================================
REM Step 3: Copy Application Files
REM ============================================================================

echo Step 3: Copying application files...
echo.

echo Copying executable and dependencies...
xcopy /E /I /Y "VideoGenerator\bin\Release\net6.0-windows\*" "release\bin\"

echo Copying backend files...
copy /Y "backend\generate.py" "release\backend\"
copy /Y "backend\download_models.py" "release\backend\"
copy /Y "backend\verify_setup.py" "release\backend\"
copy /Y "backend\test_generation.py" "release\backend\"
copy /Y "backend\requirements.txt" "release\backend\"
copy /Y "backend\models_catalog.json" "release\backend\"
copy /Y "backend\__init__.py" "release\backend\"

if exist "backend\utils" (
    xcopy /E /I /Y "backend\utils" "release\backend\utils\"
)
if exist "backend\pipelines" (
    xcopy /E /I /Y "backend\pipelines" "release\backend\pipelines\"
)
if exist "backend\services" (
    xcopy /E /I /Y "backend\services" "release\backend\services\"
)

echo Copying documentation...
if exist "README.md" copy /Y "README.md" "release\docs\"
if exist "QUICKSTART.md" copy /Y "QUICKSTART.md" "release\docs\"
if exist "TROUBLESHOOTING.md" copy /Y "TROUBLESHOOTING.md" "release\docs\"
if exist "RELEASE_NOTES.md" copy /Y "RELEASE_NOTES.md" "release\docs\"
if exist "LICENSE" copy /Y "LICENSE" "release\docs\"

echo Copying setup scripts...
if exist "scripts\setup_wsl.sh" copy /Y "scripts\setup_wsl.sh" "release\scripts\"
if exist "scripts\test_integration.sh" copy /Y "scripts\test_integration.sh" "release\scripts\"

echo.
echo ✓ Files copied successfully
echo.

REM ============================================================================
REM Step 4: Create Portable ZIP
REM ============================================================================

echo Step 4: Creating portable ZIP package...
echo.

if not exist "release\portable\temp" mkdir release\portable\temp
if not exist "release\portable\temp\ImageToVideoGenerator" mkdir release\portable\temp\ImageToVideoGenerator

echo Copying files to portable directory...
xcopy /E /I /Y "release\bin" "release\portable\temp\ImageToVideoGenerator\bin\"
xcopy /E /I /Y "release\backend" "release\portable\temp\ImageToVideoGenerator\backend\"
xcopy /E /I /Y "release\docs" "release\portable\temp\ImageToVideoGenerator\docs\"
xcopy /E /I /Y "release\scripts" "release\portable\temp\ImageToVideoGenerator\scripts\"

REM Create README for portable version
echo Image-to-Video Generator - Portable Version > "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo ============================================ >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo. >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo Version: 1.0.0 >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo Package Type: Portable (No Installation Required) >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo. >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo QUICK START >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo ----------- >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo. >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo 1. Extract this entire folder >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo 2. Install .NET 6.0 Desktop Runtime >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo 3. Install WSL 2 with Ubuntu 22.04 >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo 4. Run setup: bash scripts/setup_wsl.sh >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo 5. Download models: python backend/download_models.py >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo 6. Run: bin\VideoGenerator.exe >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo. >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"
echo See docs\QUICKSTART.md for detailed instructions. >> "release\portable\temp\ImageToVideoGenerator\README_PORTABLE.txt"

REM Create launch script
echo @echo off > "release\portable\temp\ImageToVideoGenerator\Start.bat"
echo echo Starting Image-to-Video Generator... >> "release\portable\temp\ImageToVideoGenerator\Start.bat"
echo start "" "%%~dp0bin\VideoGenerator.exe" >> "release\portable\temp\ImageToVideoGenerator\Start.bat"

echo Compressing to ZIP...
powershell -Command "Compress-Archive -Path 'release\portable\temp\ImageToVideoGenerator' -DestinationPath 'release\portable\ImageToVideoGenerator-v1.0.0-Portable.zip' -Force"

echo Cleaning up temp files...
rmdir /S /Q "release\portable\temp"

echo.
echo ✓ Portable ZIP created: release\portable\ImageToVideoGenerator-v1.0.0-Portable.zip
echo.

REM ============================================================================
REM Step 5: Copy to Downloads Folder
REM ============================================================================

echo Step 5: Copying packages to Downloads folder...
echo.

set DOWNLOADS=%USERPROFILE%\Downloads

if exist "release\portable\ImageToVideoGenerator-v1.0.0-Portable.zip" (
    copy /Y "release\portable\ImageToVideoGenerator-v1.0.0-Portable.zip" "%DOWNLOADS%\"
    echo ✓ Copied portable ZIP to: %DOWNLOADS%\ImageToVideoGenerator-v1.0.0-Portable.zip
)

if exist "installer\Output\ImageToVideoGenerator-Setup-v1.0.0.exe" (
    copy /Y "installer\Output\ImageToVideoGenerator-Setup-v1.0.0.exe" "%DOWNLOADS%\"
    echo ✓ Copied installer to: %DOWNLOADS%\ImageToVideoGenerator-Setup-v1.0.0.exe
) else (
    echo ⚠ Installer not found - you need to compile it with Inno Setup
    echo   1. Install Inno Setup from https://jrsoftware.org/isinfo.php
    echo   2. Right-click installer\setup.iss and select "Compile"
    echo   3. Run this script again to copy to Downloads
)

echo.
echo ============================================================================
echo Build Complete!
echo ============================================================================
echo.
echo Packages created:
echo   • Portable ZIP: release\portable\ImageToVideoGenerator-v1.0.0-Portable.zip
if exist "installer\Output\ImageToVideoGenerator-Setup-v1.0.0.exe" (
    echo   • Installer: installer\Output\ImageToVideoGenerator-Setup-v1.0.0.exe
)
echo.
echo Copied to Downloads:
dir /B "%DOWNLOADS%\ImageToVideoGenerator*" 2>nul
echo.
echo Next steps:
echo   1. Test the portable package
if not exist "installer\Output\ImageToVideoGenerator-Setup-v1.0.0.exe" (
    echo   2. Create installer with Inno Setup (installer\setup.iss^)
    echo   3. Upload to GitHub release
) else (
    echo   2. Upload to GitHub release
)
echo.
pause
