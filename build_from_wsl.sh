#!/bin/bash
##############################################################################
# Build Image-to-Video Generator from WSL
##############################################################################
#
# This script builds the C# application directly from WSL using dotnet CLI
#
# Prerequisites:
#   - .NET 6.0 SDK installed in WSL (run: sudo bash install_dotnet_wsl.sh)
#
# Usage:
#   bash build_from_wsl.sh
#
##############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Image-to-Video Generator - WSL Build${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

##############################################################################
# Step 1: Verify .NET SDK
##############################################################################

echo -e "${BLUE}Step 1: Verifying .NET SDK...${NC}"

if ! command -v dotnet &> /dev/null; then
    echo -e "${RED}Error: dotnet CLI not found${NC}"
    echo ""
    echo "Please install .NET 6.0 SDK first:"
    echo "  sudo bash install_dotnet_wsl.sh"
    echo ""
    exit 1
fi

DOTNET_VERSION=$(dotnet --version)
echo -e "${GREEN}✓ dotnet version: $DOTNET_VERSION${NC}"
echo ""

##############################################################################
# Step 2: Clean Previous Build (Optional)
##############################################################################

echo -e "${BLUE}Step 2: Cleaning previous build...${NC}"

if [ -d "release" ]; then
    rm -rf release
    echo -e "${GREEN}✓ Cleaned release directory${NC}"
else
    echo -e "${YELLOW}→ No previous build found${NC}"
fi
echo ""

##############################################################################
# Step 3: Restore NuGet Packages
##############################################################################

echo -e "${BLUE}Step 3: Restoring NuGet packages...${NC}"

cd VideoGenerator
dotnet restore
echo -e "${GREEN}✓ Packages restored${NC}"
echo ""

##############################################################################
# Step 4: Build Release Configuration
##############################################################################

echo -e "${BLUE}Step 4: Building Release configuration...${NC}"

dotnet build --configuration Release --no-restore

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"
echo ""

cd ..

##############################################################################
# Step 5: Create Release Directory Structure
##############################################################################

echo -e "${BLUE}Step 5: Creating release directory structure...${NC}"

mkdir -p release/bin
mkdir -p release/docs
mkdir -p release/scripts
mkdir -p release/backend
mkdir -p release/portable

echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

##############################################################################
# Step 6: Copy Application Files
##############################################################################

echo -e "${BLUE}Step 6: Copying application files...${NC}"

# Copy executable and dependencies
echo "→ Copying binaries..."
cp -r VideoGenerator/bin/Release/net6.0-windows/* release/bin/

# Copy backend files
echo "→ Copying backend..."
cp backend/generate.py release/backend/ 2>/dev/null || true
cp backend/download_models.py release/backend/ 2>/dev/null || true
cp backend/verify_setup.py release/backend/ 2>/dev/null || true
cp backend/test_generation.py release/backend/ 2>/dev/null || true
cp backend/requirements.txt release/backend/ 2>/dev/null || true
cp backend/models_catalog.json release/backend/ 2>/dev/null || true
cp backend/__init__.py release/backend/ 2>/dev/null || true

# Copy backend subdirectories
if [ -d "backend/utils" ]; then
    cp -r backend/utils release/backend/
fi
if [ -d "backend/pipelines" ]; then
    cp -r backend/pipelines release/backend/
fi
if [ -d "backend/services" ]; then
    cp -r backend/services release/backend/
fi

# Copy documentation
echo "→ Copying documentation..."
cp README.md release/docs/ 2>/dev/null || true
cp QUICKSTART.md release/docs/ 2>/dev/null || true
cp TROUBLESHOOTING.md release/docs/ 2>/dev/null || true
cp RELEASE_NOTES.md release/docs/ 2>/dev/null || true
cp LICENSE release/docs/ 2>/dev/null || true

# Copy setup scripts
echo "→ Copying setup scripts..."
cp scripts/setup_wsl.sh release/scripts/ 2>/dev/null || true
cp scripts/test_integration.sh release/scripts/ 2>/dev/null || true

echo -e "${GREEN}✓ Files copied${NC}"
echo ""

##############################################################################
# Step 7: Create Portable ZIP Package
##############################################################################

echo -e "${BLUE}Step 7: Creating portable ZIP package...${NC}"

# Create temporary directory for packaging
mkdir -p release/portable/temp/ImageToVideoGenerator

# Copy all files to temp directory
cp -r release/bin release/portable/temp/ImageToVideoGenerator/
cp -r release/backend release/portable/temp/ImageToVideoGenerator/
cp -r release/docs release/portable/temp/ImageToVideoGenerator/
cp -r release/scripts release/portable/temp/ImageToVideoGenerator/

# Create README for portable version
cat > release/portable/temp/ImageToVideoGenerator/README_PORTABLE.txt << 'EOF'
Image-to-Video Generator - Portable Version
============================================

Version: 1.0.0
Package Type: Portable (No Installation Required)

QUICK START
-----------

1. Extract this entire folder to a location of your choice
2. Install .NET 6.0 Desktop Runtime from:
   https://dotnet.microsoft.com/download/dotnet/6.0
3. Install WSL 2 with Ubuntu 22.04:
   wsl --install -d Ubuntu-22.04
4. Open Ubuntu (WSL) terminal and run:
   bash scripts/setup_wsl.sh
5. Download models (~15GB):
   python backend/download_models.py
6. Run the application:
   bin/VideoGenerator.exe

See docs/QUICKSTART.md for detailed instructions.

SYSTEM REQUIREMENTS
-------------------
- Windows 10/11 (64-bit)
- .NET 6.0 Desktop Runtime
- WSL 2 with Ubuntu 22.04
- NVIDIA RTX GPU (12GB+ VRAM)
- 16GB+ RAM
- 30GB+ free disk space

SUPPORT
-------
Documentation: docs/
GitHub: https://github.com/TawfiqulBari/img-vid-local
Issues: https://github.com/TawfiqulBari/img-vid-local/issues
EOF

# Create launch script
cat > release/portable/temp/ImageToVideoGenerator/Start.bat << 'EOF'
@echo off
echo Starting Image-to-Video Generator...
start "" "%~dp0bin\VideoGenerator.exe"
EOF

# Create ZIP package
echo "→ Compressing to ZIP..."
cd release/portable/temp
zip -r -q ../ImageToVideoGenerator-v1.0.0-Portable.zip ImageToVideoGenerator
cd ../../..

# Cleanup temp files
rm -rf release/portable/temp

ZIP_SIZE=$(du -h release/portable/ImageToVideoGenerator-v1.0.0-Portable.zip | cut -f1)
echo -e "${GREEN}✓ Portable ZIP created: $ZIP_SIZE${NC}"
echo ""

##############################################################################
# Step 8: Copy to Windows Downloads Folder
##############################################################################

echo -e "${BLUE}Step 8: Copying to Windows Downloads folder...${NC}"

# Get Windows username
WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
DOWNLOADS="/mnt/c/Users/$WIN_USER/Downloads"

if [ -d "$DOWNLOADS" ]; then
    cp release/portable/ImageToVideoGenerator-v1.0.0-Portable.zip "$DOWNLOADS/"
    echo -e "${GREEN}✓ Copied to: $DOWNLOADS/${NC}"
    echo -e "${GREEN}  → ImageToVideoGenerator-v1.0.0-Portable.zip${NC}"
else
    echo -e "${YELLOW}⚠ Downloads folder not found${NC}"
    echo "Manual copy required to: C:\\Users\\$WIN_USER\\Downloads"
fi

echo ""

##############################################################################
# Step 9: Generate Build Summary
##############################################################################

echo -e "${BLUE}Step 9: Build summary...${NC}"

# Create version info
cat > release/VERSION.txt << EOF
Image-to-Video Generator - Build Information
=============================================

Version: 1.0.0
Build Date: $(date '+%Y-%m-%d %H:%M:%S')
Build Type: Release
Build Environment: WSL (Ubuntu)
.NET Version: $DOTNET_VERSION

System Requirements
-------------------
- Windows 10/11 (64-bit)
- .NET 6.0 Desktop Runtime
- WSL 2 with Ubuntu 22.04
- NVIDIA RTX GPU (12GB+ VRAM)
- 30GB+ free disk space
- 16GB+ RAM

Installation
------------
See docs/QUICKSTART.md for complete installation instructions.

Support
-------
GitHub: https://github.com/TawfiqulBari/img-vid-local
Issues: https://github.com/TawfiqulBari/img-vid-local/issues
EOF

echo -e "${GREEN}✓ Version info created${NC}"
echo ""

##############################################################################
# Summary
##############################################################################

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TOTAL_SIZE=$(du -sh release | cut -f1)
echo "Build artifacts:"
echo "  • Release directory: release/ ($TOTAL_SIZE)"
echo "  • Portable package: release/portable/ImageToVideoGenerator-v1.0.0-Portable.zip ($ZIP_SIZE)"
echo "  • Executable: release/bin/VideoGenerator.exe"
echo ""

if [ -d "$DOWNLOADS" ]; then
    echo "Package copied to:"
    echo "  • $DOWNLOADS/ImageToVideoGenerator-v1.0.0-Portable.zip"
    echo ""
fi

echo "Next steps:"
echo "  1. Upload to GitHub release:"
echo "     bash upload_to_github.sh"
echo "  2. Test the application:"
echo "     cd release/bin && ./VideoGenerator.exe"
echo ""
