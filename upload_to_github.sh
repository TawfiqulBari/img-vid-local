#!/bin/bash
##############################################################################
# Upload Release Assets to GitHub
##############################################################################
#
# Run this from WSL after building packages on Windows
#
# Usage: bash upload_to_github.sh
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
echo -e "${BLUE}Upload Release Assets to GitHub${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) not installed${NC}"
    echo "Install with: sudo apt install gh"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub${NC}"
    echo ""
    echo "Please authenticate first:"
    echo "  gh auth login"
    echo ""
    echo "Or use your PAT:"
    echo "  echo \"YOUR_PAT_HERE\" | gh auth login --with-token"
    exit 1
fi

echo -e "${GREEN}✓ Authenticated with GitHub${NC}"
echo ""

# Files to upload
PORTABLE_ZIP="release/portable/ImageToVideoGenerator-v1.0.0-Portable.zip"
INSTALLER="installer/Output/ImageToVideoGenerator-Setup-v1.0.0.exe"

# Check which files exist
echo "Checking for build artifacts..."
echo ""

UPLOAD_COUNT=0

if [ -f "$PORTABLE_ZIP" ]; then
    SIZE=$(du -h "$PORTABLE_ZIP" | cut -f1)
    echo -e "${GREEN}✓ Found portable ZIP:${NC} $PORTABLE_ZIP ($SIZE)"
    UPLOAD_COUNT=$((UPLOAD_COUNT + 1))
else
    echo -e "${YELLOW}⚠ Portable ZIP not found:${NC} $PORTABLE_ZIP"
    echo "  Run build_and_package.bat from Windows first"
fi

if [ -f "$INSTALLER" ]; then
    SIZE=$(du -h "$INSTALLER" | cut -f1)
    echo -e "${GREEN}✓ Found installer:${NC} $INSTALLER ($SIZE)"
    UPLOAD_COUNT=$((UPLOAD_COUNT + 1))
else
    echo -e "${YELLOW}⚠ Installer not found:${NC} $INSTALLER"
    echo "  Create installer with Inno Setup (optional)"
fi

echo ""

if [ $UPLOAD_COUNT -eq 0 ]; then
    echo -e "${RED}No files to upload!${NC}"
    echo ""
    echo "Steps to create packages:"
    echo "  1. Open Windows PowerShell or Command Prompt"
    echo "  2. cd \\\\wsl.localhost\\Ubuntu\\home\\tawfiq\\personal-projects\\image-video-3"
    echo "  3. Run: build_and_package.bat"
    echo "  4. Run this script again"
    exit 1
fi

echo -e "${BLUE}Uploading $UPLOAD_COUNT file(s) to GitHub release v1.0.0...${NC}"
echo ""

# Upload portable ZIP
if [ -f "$PORTABLE_ZIP" ]; then
    echo "Uploading portable package..."
    if gh release upload v1.0.0 "$PORTABLE_ZIP" --repo TawfiqulBari/img-vid-local --clobber; then
        echo -e "${GREEN}✓ Uploaded:${NC} ImageToVideoGenerator-v1.0.0-Portable.zip"
    else
        echo -e "${RED}✗ Failed to upload portable package${NC}"
    fi
    echo ""
fi

# Upload installer
if [ -f "$INSTALLER" ]; then
    echo "Uploading installer..."
    if gh release upload v1.0.0 "$INSTALLER" --repo TawfiqulBari/img-vid-local --clobber; then
        echo -e "${GREEN}✓ Uploaded:${NC} ImageToVideoGenerator-Setup-v1.0.0.exe"
    else
        echo -e "${RED}✗ Failed to upload installer${NC}"
    fi
    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Upload Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "View your release at:"
echo "https://github.com/TawfiqulBari/img-vid-local/releases/tag/v1.0.0"
echo ""
