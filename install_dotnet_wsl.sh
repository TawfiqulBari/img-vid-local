#!/bin/bash
##############################################################################
# Install .NET 6.0 SDK in WSL
##############################################################################
#
# Run this script with: sudo bash install_dotnet_wsl.sh
#
##############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Installing .NET 6.0 SDK in WSL${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Please run with sudo:${NC}"
    echo "  sudo bash install_dotnet_wsl.sh"
    exit 1
fi

echo -e "${BLUE}Step 1: Adding Microsoft package repository...${NC}"

# Download and install Microsoft package repository
cd /tmp
wget -q https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb
dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb

echo -e "${GREEN}✓ Repository added${NC}"
echo ""

echo -e "${BLUE}Step 2: Updating package list...${NC}"
apt update -qq

echo -e "${GREEN}✓ Package list updated${NC}"
echo ""

echo -e "${BLUE}Step 3: Installing .NET 6.0 SDK...${NC}"
echo "This may take 5-10 minutes..."
echo ""

apt install -y dotnet-sdk-6.0

echo ""
echo -e "${GREEN}✓ .NET 6.0 SDK installed${NC}"
echo ""

echo -e "${BLUE}Step 4: Verifying installation...${NC}"

# Verify installation
DOTNET_VERSION=$(dotnet --version 2>&1 || echo "not found")

if [[ "$DOTNET_VERSION" == *"not found"* ]]; then
    echo -e "${YELLOW}⚠ dotnet not found in PATH${NC}"
    echo "You may need to restart your terminal"
else
    echo -e "${GREEN}✓ dotnet version: $DOTNET_VERSION${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "You can now build .NET projects from WSL:"
echo "  cd /home/tawfiq/personal-projects/image-video-3"
echo "  bash build_from_wsl.sh"
echo ""
echo "If 'dotnet' command not found, restart your terminal."
echo ""
