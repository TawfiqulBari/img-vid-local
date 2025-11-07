# Quick Start Guide - Image-to-Video Generator

Get up and running in 30 minutes! ⚡

---

## 📋 Prerequisites

Before you begin, ensure you have:

✅ **Hardware:**
- NVIDIA RTX 3060 (12GB VRAM) or similar
- 30GB+ free disk space on D:\ drive
- 16GB+ RAM recommended

✅ **Software:**
- Windows 10/11 (64-bit)
- WSL 2 (Windows Subsystem for Linux)
- .NET 6.0 Runtime or SDK

---

## 🚀 Step 1: Install WSL 2 (if not already installed)

Open PowerShell as Administrator and run:

```powershell
wsl --install -d Ubuntu-22.04
```

Restart your computer when prompted.

After restart, set up your Ubuntu username and password.

**Verify WSL 2:**
```powershell
wsl --list --verbose
```

You should see Ubuntu-22.04 with VERSION 2.

---

## 🔧 Step 2: Set Up Python Environment in WSL

Open Ubuntu (WSL) terminal and run:

```bash
# Navigate to project directory
cd /mnt/c/path/to/image-video-3  # Adjust path as needed

# Run automated setup script
bash scripts/setup_wsl.sh
```

This script will:
- ✅ Install Python 3.10
- ✅ Create virtual environment
- ✅ Install PyTorch with CUDA 11.8
- ✅ Install all dependencies
- ✅ Create directory structure on D:\

**Time:** ~10-15 minutes

---

## 📥 Step 3: Download AI Models

Still in WSL terminal:

```bash
# Activate virtual environment (if not already active)
source backend/venv/bin/activate

# Download models (SVD-XT, AnimateDiff, Realistic Vision)
python backend/download_models.py
```

**Time:** ~20-40 minutes (depends on internet speed)
**Size:** ~15GB total

**What's being downloaded:**
- SVD-XT (~10GB) - Fast realistic video generation
- AnimateDiff (~3GB) - Motion adapter
- Realistic Vision v5.1 (~2GB) - Photorealistic base model

---

## ✅ Step 4: Verify Setup

```bash
# Run verification script
python backend/verify_setup.py
```

You should see ✅ for all critical checks:
- Python 3.10
- CUDA available
- Dependencies installed
- Models downloaded

If any checks fail, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## 🎬 Step 5: Test Video Generation (Optional but Recommended)

```bash
# Quick test (30-60 seconds)
python backend/test_generation.py --quick

# Full test with both pipelines (2-3 minutes)
python backend/test_generation.py
```

Videos will be saved to: `D:\VideoGenerator\output\`

---

## 🖥️ Step 6: Build C# Application

Open PowerShell or Command Prompt in the project root:

```powershell
# Navigate to C# project
cd VideoGenerator

# Build application
dotnet build --configuration Release

# Or open in Visual Studio 2022
start VideoGenerator.sln
```

**Time:** ~1-2 minutes

---

## ▶️ Step 7: Run the Application

### Option A: From Command Line
```powershell
cd VideoGenerator
dotnet run
```

### Option B: From Visual Studio
1. Open `VideoGenerator.sln`
2. Press F5 or click "Start"

### Option C: Run Executable Directly
```
VideoGenerator\bin\Release\net6.0-windows\VideoGenerator.exe
```

---

## 🎨 Step 8: Generate Your First Video!

1. **Click "Browse Image"** and select a photo
2. **Enter a prompt:** e.g., "slow cinematic zoom in, dramatic lighting"
3. **Select model:** SVD-XT (for beginners)
4. **Adjust parameters:** (or keep defaults)
   - Frames: 25
   - FPS: 8
   - Resolution: 1024x576
5. **Click "Generate Video"**
6. **Wait 30-90 seconds** ⏱️
7. **Watch your video!** 🎉

---

## 🔥 Step 9: Download NSFW Models (Optional)

In the application:

1. Click **"🔥 Browse CivitAI Models (NSFW)"**
2. Browse the curated catalog of 6 models
3. Click on any model to see details
4. Click **"📥 Download Model"**
5. Wait for download (~2GB, 10-30 minutes)
6. Restart application
7. New model appears in dropdown!

**Recommended NSFW models:**
- **URPM v2.3** - Best for explicit NSFW (Level 60)
- **ChilloutMix** - Best for Asian faces (Level 60)
- **epiCRealism** - Best texture & cinematic (Level 31)

---

## 📊 Quick Reference

### Generation Times (RTX 3060)
| Pipeline | Resolution | Frames | Time |
|----------|------------|--------|------|
| SVD | 512x512 | 25 | 30-60s |
| SVD | 1024x576 | 25 | 60-90s |
| AnimateDiff | 512x512 | 24 | 45-90s |

### VRAM Usage
| Pipeline | Resolution | VRAM |
|----------|------------|------|
| SVD | 512x512 | 7-8GB |
| SVD | 1024x576 | 9-10GB |
| AnimateDiff | 512x512 | 8-9GB |

### Recommended Parameters

**For Speed (SVD):**
- Frames: 14-25
- FPS: 8
- Resolution: 512x512
- Steps: 15-20

**For Quality (AnimateDiff):**
- Frames: 24-48
- FPS: 16-24
- Resolution: 512x512
- Steps: 25-30
- Guidance: 7-8

---

## 🎯 Common Workflows

### Workflow 1: Quick Test Video
1. Select any image
2. Use SVD-XT model
3. Prompt: "slow zoom in"
4. 25 frames @ 8 FPS
5. Generate → ~30 seconds

### Workflow 2: Cinematic Scene
1. Select landscape/portrait image
2. Use SVD-XT model
3. Prompt: "cinematic dolly shot, smooth camera movement, dramatic lighting"
4. 60 frames @ 24 FPS @ 1024x576
5. Generate → ~90 seconds

### Workflow 3: Character Animation
1. Select character image
2. Use AnimateDiff + URPM/Realistic Vision
3. Prompt: "person turning head slowly, wind blowing through hair, golden hour lighting"
4. Negative: "blurry, static, distorted"
5. 48 frames @ 16 FPS
6. Generate → ~90 seconds

### Workflow 4: NSFW Content (Private Use)
1. Download URPM or ChilloutMix via model browser
2. Select appropriate image
3. Use explicit prompts (as desired)
4. Use negative prompts for control
5. AnimateDiff for best prompt adherence
6. Generate responsibly! (18+, private use only)

---

## 🆘 Troubleshooting Quick Fixes

### "Python backend not available"
```bash
# In WSL, activate venv and test
source backend/venv/bin/activate
python backend/generate.py --list-models
```

### "CUDA not available"
```bash
# Check NVIDIA drivers in WSL
nvidia-smi

# If not working, reinstall CUDA drivers for WSL
# Follow: https://docs.nvidia.com/cuda/wsl-user-guide/
```

### "Out of VRAM"
- Reduce number of frames
- Lower resolution (512x512)
- Set decode_chunk_size to 2 (Advanced Settings)
- Close other GPU applications

### "Model not found"
```bash
# Re-download models
python backend/download_models.py
```

For more detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## 📚 Next Steps

**Learn More:**
- Read [README.md](README.md) for detailed overview
- Check [plans/SPEC.md](plans/SPEC.md) for technical details
- Review [plans/MODELS.md](plans/MODELS.md) for model information

**Advanced Usage:**
- Experiment with different models
- Try custom prompts and negative prompts
- Adjust generation parameters for different effects
- Download custom models from CivitAI

**Get Help:**
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review test results: `bash scripts/test_integration.sh`
- Run verification: `python backend/verify_setup.py`

---

## 🎉 You're Ready!

Congratulations! You can now generate AI videos from images. Have fun and be creative! 🚀

**Remember:**
- ⚠️ NSFW models are for private use only (18+)
- 💾 Videos save to `D:\VideoGenerator\output\`
- 🔄 First generation is slow (model loading), subsequent ones are faster
- 💪 RTX 3060 can handle most settings within VRAM limits

**Happy generating!** 🎬✨
