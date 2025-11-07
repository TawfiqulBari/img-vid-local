##############################################################################
# Portable Package Creation Script
##############################################################################
#
# Creates a portable ZIP package of the Image-to-Video Generator that can
# be extracted and run without installation.
#
# Usage:
#   .\scripts\create_portable.ps1
#
# Requirements:
#   - Release build completed (run .\scripts\build_release.ps1 first)
#   - PowerShell 5.1 or later
#
# Output:
#   release\portable\ImageToVideoGenerator-v1.0.0-Portable.zip
#
##############################################################################

param(
    [switch]$IncludeModels = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Header {
    param($Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""
}

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ReleaseDir = Join-Path $ProjectRoot "release"
$PortableDir = Join-Path $ReleaseDir "portable"
$PortableTempDir = Join-Path $PortableDir "temp"

Write-Header "Image-to-Video Generator - Portable Package Creator"

##############################################################################
# Step 1: Verify Prerequisites
##############################################################################

Write-Header "Step 1: Verifying Prerequisites"

# Check if release build exists
if (-not (Test-Path (Join-Path $ReleaseDir "bin\VideoGenerator.exe"))) {
    Write-Error "Release build not found. Run .\scripts\build_release.ps1 first."
    exit 1
}
Write-Success "Release build found"

# Check if Compress-Archive is available
try {
    Get-Command Compress-Archive -ErrorAction Stop | Out-Null
    Write-Success "ZIP compression available"
} catch {
    Write-Error "Compress-Archive not available. PowerShell 5.0+ required."
    exit 1
}

##############################################################################
# Step 2: Create Portable Directory Structure
##############################################################################

Write-Header "Step 2: Creating Portable Directory Structure"

# Clean up existing portable temp directory
if (Test-Path $PortableTempDir) {
    Write-Info "Removing existing temp directory..."
    Remove-Item -Path $PortableTempDir -Recurse -Force
}

# Create new temp directory
New-Item -Path $PortableTempDir -ItemType Directory | Out-Null

# Create subdirectories
$AppDir = Join-Path $PortableTempDir "ImageToVideoGenerator"
$BinDir = Join-Path $AppDir "bin"
$DocsDir = Join-Path $AppDir "docs"
$ScriptsDir = Join-Path $AppDir "scripts"
$BackendDir = Join-Path $AppDir "backend"

@($AppDir, $BinDir, $DocsDir, $ScriptsDir, $BackendDir) | ForEach-Object {
    New-Item -Path $_ -ItemType Directory | Out-Null
}

Write-Success "Directory structure created"

##############################################################################
# Step 3: Copy Application Files
##############################################################################

Write-Header "Step 3: Copying Application Files"

Write-Info "Copying executable and dependencies..."
Copy-Item -Path "$ReleaseDir\bin\*" -Destination $BinDir -Recurse -Force
Write-Success "Application files copied"

##############################################################################
# Step 4: Copy Documentation
##############################################################################

Write-Header "Step 4: Copying Documentation"

if (Test-Path (Join-Path $ReleaseDir "docs")) {
    Copy-Item -Path "$ReleaseDir\docs\*" -Destination $DocsDir -Force
    Write-Success "Documentation copied"
} else {
    Write-Warning "Documentation not found in release directory"
}

# Copy version info
Copy-Item -Path (Join-Path $ReleaseDir "VERSION.txt") -Destination $AppDir -Force

##############################################################################
# Step 5: Copy Setup Scripts
##############################################################################

Write-Header "Step 5: Copying Setup Scripts"

if (Test-Path (Join-Path $ReleaseDir "scripts")) {
    Copy-Item -Path "$ReleaseDir\scripts\*" -Destination $ScriptsDir -Force
    Write-Success "Setup scripts copied"
}

# Copy backend scripts (but not venv)
$BackendSource = Join-Path $ProjectRoot "backend"
$BackendFiles = @(
    "generate.py",
    "test_generation.py",
    "download_models.py",
    "verify_setup.py",
    "requirements.txt",
    "models_catalog.json"
)

foreach ($File in $BackendFiles) {
    $SourcePath = Join-Path $BackendSource $File
    if (Test-Path $SourcePath) {
        Copy-Item -Path $SourcePath -Destination $BackendDir -Force
        Write-Info "Copied: $File"
    }
}

# Copy backend utils directory
$UtilsSource = Join-Path $BackendSource "utils"
if (Test-Path $UtilsSource) {
    $UtilsDest = Join-Path $BackendDir "utils"
    Copy-Item -Path $UtilsSource -Destination $UtilsDest -Recurse -Force
    Write-Info "Copied: utils directory"
}

Write-Success "Backend files copied"

##############################################################################
# Step 6: Copy Models (Optional)
##############################################################################

if ($IncludeModels) {
    Write-Header "Step 6: Copying AI Models (Optional)"
    Write-Warning "This will significantly increase package size (~15GB)"

    $ModelsSource = "D:\VideoGenerator\models"
    if (Test-Path $ModelsSource) {
        $ModelsDest = Join-Path $AppDir "models"
        Write-Info "Copying models... This may take several minutes..."

        Copy-Item -Path $ModelsSource -Destination $ModelsDest -Recurse -Force
        Write-Success "Models copied"

        $ModelsSize = (Get-ChildItem -Path $ModelsDest -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
        Write-Info "Models size: $([math]::Round($ModelsSize, 2)) GB"
    } else {
        Write-Warning "Models directory not found at: $ModelsSource"
    }
} else {
    Write-Info "Skipping models (use -IncludeModels to include them)"
}

##############################################################################
# Step 7: Create README for Portable Version
##############################################################################

Write-Header "Step 7: Creating Portable README"

$PortableReadme = @"
Image-to-Video Generator - Portable Version
============================================

Version: 1.0.0
Package Type: Portable (No Installation Required)

QUICK START
-----------

1. Extract this entire folder to a location of your choice
   Example: C:\Tools\ImageToVideoGenerator

2. Ensure you have the required software:
   - Windows 10/11 (64-bit)
   - .NET 6.0 Desktop Runtime
     Download: https://dotnet.microsoft.com/download/dotnet/6.0
   - WSL 2 with Ubuntu 22.04
     Install: wsl --install -d Ubuntu-22.04

3. Set up Python backend:
   - Open Ubuntu (WSL) terminal
   - Navigate to this directory
   - Run: bash scripts/setup_wsl.sh

4. Download AI models:
   - Follow prompts from setup script
   - Models will be saved to D:\VideoGenerator\models\
   - Size: ~15GB, Time: 20-40 minutes

5. Run the application:
   - Double-click bin\VideoGenerator.exe
   - Or run from command line

DIRECTORY STRUCTURE
-------------------

ImageToVideoGenerator\
├── bin\                    Application files
│   └── VideoGenerator.exe  Main executable
├── backend\                Python backend scripts
│   ├── generate.py         Main generation script
│   ├── download_models.py  Model download utility
│   └── verify_setup.py     Setup verification
├── docs\                   Documentation
│   ├── QUICKSTART.md       Step-by-step setup guide
│   └── TROUBLESHOOTING.md  Problem-solving guide
├── scripts\                Setup scripts
│   └── setup_wsl.sh        WSL environment setup
└── VERSION.txt             Version information

SYSTEM REQUIREMENTS
-------------------

Minimum:
- Windows 10 (64-bit) build 17763 or later
- .NET 6.0 Desktop Runtime
- WSL 2 with Ubuntu 22.04
- NVIDIA RTX 3060 (12GB VRAM) or equivalent
- 16GB RAM
- 30GB free disk space

Recommended:
- Windows 11 (64-bit)
- RTX 3080 or better (12GB+ VRAM)
- 32GB RAM
- SSD for models and output

IMPORTANT NOTES
---------------

1. AGE RESTRICTION
   ⚠️ This application is for users 18+ years old
   ⚠️ Supports NSFW (Not Safe For Work) AI models
   ⚠️ Use responsibly and legally

2. OFFLINE OPERATION
   ✓ All processing is done locally
   ✓ No data sent to external servers
   ✓ No telemetry or tracking
   ✓ Works completely offline after setup

3. FIRST RUN
   - First generation is slow (model loading)
   - Subsequent generations are much faster
   - Allow 30-90 seconds for first video

4. TROUBLESHOOTING
   - See docs\TROUBLESHOOTING.md for common issues
   - Run backend\verify_setup.py to check your environment
   - Ensure all prerequisites are installed

GETTING HELP
------------

Documentation:
- QUICKSTART.md - Complete setup guide
- TROUBLESHOOTING.md - Common problems and solutions

Online:
- GitHub: https://github.com/YOUR_USERNAME/image-video-generator
- Issues: https://github.com/YOUR_USERNAME/image-video-generator/issues

LEGAL
-----

- You are responsible for all generated content
- Follow local laws regarding AI-generated content
- For private use only
- Respect copyright and intellectual property

LICENSE
-------

See docs\LICENSE for licensing information.

ENJOY!
------

Have fun generating AI videos! 🎬✨
"@

$PortableReadme | Out-File -FilePath (Join-Path $AppDir "README_PORTABLE.txt") -Encoding UTF8
Write-Success "Portable README created"

##############################################################################
# Step 8: Create Launch Script
##############################################################################

Write-Header "Step 8: Creating Launch Script"

$LaunchScript = @"
@echo off
REM Image-to-Video Generator - Launcher
REM ====================================

echo.
echo Image-to-Video Generator v1.0.0
echo ================================
echo.

REM Check if .NET is installed
where dotnet >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: .NET 6.0 Runtime not found!
    echo.
    echo Please install .NET 6.0 Desktop Runtime from:
    echo https://dotnet.microsoft.com/download/dotnet/6.0
    echo.
    pause
    exit /b 1
)

REM Launch application
echo Starting application...
echo.
start "" "%~dp0bin\VideoGenerator.exe"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start application
    echo.
    echo Troubleshooting:
    echo 1. Check if all files are extracted correctly
    echo 2. Verify .NET 6.0 is installed
    echo 3. See docs\TROUBLESHOOTING.md
    echo.
    pause
    exit /b 1
)

echo Application launched successfully!
timeout /t 2 >nul
"@

$LaunchScript | Out-File -FilePath (Join-Path $AppDir "Start.bat") -Encoding ASCII
Write-Success "Launch script created"

##############################################################################
# Step 9: Calculate Package Size
##############################################################################

Write-Header "Step 9: Calculating Package Size"

$TotalSize = (Get-ChildItem -Path $AppDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
$SizeMB = $TotalSize / 1MB
$SizeGB = $TotalSize / 1GB

if ($SizeGB -gt 1) {
    Write-Info "Package size: $([math]::Round($SizeGB, 2)) GB"
} else {
    Write-Info "Package size: $([math]::Round($SizeMB, 2)) MB"
}

$FileCount = (Get-ChildItem -Path $AppDir -Recurse -File | Measure-Object).Count
Write-Info "Total files: $FileCount"

##############################################################################
# Step 10: Create ZIP Archive
##############################################################################

Write-Header "Step 10: Creating ZIP Archive"

$ZipFileName = "ImageToVideoGenerator-v1.0.0-Portable.zip"
$ZipFilePath = Join-Path $PortableDir $ZipFileName

# Remove existing ZIP if present
if (Test-Path $ZipFilePath) {
    Write-Info "Removing existing ZIP file..."
    Remove-Item -Path $ZipFilePath -Force
}

Write-Info "Compressing files... This may take a few minutes..."

try {
    Compress-Archive -Path $AppDir -DestinationPath $ZipFilePath -CompressionLevel Optimal
    Write-Success "ZIP archive created successfully"
} catch {
    Write-Error "Failed to create ZIP archive: $_"
    exit 1
}

##############################################################################
# Step 11: Verify ZIP Archive
##############################################################################

Write-Header "Step 11: Verifying ZIP Archive"

if (Test-Path $ZipFilePath) {
    $ZipSize = (Get-Item $ZipFilePath).Length
    $ZipSizeMB = $ZipSize / 1MB
    $ZipSizeGB = $ZipSize / 1GB

    if ($ZipSizeGB -gt 1) {
        Write-Info "Compressed size: $([math]::Round($ZipSizeGB, 2)) GB"
    } else {
        Write-Info "Compressed size: $([math]::Round($ZipSizeMB, 2)) MB"
    }

    $CompressionRatio = ($ZipSize / $TotalSize) * 100
    Write-Info "Compression ratio: $([math]::Round($CompressionRatio, 1))%"

    Write-Success "ZIP file verified"
} else {
    Write-Error "ZIP file not found after compression"
    exit 1
}

##############################################################################
# Step 12: Cleanup Temp Directory
##############################################################################

Write-Header "Step 12: Cleaning Up"

Write-Info "Removing temporary files..."
Remove-Item -Path $PortableTempDir -Recurse -Force
Write-Success "Cleanup complete"

##############################################################################
# Summary
##############################################################################

Write-Header "Portable Package Created Successfully!"

Write-Success "Package location: $ZipFilePath"

if ($ZipSizeGB -gt 1) {
    Write-Info "Package size: $([math]::Round($ZipSizeGB, 2)) GB"
} else {
    Write-Info "Package size: $([math]::Round($ZipSizeMB, 2)) MB"
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test the portable package by extracting it"
Write-Host "  2. Verify all files are present"
Write-Host "  3. Test on a clean machine (recommended)"
Write-Host "  4. Upload to GitHub Releases or distribution platform"
Write-Host ""

if (-not $IncludeModels) {
    Write-Host "Note: AI models are NOT included in this package." -ForegroundColor Yellow
    Write-Host "      Users will need to download models after extraction (~15GB)." -ForegroundColor Yellow
    Write-Host "      Use -IncludeModels flag to create a package with models." -ForegroundColor Yellow
    Write-Host ""
}
