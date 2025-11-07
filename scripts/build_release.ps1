##############################################################################
# Release Build Script
##############################################################################
#
# Builds the Image-to-Video Generator C# application in Release mode
# and prepares it for distribution.
#
# Usage:
#   .\scripts\build_release.ps1
#
# Requirements:
#   - .NET 6.0 SDK installed
#   - PowerShell 5.1 or later
#
##############################################################################

param(
    [switch]$Clean = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
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
$CSharpProject = Join-Path $ProjectRoot "VideoGenerator"
$ReleaseDir = Join-Path $ProjectRoot "release"

Write-Header "Image-to-Video Generator - Release Build"

##############################################################################
# Step 1: Verify Prerequisites
##############################################################################

Write-Header "Step 1: Verifying Prerequisites"

# Check .NET SDK
Write-Info "Checking for .NET SDK..."
try {
    $dotnetVersion = & dotnet --version
    Write-Success ".NET SDK found: $dotnetVersion"
} catch {
    Write-Error ".NET SDK not found. Install from: https://dotnet.microsoft.com/download"
    exit 1
}

# Check project file exists
if (-not (Test-Path (Join-Path $CSharpProject "VideoGenerator.csproj"))) {
    Write-Error "VideoGenerator.csproj not found in $CSharpProject"
    exit 1
}
Write-Success "Project file found"

##############################################################################
# Step 2: Clean Previous Build (if requested)
##############################################################################

if ($Clean) {
    Write-Header "Step 2: Cleaning Previous Build"

    Write-Info "Cleaning bin and obj directories..."
    & dotnet clean "$CSharpProject\VideoGenerator.csproj" --configuration Release

    if (Test-Path $ReleaseDir) {
        Write-Info "Removing previous release directory..."
        Remove-Item -Path $ReleaseDir -Recurse -Force
    }

    Write-Success "Clean complete"
}

##############################################################################
# Step 3: Restore NuGet Packages
##############################################################################

Write-Header "Step 3: Restoring NuGet Packages"

Write-Info "Restoring packages..."
& dotnet restore "$CSharpProject\VideoGenerator.csproj"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to restore packages"
    exit 1
}

Write-Success "Packages restored"

##############################################################################
# Step 4: Build Release Configuration
##############################################################################

Write-Header "Step 4: Building Release Configuration"

Write-Info "Building VideoGenerator in Release mode..."

$buildArgs = @(
    "build",
    "$CSharpProject\VideoGenerator.csproj",
    "--configuration", "Release",
    "--no-restore"
)

if ($Verbose) {
    $buildArgs += "--verbosity", "detailed"
}

& dotnet @buildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit 1
}

Write-Success "Build successful"

##############################################################################
# Step 5: Verify Build Output
##############################################################################

Write-Header "Step 5: Verifying Build Output"

$BinRelease = Join-Path $CSharpProject "bin\Release\net6.0-windows"
$ExePath = Join-Path $BinRelease "VideoGenerator.exe"

if (-not (Test-Path $ExePath)) {
    Write-Error "VideoGenerator.exe not found at: $ExePath"
    exit 1
}

Write-Success "Executable found: VideoGenerator.exe"

# Get file size
$ExeSize = (Get-Item $ExePath).Length / 1MB
Write-Info "Executable size: $([math]::Round($ExeSize, 2)) MB"

# Count DLL dependencies
$DllCount = (Get-ChildItem -Path $BinRelease -Filter "*.dll" | Measure-Object).Count
Write-Info "Dependencies: $DllCount DLL files"

##############################################################################
# Step 6: Create Release Directory Structure
##############################################################################

Write-Header "Step 6: Creating Release Directory Structure"

# Create release directory
if (-not (Test-Path $ReleaseDir)) {
    New-Item -Path $ReleaseDir -ItemType Directory | Out-Null
}

# Create subdirectories
$ReleaseBinDir = Join-Path $ReleaseDir "bin"
$ReleaseDocsDir = Join-Path $ReleaseDir "docs"
$ReleaseScriptsDir = Join-Path $ReleaseDir "scripts"

@($ReleaseBinDir, $ReleaseDocsDir, $ReleaseScriptsDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -Path $_ -ItemType Directory | Out-Null
    }
}

Write-Success "Release directory structure created"

##############################################################################
# Step 7: Copy Application Files
##############################################################################

Write-Header "Step 7: Copying Application Files"

Write-Info "Copying executable and dependencies..."
Copy-Item -Path "$BinRelease\*" -Destination $ReleaseBinDir -Recurse -Force

Write-Success "Application files copied to: $ReleaseBinDir"

##############################################################################
# Step 8: Copy Documentation
##############################################################################

Write-Header "Step 8: Copying Documentation"

$DocFiles = @(
    "README.md",
    "QUICKSTART.md",
    "TROUBLESHOOTING.md",
    "LICENSE"
)

foreach ($DocFile in $DocFiles) {
    $SourcePath = Join-Path $ProjectRoot $DocFile
    if (Test-Path $SourcePath) {
        Copy-Item -Path $SourcePath -Destination $ReleaseDocsDir -Force
        Write-Info "Copied: $DocFile"
    } else {
        Write-Info "Skipped (not found): $DocFile"
    }
}

# Copy backend catalog
$CatalogPath = Join-Path $ProjectRoot "backend\models_catalog.json"
if (Test-Path $CatalogPath) {
    Copy-Item -Path $CatalogPath -Destination $ReleaseBinDir -Force
    Write-Info "Copied: models_catalog.json"
}

Write-Success "Documentation copied"

##############################################################################
# Step 9: Copy Setup Scripts
##############################################################################

Write-Header "Step 9: Copying Setup Scripts"

$SetupScripts = @(
    "scripts\setup_wsl.sh",
    "scripts\test_integration.sh"
)

foreach ($Script in $SetupScripts) {
    $SourcePath = Join-Path $ProjectRoot $Script
    if (Test-Path $SourcePath) {
        Copy-Item -Path $SourcePath -Destination $ReleaseScriptsDir -Force
        Write-Info "Copied: $(Split-Path -Leaf $Script)"
    }
}

Write-Success "Setup scripts copied"

##############################################################################
# Step 10: Create Version Info File
##############################################################################

Write-Header "Step 10: Creating Version Info"

$VersionInfo = @"
Image-to-Video Generator - Release Information
=============================================

Version: 1.0.0
Build Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Build Configuration: Release
.NET Version: net6.0-windows

System Requirements
-------------------
- Windows 10/11 (64-bit)
- .NET 6.0 Runtime (Desktop)
- WSL 2 with Ubuntu 22.04
- NVIDIA RTX GPU (12GB+ VRAM recommended)
- 30GB+ free disk space
- 16GB+ RAM recommended

Installation
------------
1. Extract all files to a directory (e.g., C:\VideoGenerator)
2. Follow QUICKSTART.md in the docs folder
3. Run VideoGenerator.exe after setup

Support
-------
For issues and troubleshooting, see TROUBLESHOOTING.md in the docs folder.

License
-------
See LICENSE file for licensing information.
"@

$VersionInfo | Out-File -FilePath (Join-Path $ReleaseDir "VERSION.txt") -Encoding UTF8
Write-Success "Version info created"

##############################################################################
# Step 11: Generate File Listing
##############################################################################

Write-Header "Step 11: Generating File Listing"

$FileList = Get-ChildItem -Path $ReleaseDir -Recurse -File |
    Select-Object @{Name="Path";Expression={$_.FullName.Replace($ReleaseDir, ".")}},
                  @{Name="Size";Expression={"{0:N2} KB" -f ($_.Length / 1KB)}}

$FileList | Format-Table -AutoSize | Out-File -FilePath (Join-Path $ReleaseDir "FILES.txt") -Encoding UTF8
Write-Success "File listing created: FILES.txt"

##############################################################################
# Summary
##############################################################################

Write-Header "Build Summary"

$TotalSize = (Get-ChildItem -Path $ReleaseDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Success "Release build completed successfully!"
Write-Info "Release directory: $ReleaseDir"
Write-Info "Total size: $([math]::Round($TotalSize, 2)) MB"
Write-Info "Executable: $ReleaseBinDir\VideoGenerator.exe"

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test the application: $ReleaseBinDir\VideoGenerator.exe"
Write-Host "  2. Create installer: .\scripts\build_installer.ps1"
Write-Host "  3. Create portable ZIP: .\scripts\create_portable.ps1"
Write-Host "  4. Review documentation in: $ReleaseDocsDir"
Write-Host ""
