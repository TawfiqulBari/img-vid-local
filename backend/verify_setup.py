#!/usr/bin/env python3
"""
Environment Setup Verification Script

Checks that all requirements for the Image-to-Video Generator are met:
- Python version
- CUDA availability
- Dependencies installed
- Models downloaded
- Directory structure
- Disk space

Usage:
    python backend/verify_setup.py
"""

import sys
import os
from pathlib import Path
import subprocess

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def print_info(text):
    print(f"ℹ  {text}")

# Track overall status
all_checks_passed = True

# ==============================================================================
# 1. Python Version Check
# ==============================================================================

print_header("1. Python Version Check")

python_version = sys.version_info
print_info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

if python_version.major == 3 and python_version.minor == 10:
    print_success("Python 3.10 detected (required)")
else:
    print_error(f"Python 3.10 required, found {python_version.major}.{python_version.minor}")
    print_info("Install with: sudo apt install python3.10 python3.10-venv")
    all_checks_passed = False

# ==============================================================================
# 2. Virtual Environment Check
# ==============================================================================

print_header("2. Virtual Environment Check")

in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

if in_venv:
    print_success("Running in virtual environment")
    print_info(f"Virtual environment: {sys.prefix}")
else:
    print_warning("Not running in virtual environment")
    print_info("Activate with: source backend/venv/bin/activate")

# ==============================================================================
# 3. CUDA & GPU Check
# ==============================================================================

print_header("3. CUDA & GPU Check")

try:
    import torch
    print_success("PyTorch installed")
    print_info(f"PyTorch version: {torch.__version__}")

    if torch.cuda.is_available():
        print_success("CUDA is available")
        print_info(f"CUDA version: {torch.version.cuda}")

        gpu_name = torch.cuda.get_device_name(0)
        print_info(f"GPU: {gpu_name}")

        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print_info(f"VRAM: {vram_gb:.2f} GB")

        if vram_gb >= 11:
            print_success(f"Sufficient VRAM ({vram_gb:.2f} GB >= 11 GB)")
        else:
            print_warning(f"Limited VRAM ({vram_gb:.2f} GB). 12GB recommended.")
    else:
        print_error("CUDA not available")
        print_info("Check: nvidia-smi")
        print_info("Follow: https://docs.nvidia.com/cuda/wsl-user-guide/index.html")
        all_checks_passed = False

except ImportError:
    print_error("PyTorch not installed")
    print_info("Install with: pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu118")
    all_checks_passed = False

# ==============================================================================
# 4. Dependencies Check
# ==============================================================================

print_header("4. Dependencies Check")

required_packages = [
    ('diffusers', '0.24.0'),
    ('transformers', '4.36.0'),
    ('accelerate', '0.25.0'),
    ('xformers', '0.0.23'),
    ('cv2', 'opencv-python'),
    ('PIL', 'Pillow'),
]

missing_packages = []

for package_name, display_name in required_packages:
    try:
        if package_name == 'cv2':
            import cv2
            version = cv2.__version__
        elif package_name == 'PIL':
            from PIL import Image
            import PIL
            version = PIL.__version__
        else:
            module = __import__(package_name)
            version = getattr(module, '__version__', 'unknown')

        print_success(f"{display_name}: {version}")
    except ImportError:
        print_error(f"{display_name} not installed")
        missing_packages.append(display_name)

if missing_packages:
    print_warning(f"Missing packages: {', '.join(missing_packages)}")
    print_info("Install with: pip install -r backend/requirements.txt")
    all_checks_passed = False

# ==============================================================================
# 5. Directory Structure Check
# ==============================================================================

print_header("5. Directory Structure Check")

required_dirs = [
    "/mnt/d/VideoGenerator/models",
    "/mnt/d/VideoGenerator/output",
    "/mnt/d/VideoGenerator/logs",
]

for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print_success(f"{dir_path} exists")
    else:
        print_warning(f"{dir_path} does not exist")
        print_info(f"Create with: mkdir -p {dir_path}")

# ==============================================================================
# 6. Models Check
# ==============================================================================

print_header("6. Models Check")

models_dir = Path("/mnt/d/VideoGenerator/models")

# Check SVD-XT
svd_path = models_dir / "svd-xt"
if svd_path.exists() and svd_path.is_dir():
    file_count = len(list(svd_path.rglob("*")))
    if file_count > 10:
        print_success(f"SVD-XT model found ({file_count} files)")
    else:
        print_warning(f"SVD-XT directory exists but may be incomplete ({file_count} files)")
else:
    print_error("SVD-XT model not found")
    print_info("Download with: python backend/download_models.py")
    all_checks_passed = False

# Check AnimateDiff
animatediff_path = models_dir / "animatediff"
if animatediff_path.exists() and animatediff_path.is_dir():
    file_count = len(list(animatediff_path.rglob("*")))
    if file_count > 5:
        print_success(f"AnimateDiff motion adapter found ({file_count} files)")
    else:
        print_warning(f"AnimateDiff directory exists but may be incomplete ({file_count} files)")
else:
    print_error("AnimateDiff motion adapter not found")
    print_info("Download with: python backend/download_models.py")
    all_checks_passed = False

# Check for SD 1.5 base models
realistic_vision_dir = models_dir / "realistic-vision"
model_count = 0

if realistic_vision_dir.exists():
    safetensors = list(realistic_vision_dir.glob("*.safetensors"))
    model_count += len(safetensors)
    if safetensors:
        print_success(f"Realistic Vision model found: {safetensors[0].name}")

# Check custom models
custom_dir = models_dir / "custom"
if custom_dir.exists():
    custom_safetensors = list(custom_dir.glob("*.safetensors"))
    model_count += len(custom_safetensors)
    if custom_safetensors:
        print_success(f"Custom models found: {len(custom_safetensors)}")
        for model in custom_safetensors:
            print_info(f"  - {model.name}")

if model_count == 0:
    print_warning("No SD 1.5 base models found for AnimateDiff")
    print_info("Download default model: python backend/download_models.py")
    print_info("Or browse CivitAI models via the application")

# ==============================================================================
# 7. Disk Space Check
# ==============================================================================

print_header("7. Disk Space Check")

try:
    stat = os.statvfs(models_dir)
    available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

    print_info(f"Available space on D:\\: {available_gb:.2f} GB")

    if available_gb >= 10:
        print_success("Sufficient disk space")
    elif available_gb >= 5:
        print_warning(f"Low disk space ({available_gb:.2f} GB). 10GB+ recommended for model downloads.")
    else:
        print_error(f"Very low disk space ({available_gb:.2f} GB). Free up space before downloading models.")
        all_checks_passed = False

except Exception as e:
    print_warning(f"Could not check disk space: {e}")

# ==============================================================================
# 8. Backend Scripts Check
# ==============================================================================

print_header("8. Backend Scripts Check")

backend_scripts = [
    "backend/generate.py",
    "backend/test_generation.py",
    "backend/download_models.py",
]

for script in backend_scripts:
    if os.path.exists(script):
        print_success(f"{script} exists")
        # Check if executable
        if os.access(script, os.X_OK):
            print_info(f"  ✓ Executable")
    else:
        print_error(f"{script} not found")
        all_checks_passed = False

# ==============================================================================
# Summary
# ==============================================================================

print_header("Setup Verification Summary")

if all_checks_passed:
    print_success("All critical checks passed!")
    print_info("\nYou can now:")
    print_info("  1. Test generation: python backend/test_generation.py --quick")
    print_info("  2. Start C# application: dotnet run --project VideoGenerator")
    print_info("  3. Generate videos!\n")
    sys.exit(0)
else:
    print_error("Some checks failed. Please review the issues above.")
    print_info("\nCommon fixes:")
    print_info("  - Install Python 3.10: sudo apt install python3.10 python3.10-venv")
    print_info("  - Run setup script: bash scripts/setup_wsl.sh")
    print_info("  - Download models: python backend/download_models.py")
    print_info("  - Check NVIDIA drivers: nvidia-smi\n")
    sys.exit(1)
