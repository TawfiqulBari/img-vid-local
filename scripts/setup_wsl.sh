#!/bin/bash
##############################################################################
# Image-to-Video Generator - WSL Environment Setup Script
##############################################################################
#
# This script automates the setup of the Python development environment
# in WSL for the image-to-video generator application.
#
# Usage:
#   bash scripts/setup_wsl.sh
#   # Or make executable: chmod +x scripts/setup_wsl.sh && ./scripts/setup_wsl.sh
#
# What this script does:
#   1. Checks system requirements (Python 3.10/3.11/3.12, nvidia-smi)
#   2. Creates Python virtual environment
#   3. Installs PyTorch with CUDA 11.8
#   4. Installs all dependencies
#   5. Verifies GPU access
#   6. Creates necessary directories on D:\ drive
#   7. Provides next steps
#
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_header "Image-to-Video Generator - WSL Setup"

echo "Project Root: $PROJECT_ROOT"
echo "Current User: $USER"
echo "Current Directory: $(pwd)"

##############################################################################
# Step 1: Check Prerequisites
##############################################################################

print_header "Step 1: Checking Prerequisites"

# Check if running in WSL
if grep -qi microsoft /proc/version; then
    print_success "Running in WSL"
else
    print_warning "Not running in WSL - this script is designed for WSL"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python 3.10, 3.11, or 3.12
PYTHON_CMD=""
PYTHON_VERSION=""

# Try specific versions first
for VERSION in "3.10" "3.11" "3.12"; do
    if command -v "python$VERSION" &> /dev/null; then
        PYTHON_CMD="python$VERSION"
        PYTHON_VERSION=$(python$VERSION --version | cut -d' ' -f2)
        print_success "Python $VERSION found: $PYTHON_VERSION"
        break
    fi
done

# If no specific version found, check python3
if [ -z "$PYTHON_CMD" ] && command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    case "$PYTHON_VERSION" in
        3.10|3.11|3.12)
            PYTHON_CMD="python3"
            print_success "Python $PYTHON_VERSION found: $(python3 --version)"
            ;;
        *)
            print_error "Python 3.10+ not found (found Python $PYTHON_VERSION)"
            print_info "This project requires Python 3.10, 3.11, or 3.12"
            print_info "Install with: sudo apt update && sudo apt install python3.12 python3.12-venv python3.12-dev"
            exit 1
            ;;
    esac
fi

# If still no Python found
if [ -z "$PYTHON_CMD" ]; then
    print_error "Python not found"
    print_info "Install with: sudo apt update && sudo apt install python3.12 python3.12-venv python3.12-dev"
    exit 1
fi

# Check nvidia-smi
if command -v nvidia-smi &> /dev/null; then
    print_success "nvidia-smi found"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | head -1
else
    print_error "nvidia-smi not found - NVIDIA drivers not installed"
    print_info "Follow: https://docs.nvidia.com/cuda/wsl-user-guide/index.html"
    read -p "Continue without GPU? (not recommended) (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check git
if ! command -v git &> /dev/null; then
    print_warning "git not found - Installing..."
    sudo apt update && sudo apt install -y git
fi

##############################################################################
# Step 2: Create Virtual Environment
##############################################################################

print_header "Step 2: Creating Python Virtual Environment"

VENV_PATH="$PROJECT_ROOT/backend/venv"

if [ -d "$VENV_PATH" ]; then
    print_warning "Virtual environment already exists at $VENV_PATH"
    read -p "Delete and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_PATH"
        print_info "Deleted existing virtual environment"
    else
        print_info "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_PATH" ]; then
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_PATH"
    print_success "Virtual environment created"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel
print_success "pip upgraded to $(pip --version | cut -d' ' -f2)"

##############################################################################
# Step 3: Install PyTorch with CUDA 11.8
##############################################################################

print_header "Step 3: Installing PyTorch with CUDA 11.8"

print_info "This may take 5-10 minutes depending on your internet speed..."

pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 \
    --index-url https://download.pytorch.org/whl/cu118

print_success "PyTorch installed"

# Verify PyTorch CUDA
print_info "Verifying PyTorch CUDA support..."
python -c "import torch; print(f'PyTorch Version: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}' if torch.cuda.is_available() else 'CUDA Not Available')"

##############################################################################
# Step 4: Install All Dependencies
##############################################################################

print_header "Step 4: Installing All Dependencies"

print_info "This may take 10-15 minutes..."
print_info "Installing from: $PROJECT_ROOT/backend/requirements.txt"

# Install with no cache to avoid memory issues
pip install --no-cache-dir -r "$PROJECT_ROOT/backend/requirements.txt"

print_success "All dependencies installed"

##############################################################################
# Step 5: Verify Installation
##############################################################################

print_header "Step 5: Verifying Installation"

# Check key packages
print_info "Checking installed packages..."

PACKAGES=("torch" "diffusers" "transformers" "accelerate" "xformers" "PIL" "cv2")
for pkg in "${PACKAGES[@]}"; do
    if python -c "import $pkg" 2>/dev/null; then
        print_success "$pkg is importable"
    else
        print_error "$pkg failed to import"
    fi
done

# Run GPU check script
if [ -f "$SCRIPT_DIR/check_gpu.py" ]; then
    print_info "Running comprehensive GPU check..."
    python "$SCRIPT_DIR/check_gpu.py"
else
    print_warning "check_gpu.py not found, skipping comprehensive check"
fi

##############################################################################
# Step 6: Create Necessary Directories
##############################################################################

print_header "Step 6: Creating Directory Structure"

# Create directories on D:\ drive (Windows)
D_DRIVE="/mnt/d"

if [ -d "$D_DRIVE" ]; then
    print_success "D:\\ drive accessible at $D_DRIVE"

    # Create VideoGenerator structure
    VIDEO_GEN_DIR="$D_DRIVE/VideoGenerator"
    mkdir -p "$VIDEO_GEN_DIR/models"
    mkdir -p "$VIDEO_GEN_DIR/output"
    mkdir -p "$VIDEO_GEN_DIR/logs"

    print_success "Created directory structure:"
    print_info "  - $VIDEO_GEN_DIR/models/  (for AI models)"
    print_info "  - $VIDEO_GEN_DIR/output/  (for generated videos)"
    print_info "  - $VIDEO_GEN_DIR/logs/    (for logs)"

    # Set permissions
    chmod -R 755 "$VIDEO_GEN_DIR" 2>/dev/null || true

else
    print_warning "D:\\ drive not accessible at $D_DRIVE"
    print_info "You may need to create D:\\VideoGenerator\\models\\ manually in Windows"
fi

# Create Python package __init__.py files
print_info "Creating Python package files..."
touch "$PROJECT_ROOT/backend/pipelines/__init__.py"
touch "$PROJECT_ROOT/backend/services/__init__.py"
touch "$PROJECT_ROOT/backend/utils/__init__.py"
print_success "Python packages initialized"

##############################################################################
# Step 7: Summary and Next Steps
##############################################################################

print_header "Setup Complete!"

print_success "Python environment is ready for development"

echo -e "\n${GREEN}Virtual Environment:${NC}"
echo "  Location: $VENV_PATH"
echo "  Activate: source $VENV_PATH/bin/activate"
echo "  Deactivate: deactivate"

echo -e "\n${GREEN}Next Steps:${NC}"
echo "  1. Download AI models:"
echo "     ${YELLOW}python backend/download_models.py${NC}"
echo ""
echo "  2. Test GPU and Python setup:"
echo "     ${YELLOW}python scripts/check_gpu.py${NC}"
echo ""
echo "  3. Start developing!"
echo "     - Backend code: backend/"
echo "     - Frontend code: frontend/"
echo ""

if [ -d "$D_DRIVE" ]; then
    echo "  4. Models will be downloaded to:"
    echo "     ${YELLOW}D:\\VideoGenerator\\models\\${NC}"
    echo "     (accessible from WSL: /mnt/d/VideoGenerator/models/)"
else
    echo "  4. ${YELLOW}Note:${NC} D:\\ drive not accessible"
    echo "     Create D:\\VideoGenerator\\models\\ manually in Windows"
fi

echo -e "\n${BLUE}Documentation:${NC}"
echo "  - Development Plan: plans/PLAN.md"
echo "  - Technical Spec: plans/SPEC.md"
echo "  - WSL Guide: plans/wsl-windows-guide.md"
echo "  - Model Guide: plans/MODELS.md"

echo -e "\n${GREEN}Happy Coding! 🚀${NC}\n"

# Keep virtual environment activated for user
echo "Virtual environment is now activated for this session."
echo "You can start working immediately!"
