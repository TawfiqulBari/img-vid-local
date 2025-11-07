#!/usr/bin/env python3
"""
GPU and CUDA Verification Script

Checks if NVIDIA GPU is accessible and CUDA is properly configured.
Run this before attempting model downloads or video generation.

Usage:
    python scripts/check_gpu.py
    # Or make executable: chmod +x scripts/check_gpu.py && ./scripts/check_gpu.py
"""

import sys
import subprocess
import platform


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def check_python_version():
    """Check if Python version is 3.10"""
    print_header("Python Version Check")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"Python Version: {version_str}")

    if version.major == 3 and version.minor == 10:
        print_success(f"Python 3.10.x detected - Perfect!")
        return True
    elif version.major == 3 and version.minor >= 10:
        print_warning(f"Python {version_str} detected - Should work, but 3.10 is recommended")
        return True
    else:
        print_error(f"Python {version_str} detected - Need Python 3.10+")
        print_info("Install Python 3.10: sudo apt install python3.10 python3.10-venv")
        return False


def check_nvidia_smi():
    """Check if nvidia-smi is available and working"""
    print_header("NVIDIA Driver Check")

    try:
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print_success("nvidia-smi is accessible")
            print("\nGPU Information:")
            print("-" * 70)

            # Parse output for key information
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Driver Version' in line or 'CUDA Version' in line:
                    print(line.strip())
                if 'GeForce' in line or 'RTX' in line or 'GTX' in line:
                    print(line.strip())

            print("-" * 70)
            return True
        else:
            print_error("nvidia-smi returned an error")
            print(result.stderr)
            return False

    except FileNotFoundError:
        print_error("nvidia-smi not found")
        print_info("NVIDIA drivers may not be installed in WSL")
        print_info("Follow: https://docs.nvidia.com/cuda/wsl-user-guide/index.html")
        return False
    except subprocess.TimeoutExpired:
        print_error("nvidia-smi timed out")
        return False
    except Exception as e:
        print_error(f"Unexpected error running nvidia-smi: {e}")
        return False


def check_pytorch():
    """Check if PyTorch is installed and can access CUDA"""
    print_header("PyTorch and CUDA Check")

    try:
        import torch
        print_success(f"PyTorch {torch.__version__} is installed")

        # Check CUDA availability
        if torch.cuda.is_available():
            print_success("CUDA is available to PyTorch!")

            # Get device information
            device_count = torch.cuda.device_count()
            print(f"\nNumber of CUDA devices: {device_count}")

            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                device_capability = torch.cuda.get_device_capability(i)
                total_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)

                print(f"\nDevice {i}: {device_name}")
                print(f"  Compute Capability: {device_capability[0]}.{device_capability[1]}")
                print(f"  Total VRAM: {total_memory:.2f} GB")

                # Check if it's RTX 3060
                if '3060' in device_name:
                    print_success("RTX 3060 detected - Perfect for this application!")
                    if total_memory < 11.5:
                        print_warning(f"VRAM shows {total_memory:.2f}GB - Expected ~12GB")
                        print_info("Some VRAM may be reserved by system")
                elif total_memory < 12:
                    print_warning(f"GPU has {total_memory:.2f}GB VRAM - May struggle with larger videos")
                    print_info("Recommended: 12GB+ VRAM (RTX 3060 or better)")

            # Test CUDA with a simple operation
            print("\nTesting CUDA with tensor operation...")
            try:
                x = torch.rand(5, 3).cuda()
                y = torch.rand(5, 3).cuda()
                z = x + y
                print_success("CUDA tensor operations working!")

                # Clean up
                del x, y, z
                torch.cuda.empty_cache()

            except Exception as e:
                print_error(f"CUDA test failed: {e}")
                return False

            return True
        else:
            print_error("CUDA is NOT available to PyTorch")
            print_info("PyTorch may be installed without CUDA support")
            print_info("Reinstall with: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            return False

    except ImportError:
        print_warning("PyTorch is not installed yet")
        print_info("This is normal if you haven't run setup yet")
        print_info("PyTorch will be installed by setup_wsl.sh or requirements.txt")
        return None  # None = not yet installed (not an error)


def check_system_info():
    """Display system information"""
    print_header("System Information")

    print(f"Platform: {platform.system()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Kernel: {platform.release()}")

    # Check if running in WSL
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().lower()
            if 'microsoft' in version or 'wsl' in version:
                print_success("Running in WSL (Windows Subsystem for Linux)")
            else:
                print_info("Running in native Linux")
    except:
        pass


def check_disk_space():
    """Check available disk space for models"""
    print_header("Disk Space Check")

    try:
        # Check current directory
        result = subprocess.run(
            ['df', '-h', '.'],
            capture_output=True,
            text=True
        )

        print("Current directory:")
        print(result.stdout)

        # Check /mnt/d if it exists (Windows D: drive)
        import os
        if os.path.exists('/mnt/d'):
            result = subprocess.run(
                ['df', '-h', '/mnt/d'],
                capture_output=True,
                text=True
            )
            print("\nD:\\ drive (for models):")
            print(result.stdout)

            # Parse to check if >= 20GB available
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 4:
                    available = parts[3]
                    print_info(f"Available space on D:\\: {available}")
                    print_info("Need at least 20GB for models (~15GB models + 5GB buffer)")
        else:
            print_warning("/mnt/d not found - D:\\ drive may not be accessible from WSL")
            print_info("Models should be stored on D:\\VideoGenerator\\models\\")

    except Exception as e:
        print_warning(f"Could not check disk space: {e}")


def main():
    """Run all checks"""
    print("\n" + "=" * 70)
    print("  IMAGE-TO-VIDEO GENERATOR - GPU VERIFICATION")
    print("=" * 70)

    checks_passed = []
    checks_failed = []
    checks_pending = []

    # Run checks
    if check_python_version():
        checks_passed.append("Python Version")
    else:
        checks_failed.append("Python Version")

    check_system_info()
    check_disk_space()

    if check_nvidia_smi():
        checks_passed.append("NVIDIA Drivers")
    else:
        checks_failed.append("NVIDIA Drivers")

    pytorch_result = check_pytorch()
    if pytorch_result is True:
        checks_passed.append("PyTorch + CUDA")
    elif pytorch_result is False:
        checks_failed.append("PyTorch + CUDA")
    else:
        checks_pending.append("PyTorch (not installed yet)")

    # Summary
    print_header("Summary")

    if checks_passed:
        print_success(f"Passed ({len(checks_passed)}): {', '.join(checks_passed)}")

    if checks_pending:
        print_info(f"Pending ({len(checks_pending)}): {', '.join(checks_pending)}")

    if checks_failed:
        print_error(f"Failed ({len(checks_failed)}): {', '.join(checks_failed)}")
        print("\n❌ GPU setup is incomplete. Please fix the issues above.")
        return 1
    elif not checks_pending:
        print("\n✅ All checks passed! GPU is ready for video generation.")
        return 0
    else:
        print("\n⚠️  Basic checks passed. Run again after installing dependencies.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
