# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An **offline image-to-video generator** with text prompt control, designed for local execution on RTX 3060 (12GB VRAM). Transforms static images into animated videos using dual AI model support with unrestricted generation for private use.

**Key Features:**
- **Dual Model Support**: SVD-XT (fast) + AnimateDiff (high control)
- **Required Text Prompts**: User guides animation via detailed text descriptions
- **NSFW-Capable**: No content filters - full user autonomy
- **Custom Models**: Load .safetensors from CivitAI
- **100% Offline**: All processing local after initial setup

**Key Architecture:**
- **Development**: WSL (Ubuntu) for Python backend development
- **Frontend**: WPF/C# desktop application (Windows-only)
- **Backend**: Python AI inference engine (dual pipelines)
- **Models**: SVD-XT, AnimateDiff motion adapter, custom SD 1.5 models
- **Storage**: Models on D:\ drive (accessible from WSL via `/mnt/d/`)
- **Communication**: C# ↔ Python via subprocess with JSON
- **Deployment**: Windows desktop application

## Technology Stack

### Frontend (WPF/C#)
- .NET 6.0+ with WPF
- Windows-only desktop application
- XAML for UI definition
- System.Text.Json for JSON serialization
- Process-based communication with Python backend

### Backend (Python)
- **Python 3.10** (required for compatibility)
- **PyTorch with CUDA 11.8** for GPU acceleration
- **diffusers** library for model inference
- **transformers**, **accelerate**, **safetensors**
- **xformers** for memory-efficient attention
- **opencv-python** and **Pillow** for image/video processing

### AI Models
- **SVD-XT**: Stable Video Diffusion from Stability AI (fast, limited text conditioning)
- **AnimateDiff**: Motion adapter for Stable Diffusion 1.5 models (strong text conditioning)
- **Custom Models**: .safetensors files from CivitAI (Realistic Vision, DreamShaper, etc.)
- **NSFW Support**: All safety checkers intentionally disabled for unrestricted private use

## WSL Development Workflow

### Environment
- **Development OS**: WSL 2 (Ubuntu 22.04)
- **Deployment OS**: Windows 10/11
- **Code Location**: `~/personal-projects/image-video-3/` (WSL filesystem)
- **Model Storage**: `D:\VideoGenerator\models\` (Windows drive, accessed via `/mnt/d/`)
- **IDE**: VS Code with WSL extension (recommended)

### Why WSL?
- Better Python/Linux tooling for AI/ML development
- Faster filesystem operations for code
- Native package management (apt, pip)
- Consistent with dup-checker development methodology
- WPF development can still happen in VS Code or Visual Studio

### Path Conversion (Critical!)

**Always use correct paths for each environment:**

**Python Code** (runs in WSL):
```python
# Use /mnt/d/ for Windows drives
model_path = "/mnt/d/VideoGenerator/models/svd-xt"
output_path = "/mnt/d/VideoGenerator/output/video.mp4"
```

**C# Code** (runs on Windows):
```csharp
// Use D:\ for Windows drives
string modelPath = @"D:\VideoGenerator\models\svd-xt";
string outputPath = @"D:\VideoGenerator\output\video.mp4";
```

**Conversion Utilities**:
- Python: `backend/utils/path_utils.py` (windows_to_wsl_path, wsl_to_windows_path)
- C#: `frontend/Services/PathUtils.cs` (WindowsToWSLPath, WSLToWindowsPath)

## Development Commands

```bash
# In WSL - Automated setup
cd ~/personal-projects/image-video-3
bash scripts/setup_wsl.sh

# Or manual setup:
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

### Python Backend Setup (Manual)

```bash
# Navigate to project (in WSL)
cd ~/personal-projects/image-video-3/backend

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install PyTorch with CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install all dependencies
pip install -r requirements.txt

# Verify GPU access
python check_gpu.py
```

### Download Models (to D:\ drive)

```bash
# In WSL with venv activated
cd ~/personal-projects/image-video-3
source backend/venv/bin/activate

# Download all models (~15GB)
python backend/download_models.py

# Models will be downloaded to /mnt/d/VideoGenerator/models/
# - svd-xt/              (~10GB)
# - animatediff/         (~3GB)
# - realistic-vision/    (~2GB)
```

### Run Python Backend (Testing)

```bash
# In WSL
cd ~/personal-projects/image-video-3
source backend/venv/bin/activate

# Test SVD pipeline
python backend/generate.py '{
  "pipeline": "svd",
  "imagePath": "/mnt/d/test.jpg",
  "prompt": "slow zoom in, cinematic",
  "numFrames": 25,
  "fps": 8,
  "outputPath": "/mnt/d/VideoGenerator/output/test.mp4"
}'

# Test AnimateDiff pipeline
python backend/generate.py '{
  "pipeline": "animatediff",
  "baseModel": "/mnt/d/VideoGenerator/models/realistic-vision/model.safetensors",
  "imagePath": "/mnt/d/test.jpg",
  "prompt": "person turning head, wind blowing hair",
  "negativePrompt": "blurry, low quality",
  "numFrames": 48,
  "fps": 16,
  "outputPath": "/mnt/d/VideoGenerator/output/test_ad.mp4"
}'
```

### C# Frontend Build

```bash
# From WSL
cd ~/personal-projects/image-video-3/frontend
dotnet build VideoGenerator.sln

# Run on Windows (if .NET Runtime installed)
dotnet run --project VideoGenerator

# Or open in Visual Studio (Windows)
# File → Open → \\wsl$\Ubuntu\home\tawfiq\personal-projects\image-video-3\frontend\VideoGenerator.sln
```

## Architecture Details

### Dual Pipeline System

**Backend Structure:**
```
backend/
├── generate.py                 # CLI entry point (routes to pipelines)
├── pipelines/
│   ├── base_pipeline.py       # Abstract base class
│   ├── svd_pipeline.py        # SVD-XT implementation
│   └── animatediff_pipeline.py # AnimateDiff implementation
├── services/
│   ├── video_service.py       # High-level API
│   └── model_manager.py       # Model loading/caching
└── utils/
    ├── path_utils.py          # Windows ↔ WSL conversion
    ├── vram_utils.py          # VRAM optimization
    └── prompt_utils.py        # Prompt validation/enhancement
```

### SVD Pipeline (`pipelines/svd_pipeline.py`)

**Characteristics:**
- **Speed**: Fast generation (2-3 min for 25 frames)
- **Text Conditioning**: Limited (prompts have moderate effect)
- **Best For**: Quick generations, general animations
- **Safety Checker**: DISABLED (`self.pipe.safety_checker = None`)

**Key Parameters:**
- `prompt`: Text guidance (required, limited effect in SVD)
- `num_frames`: Total frames (25-250 depending on resolution/VRAM)
- `fps`: Output framerate (8, 12, 16, or 24)
- `motion_bucket_id`: Motion intensity (1-255, default 127)
- `decode_chunk_size`: VRAM management (2, 4, or 8)
- `num_inference_steps`: Quality vs speed (15-50)
- `seed`: Reproducibility (-1 for random)

### AnimateDiff Pipeline (`pipelines/animatediff_pipeline.py`)

**Characteristics:**
- **Speed**: Moderate (4-6 min for 48 frames)
- **Text Conditioning**: Strong (prompts heavily influence output)
- **Best For**: Precise control, specific actions, NSFW content
- **Safety Checker**: DISABLED (`load_safety_checker=False`)
- **Custom Models**: Loads .safetensors from CivitAI

**Key Parameters:**
- `prompt`: Text guidance (required, strong effect)
- `negativePrompt`: What to avoid (e.g., "blurry, low quality")
- `baseModel`: Path to SD 1.5 model (.safetensors)
- `motionAdapter`: Path to AnimateDiff motion module
- `guidanceScale`: Prompt adherence strength (1-15, default 7.5)
- `num_frames`: Total frames (16-64 depending on VRAM)
- `fps`: Output framerate
- `numInferenceSteps`: Quality vs speed (20-50)

### C# Frontend (`MainWindow.xaml.cs`)

The desktop UI provides:
1. **Image Input**: Drag-drop or file browser for source images
2. **Model Selection**: Radio buttons for SVD vs AnimateDiff vs Custom
3. **Prompt Input**: **REQUIRED** text field for animation description
4. **Negative Prompt**: Optional field to specify what to avoid
5. **Parameter Controls**: Sliders/dropdowns for duration, FPS, quality, etc.
6. **Python Communication**: Spawns subprocess with JSON parameters
7. **Video Preview**: MediaElement for playback
8. **Export**: Save generated videos to user-specified location

**Critical UI Validation:**
- Prompt field must NOT be empty (show error if user attempts generation without prompt)
- Model selection determines which parameters are visible (AnimateDiff shows more options)
- VRAM estimation shown to user before generation

### Communication Flow

```
C# Application
    ↓ (Serialize parameters to JSON)
    ↓ (Spawn python.exe process)
Python Backend (generate.py)
    ↓ (Parse JSON args)
    ↓ (Load model)
    ↓ (Generate video frames)
    ↓ (Export to MP4)
    ↓ (Return JSON response with output path)
C# Application
    ↓ (Load video into MediaElement)
```

## VRAM Constraints (RTX 3060 - 12GB)

**Realistic Limits:**
- **512x512**: Up to 250 frames (10 sec @ 25fps)
- **576x1024 (16:9)**: Up to 120 frames (5 sec @ 24fps)
- **768x768**: Up to 80 frames (3.3 sec @ 24fps)
- **1024x576 (16:9)**: Up to 60 frames (2.5 sec @ 24fps)

**Optimization Strategy:**
- Use `decode_chunk_size=2` for longer videos or higher resolutions
- Enable `model_cpu_offload()` to reduce VRAM usage
- Use FP16 precision (already enabled by default)
- Close other GPU applications during generation

## Project Structure

```
/
├── backend/                    # Python inference engine
│   ├── generate.py            # Main generation script
│   ├── download_models.py     # Model download utility
│   └── venv/                  # Python virtual environment
├── models/                     # Local AI models (not in git)
│   ├── svd-xt/               # Stable Video Diffusion model
│   └── custom/               # Optional custom models
├── VideoGenerator/            # C# WPF application
│   ├── MainWindow.xaml       # UI definition
│   ├── MainWindow.xaml.cs    # UI logic
│   └── VideoGenerator.csproj # Project file
├── output/                    # Generated videos
├── plans/                     # Technical specifications
│   └── tech_spec.md          # Detailed architecture doc
└── setup_environment.bat      # Automated setup script
```

## Key Implementation Notes

### CUDA and GPU Requirements
- CUDA 11.8 is required (not 12.x) for compatibility with PyTorch and xformers
- Ensure NVIDIA drivers are up-to-date (525.x or newer)
- Test GPU availability: `python -c "import torch; print(torch.cuda.is_available())"`

### Model Loading (Local Only)
Always use `local_files_only=True` when loading models to ensure no internet dependency:

```python
self.pipe = StableVideoDiffusionPipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    variant="fp16",
    local_files_only=True  # Critical for offline operation
)
```

### Memory Management
The application uses several techniques to fit within 12GB VRAM:
1. **CPU Offloading**: Moves unused model components to RAM
2. **VAE Slicing**: Processes VAE in smaller slices
3. **VAE Tiling**: Divides images into tiles for processing
4. **Xformers**: Memory-efficient attention mechanism
5. **Chunked Decoding**: Decodes video frames in batches

### Custom Model Support
To use custom Stable Diffusion models (.safetensors from CivitAI):

```python
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_single_file(
    "./models/custom_model.safetensors",
    torch_dtype=torch.float16,
    load_safety_checker=False  # No filtering for local use
)
```

## Performance Tuning

**For Speed (Faster Generation):**
- Resolution: 512x512
- Inference steps: 15-20
- FPS: 8
- Duration: 2-3 seconds

**For Quality (Better Results):**
- Resolution: 1024x576 or higher
- Inference steps: 40-50
- FPS: 24
- Adjust `motion_bucket_id` for desired motion intensity

## Common Issues and Solutions

### Out of Memory Errors
- Reduce `decode_chunk_size` to 2
- Reduce `num_frames`
- Lower resolution
- Ensure no other GPU applications are running

### Slow First Generation
- First run loads model into VRAM (30-60 seconds)
- Subsequent generations are much faster
- This is expected behavior

### Video Quality Issues
- Use higher `num_inference_steps` (30-50)
- Experiment with `motion_bucket_id` values
- Ensure source images are high quality
- Try different `noise_aug_strength` values (0.01-0.05)

## File Naming Conventions
- Python backend: snake_case (e.g., `generate_video`, `motion_bucket_id`)
- C# frontend: PascalCase (e.g., `GenerateVideo`, `MotionBucketId`)
- JSON parameters: snake_case (Python convention for interop)

## Important Implementation Notes

### Text Prompts Are REQUIRED
- **All generations require a text prompt** - this is not optional
- UI must validate that prompt field is not empty before starting generation
- Prompts guide the animation (camera movement, subject actions, scene changes, style)
- Both SVD and AnimateDiff pipelines accept prompts (AnimateDiff has stronger conditioning)

### No Content Filtering (Intentional)
**This is a personal, offline application for private use with no built-in content restrictions:**

**SVD Pipeline:**
```python
self.pipe.safety_checker = None  # Explicitly disable
```

**AnimateDiff Pipeline:**
```python
# When loading from .safetensors
AnimateDiffPipeline.from_single_file(
    model_path,
    load_safety_checker=False  # CRITICAL
)

# When loading from repo
AnimateDiffPipeline.from_pretrained(
    model_path,
    safety_checker=None  # CRITICAL
)
```

**Why disabled:**
- User autonomy and creative freedom
- Private, local use only (no public distribution)
- User takes full responsibility for generated content
- Allows unrestricted model choice from CivitAI

### Model Compatibility (AnimateDiff)
- **ONLY SD 1.5 models** work with AnimateDiff
- **NOT compatible**: SDXL, SD 2.x, Pony Diffusion
- Check model's "Base Model" tag on CivitAI before downloading
- Application should validate model compatibility before loading

### Path Handling Rules
**Critical for WSL/Windows hybrid development:**

1. **Never mix path formats** in same file
2. **Python code**: Always use `/mnt/d/` for Windows drives
3. **C# code**: Always use `D:\` for Windows drives
4. **Use conversion utilities** when passing paths between environments
5. **Test paths** in both directions before committing

### Privacy & Legal
- **Age restriction**: 18+ only for NSFW features
- **User responsibility**: All generated content is user's responsibility
- **No distribution**: Generated content for private use only
- **Compliance**: Users must follow local laws and regulations
- **No telemetry**: Application does not collect any data or phone home

## Phase 6: Testing & Verification

### Environment Verification
Always verify setup before making changes:

```bash
# Run comprehensive environment check
python backend/verify_setup.py

# Should verify:
# - Python 3.10
# - CUDA availability (~11.9GB VRAM)
# - All dependencies installed
# - Models downloaded correctly
# - Directory structure exists
# - Sufficient disk space
```

### Integration Testing
Test full workflow after any significant changes:

```bash
# Quick integration test (5 minutes)
bash scripts/test_integration.sh

# Full integration test (15 minutes)
bash scripts/test_integration.sh --full

# Tests include:
# - Environment verification
# - Model discovery
# - VRAM stats
# - Path conversion
# - Prompt validation
# - Video generation (both pipelines)
# - C# build
```

### Manual Testing Checklist
Before any release or major update:

1. **Backend Tests**:
   - [ ] `python backend/generate.py --list-models` works
   - [ ] `python backend/generate.py --vram-stats` works
   - [ ] `python backend/test_generation.py --quick` generates video successfully
   - [ ] Both SVD and AnimateDiff pipelines work
   - [ ] VRAM stays within 11GB limit

2. **Frontend Tests**:
   - [ ] Application launches without errors
   - [ ] "Refresh Models" populates dropdown
   - [ ] Image selection and preview works
   - [ ] All parameter controls update correctly
   - [ ] SVD generation completes successfully
   - [ ] AnimateDiff generation completes successfully
   - [ ] Video preview plays correctly
   - [ ] Progress bar updates during generation
   - [ ] Cancel button stops generation
   - [ ] VRAM stats display works

3. **CivitAI Integration Tests**:
   - [ ] Model browser opens
   - [ ] 6 models display correctly
   - [ ] Category filtering works
   - [ ] Model details show (pros/cons/settings)
   - [ ] Download button appears/works (test with small model or mock)
   - [ ] Downloaded models appear after restart

4. **Path Conversion Tests**:
   - [ ] Windows path → WSL conversion works
   - [ ] WSL path → Windows conversion works
   - [ ] Generated video loads in preview (validates round-trip)

5. **Error Handling Tests**:
   - [ ] Empty prompt shows error
   - [ ] Missing image shows error
   - [ ] Backend unavailable shows helpful message
   - [ ] Out of VRAM shows helpful message with suggestions
   - [ ] Model not found shows error

### Common Test Scenarios

**Scenario 1: New Environment Setup**
```bash
# Simulate fresh install
1. Run setup_wsl.sh
2. Download models
3. Run verify_setup.py
4. Generate test video
5. Build C# application
6. Test end-to-end generation
```

**Scenario 2: Custom Model Integration**
```bash
1. Download model via CivitAI browser
2. Restart application
3. Verify model appears in dropdown
4. Select model and generate video
5. Verify prompt adherence
6. Check VRAM usage
```

**Scenario 3: VRAM Stress Test**
```bash
# Test with high parameters
1. Set resolution to 1024x576
2. Set frames to 60
3. Use SVD pipeline
4. Observe VRAM optimization messages
5. Verify parameters are auto-adjusted
6. Verify generation completes without OOM
```

### Performance Benchmarks
Target performance metrics for RTX 3060 (12GB):

| Pipeline | Resolution | Frames | Expected Time | Max VRAM |
|----------|------------|--------|---------------|----------|
| SVD | 512x512 | 25 | 30-60s | 8GB |
| SVD | 1024x576 | 25 | 60-90s | 10GB |
| AnimateDiff | 512x512 | 24 | 45-90s | 9GB |

If performance deviates significantly, investigate:
- GPU utilization (`nvidia-smi` during generation)
- Xformers enabled
- No background GPU processes
- Model fully loaded (first generation is slow)

### Known Limitations & Workarounds

1. **First Generation Slow**:
   - Expected (model loading takes 30-60s)
   - Subsequent generations much faster
   - Not a bug

2. **Model Discovery Requires Restart**:
   - Downloaded models only detected on app launch
   - User must restart after downloading from CivitAI browser
   - Documented in UI

3. **Custom Model Compatibility**:
   - Only SD 1.5 models work with AnimateDiff
   - SDXL/SD 2.x will fail
   - Should be validated before download (future enhancement)

4. **WSL Path Requirements**:
   - Models MUST be on D:\ (or adjustable via config)
   - C:\ works but may have permission issues
   - Document this requirement clearly

### User Documentation
Always ensure these are up to date:

- **QUICKSTART.md**: Step-by-step setup guide for new users
- **TROUBLESHOOTING.md**: Common issues and solutions
- **README.md**: Project overview and feature list
- **plans/TEST_PLAN.md**: Comprehensive test cases

### Before Merging/Releasing
Run this complete verification:

```bash
# 1. Environment check
python backend/verify_setup.py

# 2. Integration tests
bash scripts/test_integration.sh --full

# 3. Manual UI testing (all items in checklist above)

# 4. Documentation review
# - README.md accurate?
# - QUICKSTART.md tested?
# - TROUBLESHOOTING.md comprehensive?
# - CLAUDE.md up to date?

# 5. Build verification
cd VideoGenerator
dotnet build --configuration Release
# Test executable works

# 6. Final smoke test
# - Fresh clone of repository
# - Follow QUICKSTART.md exactly
# - Verify everything works for new user
```

### Debugging Tips

**Issue: Generation fails silently**
```bash
# Run Python directly to see errors
source backend/venv/bin/activate
python backend/test_generation.py --quick
# Look for stack traces
```

**Issue: C# can't communicate with Python**
```bash
# Test backend availability
python backend/generate.py --list-models

# Check Python path in C# code
# Edit PythonBackendService.cs if needed
```

**Issue: Path conversion problems**
```python
# Test conversion
from utils.path_utils import windows_to_wsl_path, wsl_to_windows_path

test_path = "D:\\VideoGenerator\\models"
print(f"Original: {test_path}")
print(f"To WSL: {windows_to_wsl_path(test_path)}")
print(f"Back to Windows: {wsl_to_windows_path(windows_to_wsl_path(test_path))}")
```

**Issue: VRAM optimization not working**
```python
# Test optimizer directly
from utils.vram_utils import VRAMOptimizer

optimizer = VRAMOptimizer()
params = {"pipeline": "svd", "width": 1024, "height": 576, "numFrames": 100}
optimized, message = optimizer.optimize_params(params)
print(f"Optimized: {optimized}")
print(f"Message: {message}")
```

### Version Control Best Practices
- Never commit models (too large, use .gitignore)
- Never commit output videos
- Never commit .env files or credentials
- Keep CLAUDE.md, README.md, and documentation in sync
- Test before pushing to main branch
