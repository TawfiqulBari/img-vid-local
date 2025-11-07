# Troubleshooting Guide

Common issues and their solutions for the Image-to-Video Generator.

---

## Table of Contents

1. [Setup & Installation Issues](#setup--installation-issues)
2. [Python Backend Issues](#python-backend-issues)
3. [CUDA & GPU Issues](#cuda--gpu-issues)
4. [Model Issues](#model-issues)
5. [Generation Errors](#generation-errors)
6. [VRAM & Memory Issues](#vram--memory-issues)
7. [C# Application Issues](#c-application-issues)
8. [Path & File Issues](#path--file-issues)
9. [Performance Issues](#performance-issues)
10. [CivitAI Model Browser Issues](#civitai-model-browser-issues)

---

## Setup & Installation Issues

### Issue: "Python 3.10 not found"

**Symptoms:**
- setup_wsl.sh fails with "Python 3.10 not found"
- `python3.10 --version` returns "command not found"

**Solution:**
```bash
# Install Python 3.10
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# Verify installation
python3.10 --version
```

---

### Issue: "pip: command not found" after venv activation

**Symptoms:**
- Virtual environment activates but pip is missing
- `pip --version` returns error

**Solution:**
```bash
# Recreate virtual environment
rm -rf backend/venv
python3.10 -m venv backend/venv
source backend/venv/bin/activate

# Upgrade pip
python -m ensurepip --upgrade
pip install --upgrade pip
```

---

### Issue: "Permission denied" when running scripts

**Symptoms:**
- `bash: ./script.sh: Permission denied`

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/setup_wsl.sh
chmod +x scripts/test_integration.sh
chmod +x backend/generate.py
chmod +x backend/test_generation.py
chmod +x backend/verify_setup.py

# Or run with bash explicitly
bash scripts/setup_wsl.sh
```

---

## Python Backend Issues

### Issue: "Python backend not available"

**Symptoms:**
- C# application shows "Backend not available" warning on startup
- "Refresh Models" button returns no models

**Diagnosis:**
```bash
# Test backend directly
source backend/venv/bin/activate
python backend/generate.py --list-models
```

**Solution 1: Virtual environment not activated**
```bash
source backend/venv/bin/activate
python backend/generate.py --list-models
```

**Solution 2: Dependencies not installed**
```bash
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

**Solution 3: Python path issue in C#**
Check that C# application can find Python executable. Edit `Services/PythonBackendService.cs` if needed.

---

### Issue: Import errors (diffusers, torch, etc.)

**Symptoms:**
- `ModuleNotFoundError: No module named 'diffusers'`
- `ImportError: cannot import name...`

**Solution:**
```bash
# Ensure virtual environment is activated
source backend/venv/bin/activate

# Reinstall dependencies
pip install --no-cache-dir -r backend/requirements.txt

# Verify key packages
python -c "import torch; print(torch.__version__)"
python -c "import diffusers; print(diffusers.__version__)"
```

---

## CUDA & GPU Issues

### Issue: "CUDA not available" / "torch.cuda.is_available() returns False"

**Symptoms:**
- `python scripts/check_gpu.py` shows "CUDA not available"
- Generation attempts fail with CUDA errors

**Diagnosis:**
```bash
# Check if nvidia-smi works in WSL
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

**Solution 1: NVIDIA drivers not installed in WSL**
Follow official guide: https://docs.nvidia.com/cuda/wsl-user-guide/index.html

Key steps:
1. Install latest NVIDIA drivers on Windows (not in WSL!)
2. Ensure WSL 2 is being used (`wsl --list --verbose`)
3. Test: `nvidia-smi` in WSL should show GPU

**Solution 2: Wrong PyTorch version**
```bash
# Uninstall existing PyTorch
pip uninstall torch torchvision torchaudio

# Install with CUDA 11.8
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu118
```

**Solution 3: WSL 1 instead of WSL 2**
```powershell
# In Windows PowerShell (as Administrator)
wsl --set-version Ubuntu-22.04 2
wsl --set-default-version 2
```

---

### Issue: "nvidia-smi works but PyTorch can't find CUDA"

**Symptoms:**
- `nvidia-smi` shows GPU
- `torch.cuda.is_available()` returns False

**Solution:**
```bash
# Check CUDA version from nvidia-smi
nvidia-smi
# Note the CUDA version (should be 11.x or 12.x)

# Reinstall matching PyTorch
pip uninstall torch torchvision torchaudio

# For CUDA 11.8
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu118
```

---

## Model Issues

### Issue: "Model not found" / "No models available"

**Symptoms:**
- `python backend/generate.py --list-models` returns empty list
- Model dropdown in C# app is empty

**Diagnosis:**
```bash
# Check if models directory exists
ls -la /mnt/d/VideoGenerator/models/

# Check for SVD-XT
ls -la /mnt/d/VideoGenerator/models/svd-xt/

# Check for AnimateDiff
ls -la /mnt/d/VideoGenerator/models/animatediff/
```

**Solution:**
```bash
# Download models
python backend/download_models.py

# Or download specific models
python backend/download_models.py --models svd animatediff
```

---

### Issue: "Model files corrupted" / incomplete download

**Symptoms:**
- Models download but generation fails
- "Model loading error" messages

**Solution:**
```bash
# Remove incomplete models
rm -rf /mnt/d/VideoGenerator/models/svd-xt
rm -rf /mnt/d/VideoGenerator/models/animatediff

# Re-download
python backend/download_models.py
```

---

### Issue: Custom model not detected after download

**Symptoms:**
- Downloaded .safetensors from CivitAI browser
- Model doesn't appear in dropdown

**Solution:**
1. **Restart the C# application** (models are discovered on startup)
2. Check file location: `D:\VideoGenerator\models\custom\*.safetensors`
3. Ensure AnimateDiff motion adapter is downloaded:
```bash
ls /mnt/d/VideoGenerator/models/animatediff/
```
4. Click "Refresh Models" in application

---

## Generation Errors

### Issue: "Prompt is required and cannot be empty"

**Symptoms:**
- Generation fails immediately with prompt error

**Solution:**
- Enter a text prompt (minimum 3 characters)
- Examples: "slow zoom in", "dramatic lighting", "person walking"
- Prompts are REQUIRED for all generations in this application

---

### Issue: "Image file not found"

**Symptoms:**
- Selected image but generation fails with "not found" error

**Solution 1: Path with spaces or special characters**
- Avoid paths with spaces
- Use paths like: `D:\Images\test.jpg` not `D:\My Images\test image.jpg`

**Solution 2: Path conversion issue**
```bash
# Test path conversion
python -c "
from utils.path_utils import windows_to_wsl_path
print(windows_to_wsl_path('D:\\\\Images\\\\test.jpg'))
"
```

---

### Issue: Generation freezes / hangs

**Symptoms:**
- Progress bar stuck
- No error messages
- Application appears frozen

**Diagnosis:**
1. Check if Python process is running:
```bash
ps aux | grep python
```

2. Check VRAM usage:
```bash
nvidia-smi
```

**Solution 1: First-time model loading**
- First generation takes 30-60s to load model into VRAM
- Subsequent generations are faster
- Be patient!

**Solution 2: Insufficient VRAM**
- See [VRAM & Memory Issues](#vram--memory-issues)

**Solution 3: Python process crashed**
- Click "Cancel" in UI
- Check WSL terminal for error messages
- Try with lower parameters (fewer frames, smaller resolution)

---

### Issue: "Generation failed" with no specific error

**Symptoms:**
- Generation starts but fails quickly
- Error message is generic

**Diagnosis:**
```bash
# Run backend directly to see detailed errors
source backend/venv/bin/activate

# Test with minimal params
python backend/test_generation.py --quick
```

Look for specific error messages in output.

---

## VRAM & Memory Issues

### Issue: "Out of VRAM" / CUDA out of memory error

**Symptoms:**
- `torch.cuda.OutOfMemoryError`
- Generation fails partway through

**Solution 1: Reduce parameters**
- **Frames**: 25 → 14
- **Resolution**: 1024x576 → 512x512
- **Decode chunk size** (Advanced): 4 → 2

**Solution 2: Close other GPU applications**
```bash
# Check what's using GPU
nvidia-smi

# Close: games, other AI tools, Chrome with hardware acceleration, etc.
```

**Solution 3: Let optimizer handle it**
The application automatically optimizes parameters for VRAM. If it still fails:
- Use SVD instead of AnimateDiff (uses less VRAM)
- Generate shorter videos
- Lower resolution

**Solution 4: Clear CUDA cache**
```bash
python -c "import torch; torch.cuda.empty_cache()"
```

---

### Issue: "System out of memory" (RAM, not VRAM)

**Symptoms:**
- System becomes very slow
- Windows shows high memory usage
- Application crashes without CUDA error

**Solution:**
- Close unnecessary applications
- Restart computer to free RAM
- Upgrade RAM if consistently running into this (16GB+ recommended)

---

## C# Application Issues

### Issue: ".NET 6.0 not found"

**Symptoms:**
- Application won't launch
- "You must install .NET to run this application"

**Solution:**
Download and install .NET 6.0 Runtime:
https://dotnet.microsoft.com/download/dotnet/6.0

Or for development, install .NET 6.0 SDK.

---

### Issue: "VideoGenerator.exe crashes on startup"

**Symptoms:**
- Application starts then immediately closes
- No error message

**Solution 1: Run from terminal to see errors**
```powershell
cd VideoGenerator\bin\Release\net6.0-windows\
.\VideoGenerator.exe
```

Check console output for specific error.

**Solution 2: Missing dependencies**
```powershell
# Rebuild application
cd VideoGenerator
dotnet clean
dotnet restore
dotnet build --configuration Release
```

---

### Issue: Video preview doesn't play

**Symptoms:**
- Video generated successfully
- Preview area remains black
- No error message

**Solution 1: Missing codec**
- Install K-Lite Codec Pack or Windows Media Feature Pack
- Ensure MP4 codec support

**Solution 2: File path issue**
- Check that video file exists at returned path
- Verify path conversion (WSL → Windows)

**Solution 3: MediaElement issue**
- Try opening video file directly in Windows Media Player
- If plays there, it's a WPF/MediaElement issue

---

## Path & File Issues

### Issue: "D:\ drive not accessible from WSL"

**Symptoms:**
- `/mnt/d/` doesn't exist in WSL
- Models can't be saved

**Diagnosis:**
```bash
# List mounted drives
ls /mnt/

# Try to access D:
cd /mnt/d
```

**Solution 1: D: drive not mounted**
```bash
# Mount D: drive
sudo mkdir -p /mnt/d
sudo mount -t drvfs D: /mnt/d
```

**Solution 2: Use different drive**
Edit model paths in code to use C: or another drive:
```python
# In backend code, change:
models_dir = "/mnt/c/VideoGenerator/models"  # Instead of /mnt/d/
```

---

### Issue: Path conversion errors (Windows ↔ WSL)

**Symptoms:**
- "File not found" errors despite file existing
- Path looks wrong in error messages

**Diagnosis:**
```bash
# Test path conversion
python -c "
from utils.path_utils import windows_to_wsl_path, wsl_to_windows_path

win_path = 'D:\\\\VideoGenerator\\\\models'
wsl_path = windows_to_wsl_path(win_path)
back_to_win = wsl_to_windows_path(wsl_path)

print(f'Windows: {win_path}')
print(f'WSL: {wsl_path}')
print(f'Back to Windows: {back_to_win}')
"
```

**Solution:**
Path conversion should work automatically. If not, check:
- Backslashes are properly escaped in Windows paths
- WSL paths start with `/mnt/`

---

## Performance Issues

### Issue: Generation is very slow

**Symptoms:**
- SVD takes >5 minutes for 25 frames
- AnimateDiff takes >10 minutes

**Diagnosis:**
1. Check if GPU is being used:
```bash
# During generation, run:
nvidia-smi

# GPU utilization should be 90-100%
```

2. Check if xformers is enabled:
```bash
python -c "import xformers; print(xformers.__version__)"
```

**Solution 1: GPU not being used**
- See [CUDA & GPU Issues](#cuda--gpu-issues)
- Ensure CUDA is available

**Solution 2: Xformers not installed**
```bash
pip install xformers==0.0.23
```

**Solution 3: Slow storage (HDD instead of SSD)**
- Consider moving models to SSD if on HDD
- Or accept slower performance

**Solution 4: Background processes**
- Close unnecessary applications
- Disable Windows indexing on D:\VideoGenerator\
- Check Task Manager for CPU/GPU usage

---

### Issue: First generation very slow, subsequent ones fast

**Symptoms:**
- First video: 2-3 minutes
- Second video: 30-60 seconds

**This is normal!**
- First generation loads model into VRAM (30-60s)
- Model stays loaded for subsequent generations
- Expected behavior

---

## CivitAI Model Browser Issues

### Issue: "Models catalog not found"

**Symptoms:**
- Model browser won't open
- Error about catalog file missing

**Solution:**
Ensure `backend/models_catalog.json` exists. If missing:
1. Re-clone repository
2. Or manually download catalog from repository

---

### Issue: Model download fails

**Symptoms:**
- Download starts but fails partway
- "Download failed" error

**Solution 1: Internet connection**
- Check internet connection
- CivitAI might be down (check status)
- Try again later

**Solution 2: Disk space**
```bash
# Check available space
df -h /mnt/d
```
Ensure at least 5GB free for downloads.

**Solution 3: Manual download**
1. Visit model page on CivitAI directly
2. Download .safetensors file manually
3. Place in: `D:\VideoGenerator\models\custom\`
4. Restart application

---

### Issue: Downloaded model doesn't work

**Symptoms:**
- Model appears in dropdown
- Generation fails with model error

**Solution:**
1. Ensure model is SD 1.5 based (NOT SDXL or SD 2.x)
2. Ensure AnimateDiff motion adapter is downloaded
3. Try with another model first to isolate issue

---

## Still Having Issues?

### Diagnostic Checklist

Run these commands and note the results:

```bash
# 1. Environment verification
python backend/verify_setup.py

# 2. GPU check
python scripts/check_gpu.py

# 3. Model list
python backend/generate.py --list-models

# 4. VRAM stats
python backend/generate.py --vram-stats

# 5. Integration test
bash scripts/test_integration.sh --quick
```

### Collect Information

When reporting issues, include:
1. Output of verification script
2. GPU model and VRAM
3. WSL version (`wsl --list --verbose`)
4. Python version (`python --version`)
5. Exact error message
6. Steps to reproduce

### Reset Everything

If all else fails, complete reset:

```bash
# 1. Remove virtual environment
rm -rf backend/venv

# 2. Remove models
rm -rf /mnt/d/VideoGenerator/models/*

# 3. Re-run setup
bash scripts/setup_wsl.sh

# 4. Re-download models
python backend/download_models.py

# 5. Rebuild C# application
cd VideoGenerator
dotnet clean
dotnet build --configuration Release
```

---

## Helpful Resources

- **CUDA WSL Guide:** https://docs.nvidia.com/cuda/wsl-user-guide/
- **PyTorch Installation:** https://pytorch.org/get-started/locally/
- **Diffusers Documentation:** https://huggingface.co/docs/diffusers/
- **CivitAI:** https://civitai.com/

---

## Report a Bug

If you've found a bug that's not covered here:
1. Check existing issues on GitHub
2. Create a new issue with:
   - Detailed description
   - Steps to reproduce
   - Environment info (OS, GPU, versions)
   - Error messages and logs
   - Screenshots if applicable

---

**Good luck!** Most issues are environment-related and can be resolved by carefully following the setup instructions. 🚀
