# Development Plan: Image-to-Video Generator with Text Prompts

## Project Overview
An offline image-to-video generator that converts static images into animated videos using AI models (Stable Video Diffusion & AnimateDiff). Features required text prompts for precise control over camera movements, subject actions, scene changes, and artistic style.

**Key Features**:
- **Dual Model Support**: SVD-XT + AnimateDiff with custom SD models
- **Required Text Prompts**: Control camera, actions, scenes, and style
- **NSFW-Capable**: Unrestricted local generation for private use
- **Custom Models**: Load .safetensors files from CivitAI
- **Offline Operation**: No internet required after initial setup

**Development**: WSL (Ubuntu) | **Deployment**: Windows Desktop | **Target GPU**: RTX 3060 (12GB VRAM)

---

## Phase 1: Project Foundation ✅
**Duration**: 30-45 minutes | **Status**: In Progress

### Objectives
- Set up project structure following dup-checker methodology
- Create comprehensive documentation
- Initialize development environment

### Tasks
- [x] Create directory structure (`/plans`, `/backend`, `/frontend`, `/scripts`)
- [ ] Write `.gitignore` (exclude models, .safetensors, output/)
- [ ] Create `README.md` with quick start + privacy notice
- [ ] Update `CLAUDE.md` with WSL workflow + dual-pipeline architecture
- [ ] Create `plans/SPEC.md` - Technical architecture for both pipelines
- [ ] Create `plans/MODELS.md` - CivitAI model guide + recommendations
- [ ] Create `plans/wsl-windows-guide.md` - Cross-platform development

### Deliverables
- ✅ Clean project structure
- ✅ Comprehensive planning documentation
- ⏳ Development guidelines and model recommendations

---

## Phase 2: WSL Environment + Multi-Model Setup
**Duration**: 2-3 hours | **Status**: Pending

### Objectives
- Set up Python environment with CUDA support
- Configure D:\ drive model storage
- Download multiple AI models (SVD + AnimateDiff + Realistic SD base)

### Tasks
**Environment**:
- [ ] Create `scripts/check_gpu.py` - CUDA verification utility
- [ ] Create `backend/requirements.txt` with all dependencies
- [ ] Create `scripts/setup_wsl.sh` - Automated environment setup
- [ ] Verify NVIDIA drivers: `nvidia-smi` in WSL
- [ ] Install CUDA 11.8 if needed (conditional)
- [ ] Create Python 3.10 virtual environment
- [ ] Install PyTorch with CUDA 11.8 support
- [ ] Install diffusers, transformers, accelerate, xformers

**Model Storage Configuration**:
- [ ] Configure `/mnt/d/VideoGenerator/models` directory structure:
  ```
  D:\VideoGenerator\models\
  ├── svd-xt\              (~10GB - Stability AI)
  ├── animatediff\         (~3GB - motion module)
  ├── realistic-vision\    (~2GB - NSFW-capable SD base)
  └── custom\              (user's additional .safetensors)
  ```
- [ ] Create `backend/download_models.py` with resume support:
  - Download SVD-XT from HuggingFace (stabilityai/stable-video-diffusion-img2vid-xt)
  - Download AnimateDiff motion module (guoyww/animatediff-motion-adapter-v1-5-2)
  - Download Realistic Vision v5.1 from CivitAI (model ID: 130072)
  - Implement checksum verification
  - Add progress bars for large downloads

### Success Criteria
- ✅ `nvidia-smi` shows GPU in WSL
- ✅ `python -c "import torch; print(torch.cuda.is_available())"` returns `True`
- ✅ All 3 models downloaded to D:\ and accessible from `/mnt/d/`
- ✅ `scripts/setup_wsl.sh` can reproduce environment on fresh WSL install

---

## Phase 3: Python Backend - Dual Pipeline Implementation
**Duration**: 4-5 hours | **Status**: Pending

### Objectives
- Implement SVD and AnimateDiff pipelines
- Add text prompt support for both pipelines
- Create model management system
- Build path conversion utilities for WSL/Windows

### Directory Structure
```
backend/
├── generate.py                    # Main CLI entry point
├── pipelines/
│   ├── __init__.py
│   ├── base_pipeline.py          # Abstract base class
│   ├── svd_pipeline.py           # SVD wrapper (no safety checker)
│   └── animatediff_pipeline.py   # AnimateDiff + custom SD models
├── services/
│   ├── __init__.py
│   ├── video_service.py          # High-level generation API
│   └── model_manager.py          # Model loading/switching
├── utils/
│   ├── __init__.py
│   ├── path_utils.py             # Windows ↔ WSL path conversion
│   ├── vram_utils.py             # VRAM monitoring/optimization
│   ├── prompt_utils.py           # Prompt enhancement/validation
│   └── config.py                 # Configuration management
├── download_models.py             # Model downloader
├── check_gpu.py                   # CUDA verification
├── test_generation.py             # Test both pipelines
└── requirements.txt
```

### Key Implementation Tasks

**1. Base Pipeline** (`pipelines/base_pipeline.py`):
- [ ] Abstract base class defining pipeline interface
- [ ] Common initialization logic
- [ ] VRAM optimization methods (CPU offload, VAE slicing, xformers)
- [ ] Progress callback system

**2. SVD Pipeline** (`pipelines/svd_pipeline.py`):
- [ ] Load SVD-XT model with `local_files_only=True`
- [ ] **Disable safety checker** (CRITICAL for NSFW)
- [ ] Implement text prompt as conditioning (limited effect in SVD)
- [ ] Image preprocessing (resize to 1024x576 or 576x1024)
- [ ] Frame generation with progress callbacks
- [ ] Video export with opencv

**3. AnimateDiff Pipeline** (`pipelines/animatediff_pipeline.py`):
- [ ] Load motion adapter module
- [ ] Support HuggingFace repo AND .safetensors file loading
- [ ] **Disable safety checker** (`load_safety_checker=False`, `safety_checker=None`)
- [ ] Strong text prompt conditioning
- [ ] Negative prompt support
- [ ] Image-to-video with img2img initialization
- [ ] Guidance scale control

**4. Model Manager** (`services/model_manager.py`):
- [ ] Scan `/mnt/d/VideoGenerator/models` for available models
- [ ] List SVD models, AnimateDiff bases, and custom .safetensors
- [ ] Load/unload pipelines dynamically
- [ ] Cache loaded models to avoid reloading
- [ ] Validate model compatibility (SD 1.5 for AnimateDiff)

**5. Video Service** (`services/video_service.py`):
- [ ] High-level `generate_video(params)` API
- [ ] Parameter validation (required prompt, valid ranges)
- [ ] Dynamic VRAM optimization
- [ ] Pipeline selection logic
- [ ] Error handling with user-friendly messages

**6. Utilities**:
- [ ] `path_utils.py`: Windows ↔ WSL path conversion functions
- [ ] `vram_utils.py`: VRAM monitoring, estimation, dynamic chunk size
- [ ] `prompt_utils.py`: Prompt validation, enhancement, token counting
- [ ] `config.py`: Load/save user preferences

**7. Main Entry Point** (`generate.py`):
- [ ] Parse JSON input from command line
- [ ] Validate required prompt field
- [ ] Initialize appropriate pipeline
- [ ] Call video generation
- [ ] Return JSON response with output path and metadata

### JSON Protocol

**Request** (C# → Python):
```json
{
  "pipeline": "animatediff",
  "baseModel": "D:\\VideoGenerator\\models\\realistic-vision\\model.safetensors",
  "motionAdapter": "D:\\VideoGenerator\\models\\animatediff\\",
  "imagePath": "D:\\Images\\photo.jpg",
  "prompt": "slow cinematic zoom in, woman turning head, wind blowing hair, golden hour lighting, dreamy atmosphere",
  "negativePrompt": "blurry, distorted, low quality, static, ugly, deformed",
  "numFrames": 48,
  "fps": 16,
  "guidanceScale": 7.5,
  "motionBucketId": 180,
  "numInferenceSteps": 30,
  "decodeChunkSize": 4,
  "seed": 42,
  "outputPath": "D:\\VideoGenerator\\output\\video_001.mp4"
}
```

**Response** (Python → C#):
```json
{
  "status": "success",
  "output": "D:\\VideoGenerator\\output\\video_001.mp4",
  "metadata": {
    "pipeline": "animatediff",
    "model": "realistic-vision-v5.1",
    "prompt": "slow cinematic zoom in...",
    "numFrames": 48,
    "fps": 16,
    "duration": 3.0,
    "resolution": "512x512",
    "generationTime": 145.2,
    "vramUsed": 9.8
  }
}
```

### Success Criteria
- ✅ `python generate.py '{...}'` generates video with both pipelines
- ✅ Text prompts visibly affect output
- ✅ NSFW content generates without filtering
- ✅ Custom .safetensors models load successfully
- ✅ VRAM usage stays under 12GB

---

## Phase 4: C# WPF Frontend with Prompt UI
**Duration**: 4-5 hours | **Status**: Pending

### Objectives
- Create Windows desktop UI with modern design
- Add **required** text prompt input
- Implement model selector (SVD vs AnimateDiff vs Custom)
- Build subprocess communication with Python
- Add video preview and playback controls

### UI Components (MainWindow.xaml)

```
┌────────────────────────────────────────────────────────────┐
│  Image to Video Generator                          [_][□][X]│
├─────────────────┬──────────────────────────────────────────┤
│  IMAGE UPLOAD   │                                          │
│  ┌───────────┐  │                                          │
│  │           │  │         VIDEO PREVIEW AREA               │
│  │  Preview  │  │                                          │
│  │   Image   │  │       (MediaElement for playback)        │
│  │           │  │                                          │
│  └───────────┘  │                                          │
│  [Browse Image] │                                          │
│                 │                                          │
│  MODEL          ├──────────────────────────────────────────┤
│  ◉ SVD-XT       │  ▶  ⏸  ⏹  [Save Video]                 │
│  ○ AnimateDiff  └──────────────────────────────────────────┘
│  ○ Custom...
│
│  [Select Base Model ▼]  (if AnimateDiff)
│
│  PROMPT (REQUIRED)*
│  ┌──────────────┐
│  │ slow zoom in,│
│  │ cinematic... │
│  │              │
│  └──────────────┘
│  [💡 Examples]
│
│  NEGATIVE PROMPT
│  ┌──────────────┐
│  │ blurry, low  │
│  │ quality...   │
│  └──────────────┘
│
│  SETTINGS
│  Duration: [2s ═══○═ 10s]
│  FPS: [8 ▼] [12] [16] [24]
│  Motion: [1 ════○══ 255]
│  Steps: [15 ══○═ 50]
│  Guidance: [1 ═○══ 15]
│  Seed: [______] (-1=random)
│
│  [🎬 Generate Video]
│
│  [▓▓▓▓▓▓░░░] 60%
│  Generating frame 30/50...
└─────────────────┘
```

### Key Implementation Tasks

**1. XAML Layout**:
- [ ] Grid layout: Left sidebar (400px) + Right preview (rest)
- [ ] Image upload area with drag-drop support
- [ ] Model selector (RadioButtons: SVD, AnimateDiff, Custom)
- [ ] Base model ComboBox (visible when AnimateDiff selected)
- [ ] **Required** prompt TextBox (multi-line, 80px height)
- [ ] Optional negative prompt TextBox (60px height)
- [ ] Parameter controls (Sliders, ComboBox, TextBox)
- [ ] Generate button (prominent, 45px height)
- [ ] Progress bar with status text
- [ ] MediaElement for video preview
- [ ] Playback controls (Play, Pause, Stop, Save)

**2. MainWindow.xaml.cs Logic**:
- [ ] Image loading (drag-drop + file browse)
- [ ] **Prompt validation** (reject if empty)
- [ ] Model selection change handler (show/hide base model selector)
- [ ] Parameter validation (ranges, types)
- [ ] Generate button click → validate → call Python
- [ ] Progress updates from Python stderr
- [ ] Load generated video into MediaElement
- [ ] Video playback controls
- [ ] Save As dialog

**3. Supporting Classes**:
```
frontend/VideoGenerator/
├── VideoGenerator.csproj
├── MainWindow.xaml
├── MainWindow.xaml.cs
├── Models/
│   ├── GenerationParams.cs        # Data model
│   └── GenerationResult.cs        # Response model
├── Services/
│   ├── PythonBackend.cs           # Subprocess management
│   └── PathUtils.cs               # Path conversion
├── Views/
│   ├── PromptExamplesDialog.xaml  # Example prompts popup
│   └── ModelBrowserDialog.xaml    # Browse .safetensors files
└── Resources/
    └── Icons/                      # App icons
```

**4. Python Integration** (`PythonBackend.cs`):
- [ ] Subprocess creation with proper paths
- [ ] JSON serialization of parameters
- [ ] Read stdout for final result
- [ ] Read stderr for progress updates
- [ ] Timeout handling (10 minute max)
- [ ] Error parsing and user-friendly messages
- [ ] Cancel operation support

**5. Prompt Examples Dialog**:
- [ ] Create popup window with categorized examples:
  - Camera Movements (zoom, pan, dolly, rotate)
  - Subject Actions (walking, turning, blinking, gestures)
  - Scene Changes (day/night, weather, seasons)
  - Style Effects (cinematic, dreamy, dramatic, slow-mo)
- [ ] "Use This" button to copy example to main prompt field

**6. Model Browser** (for custom .safetensors):
- [ ] File browser filtered to *.safetensors
- [ ] Show model info (file size, modification date)
- [ ] Add to model list
- [ ] Validate SD 1.5 compatibility

### Success Criteria
- ✅ Application launches without errors
- ✅ Prompt field enforces required validation
- ✅ Model selector shows available models
- ✅ Generate button triggers Python subprocess
- ✅ Progress bar updates during generation
- ✅ Generated video plays in preview
- ✅ NSFW content displays without issues

---

## Phase 5: CivitAI Model Integration
**Duration**: 2-3 hours | **Status**: Pending

### Objectives
- Add CivitAI API downloader
- Support custom .safetensors loading
- Create model compatibility checker
- Build model management UI

### Tasks

**1. CivitAI Downloader** (update `download_models.py`):
- [ ] Add function to download by model ID
- [ ] Use CivitAI API: `https://civitai.com/api/download/models/{id}`
- [ ] No API key required for public models
- [ ] Stream download with progress bar
- [ ] Resume support for interrupted downloads
- [ ] Verify file hash after download
- [ ] Extract metadata (model name, version, base model)

**2. Recommended Models**:
- [ ] Realistic Vision v5.1 (ID: 130072) - Photorealistic, NSFW
- [ ] DreamShaper 8 (ID: 128713) - Versatile, good motion
- [ ] ChilloutMix (ID: 59241) - Realistic portraits
- [ ] Add download commands to setup script

**3. Model Compatibility Checker**:
- [ ] Verify .safetensors format (not .ckpt)
- [ ] Check SD version (must be 1.5, not SDXL or 2.x)
- [ ] Read safetensors metadata for base model info
- [ ] Warn if incompatible with AnimateDiff
- [ ] Create `utils/model_validator.py`

**4. Model Manager UI** (C#):
- [ ] Show list of available models
- [ ] "Add Model" button → browse or download by URL
- [ ] Model info display (name, size, base version)
- [ ] Delete model from list
- [ ] Set default model

**5. plans/MODELS.md Guide**:
- [ ] How to browse CivitAI for models
- [ ] How to identify SD 1.5 models
- [ ] How to download .safetensors files
- [ ] How to add to application
- [ ] Recommended models for different styles
- [ ] Legal/ethical guidelines for NSFW content
- [ ] Model license information

### Success Criteria
- ✅ Can download models from CivitAI by ID
- ✅ Can load custom .safetensors from file browser
- ✅ Incompatible models show clear error message
- ✅ Model list updates dynamically
- ✅ Downloaded models work with AnimateDiff

---

## Phase 6: Integration & Multi-Pipeline Testing
**Duration**: 2-3 hours | **Status**: Pending

### Objectives
- Test end-to-end workflow with both pipelines
- Validate prompt effectiveness
- Performance benchmarking
- NSFW content testing
- Error scenario validation

### Test Scenarios

**1. SVD Pipeline Tests**:
- [ ] Test with simple prompt: "slow zoom in"
- [ ] Test with complex prompt: "cinematic dolly shot, dramatic lighting"
- [ ] Compare with/without prompt (verify difference)
- [ ] Test NSFW content generation
- [ ] Measure generation time (target: <3min for 25 frames)

**2. AnimateDiff Pipeline Tests**:
- [ ] Test with Realistic Vision base model
- [ ] Camera movement prompts (zoom, pan, rotate)
- [ ] Subject action prompts (walking, turning, gestures)
- [ ] Complex multi-action prompts
- [ ] Negative prompt effectiveness
- [ ] Test NSFW content generation
- [ ] Measure generation time (target: <5min for 48 frames)

**3. Custom Model Loading**:
- [ ] Load .safetensors from CivitAI
- [ ] Test DreamShaper model
- [ ] Test incompatible model (SDXL) → should error gracefully
- [ ] Switch models without restarting application

**4. Prompt Validation**:
- [ ] Empty prompt → rejected with error message
- [ ] Very long prompt (>77 tokens) → warning or truncation
- [ ] Special characters → handled correctly
- [ ] Emoji in prompts → processed correctly

**5. Cross-Platform Path Testing**:
- [ ] WSL Python accessing D:\ models successfully
- [ ] Windows C# passing correct paths to Python
- [ ] Path conversion works bidirectionally
- [ ] Spaces in paths handled correctly

**6. Error Scenarios**:
- [ ] Out of VRAM → reduce decode_chunk_size automatically
- [ ] Invalid image format → clear error message
- [ ] Models not found → prompt to download
- [ ] Python not found → show setup instructions
- [ ] Generation timeout (>10min) → cancel with message
- [ ] Disk full → detect and warn before generation

**7. Performance Benchmarks**:
```
Test Configuration: RTX 3060 12GB, Resolution 512x512

SVD Pipeline:
- 25 frames, 25 steps: Target <3 min, VRAM <10GB
- 50 frames, 40 steps: Target <6 min, VRAM <11GB

AnimateDiff Pipeline:
- 16 frames, 20 steps: Target <2 min, VRAM <8GB
- 48 frames, 30 steps: Target <5 min, VRAM <11GB
```

### Success Criteria
- ✅ Both pipelines generate videos successfully
- ✅ Text prompts visibly affect output
- ✅ NSFW content generates without filtering
- ✅ All error scenarios handled gracefully
- ✅ Performance meets or exceeds targets
- ✅ Can complete 10 consecutive generations without crashes

---

## Phase 7: Release Packaging & Distribution
**Duration**: 2-3 hours | **Status**: Pending

### Objectives
- Package application for Windows distribution
- Create installer and portable versions
- Write user documentation
- Set up GitHub repository with releases
- Add privacy disclaimers

### Tasks

**1. Portable Python Runtime**:
- [ ] Download Python 3.10.x embeddable package (Windows x64)
- [ ] Bundle with `backend/` folder in release
- [ ] Test standalone execution without system Python
- [ ] Create `python310._pth` for correct import paths

**2. Windows Installer** (Inno Setup):
- [ ] Create installer script (`installer.iss`)
- [ ] Bundle: WPF exe + Python runtime + dependencies
- [ ] **Exclude models** (too large - download on first run)
- [ ] Create desktop shortcut
- [ ] Create Start Menu entry
- [ ] Register file associations (.mp4 preview)
- [ ] Add uninstaller
- [ ] Include privacy notice in install wizard

**3. Portable Version**:
- [ ] Create `VideoGenerator-Portable-v1.0.0.zip`
- [ ] No installation required - unzip and run
- [ ] Includes: exe, Python runtime, backend scripts
- [ ] First run downloads models to `.\models\`
- [ ] Includes README.txt with instructions

**4. User Documentation** (`docs/USER_GUIDE.md`):
- [ ] System requirements (Windows 10/11, NVIDIA GPU, 12GB VRAM)
- [ ] Installation instructions (installer vs portable)
- [ ] First-run setup (model download ~15GB)
- [ ] Usage guide with screenshots
- [ ] Prompt writing tips
- [ ] Model selection guide
- [ ] Troubleshooting section (CUDA errors, out of memory, etc.)
- [ ] **Privacy notice** (all local, no uploads, user responsibility)
- [ ] **Age verification reminder** for NSFW content

**5. Developer Documentation** (`docs/BUILDING.md`):
- [ ] Development environment setup (WSL)
- [ ] Building from source
- [ ] Running tests
- [ ] Adding new models
- [ ] Contributing guidelines

**6. GitHub Repository Setup**:
- [ ] Initialize git repository
- [ ] Create `.github/workflows/release.yml` for automated builds
- [ ] Configure GitHub Actions to build on tag push
- [ ] Set up GitHub Releases page

**7. First Release (v1.0.0)**:
- [ ] Tag release: `git tag v1.0.0`
- [ ] Push to GitHub: `git push origin v1.0.0`
- [ ] Upload artifacts to GitHub Releases:
  - `VideoGenerator-Setup-v1.0.0.exe` (~50MB)
  - `VideoGenerator-Portable-v1.0.0.zip` (~60MB)
  - `USER_GUIDE.pdf`
- [ ] Write release notes:
  - Features list
  - System requirements
  - Known limitations
  - Privacy disclaimer

**8. Privacy & Legal Notices**:
- [ ] Add to installer: "This software processes data locally. No content is uploaded. Users are responsible for generated content and must comply with local laws."
- [ ] Add to README: Age verification statement for NSFW features
- [ ] Add to first-run dialog: Accept terms (local processing, user responsibility)
- [ ] Include MIT License or similar permissive license
- [ ] Disclaimer: "Not responsible for generated content or misuse"

### Deliverables
- ✅ `VideoGenerator-Setup-v1.0.0.exe` (installer)
- ✅ `VideoGenerator-Portable-v1.0.0.zip` (portable)
- ✅ Comprehensive user documentation
- ✅ GitHub repository with CI/CD
- ✅ First release published with privacy disclaimers

---

## Timeline Summary

| Phase | Duration | Dependencies | Key Deliverables |
|-------|----------|--------------|------------------|
| **Phase 1**: Foundation | 30-45 min | None | Project structure, docs |
| **Phase 2**: Environment + Models | 2-3 hours | Phase 1 | CUDA setup, 3 models downloaded |
| **Phase 3**: Python Backend | 4-5 hours | Phase 2 | Dual pipelines, prompt support |
| **Phase 4**: WPF Frontend | 4-5 hours | Phase 1 | UI with required prompts |
| **Phase 5**: CivitAI Integration | 2-3 hours | Phase 3 | Custom model support |
| **Phase 6**: Testing | 2-3 hours | Phase 3, 4, 5 | Validated workflows |
| **Phase 7**: Packaging | 2-3 hours | Phase 6 | Release builds |

**Total Estimated Time**: 15-22 hours (increased due to dual pipelines + custom models)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CUDA not available in WSL | Medium | High | Provide detailed setup guide, fallback to CPU (slow) |
| Out of VRAM | High | Medium | Dynamic decode_chunk_size, VRAM monitoring |
| Model downloads fail (15GB+) | Medium | Medium | Resume support, torrent alternative, manual download guide |
| AnimateDiff incompatible model | Medium | Low | Model validator, clear error messages |
| Prompt too long (>77 tokens) | Low | Low | Token counter, truncation warning |
| Path conversion bugs | Medium | Medium | Comprehensive testing, path debugging tools |
| NSFW content moderation | N/A | N/A | Intentionally disabled for private use |
| Legal liability | Low | High | Clear disclaimers, age verification, terms of service |

---

## Future Enhancements (Post v1.0)

### v1.1 Features:
- [ ] Batch processing (multiple images → videos)
- [ ] Prompt presets library (save favorite prompts)
- [ ] Real-time VRAM monitor in UI
- [ ] Video-to-video generation (extend videos)

### v1.2 Features:
- [ ] LoRA support for style customization
- [ ] ControlNet support for precise control
- [ ] Frame interpolation for smoother output
- [ ] Export to GIF, WebM formats

### v2.0 Features:
- [ ] SDXL support (when AnimateDiff adds support)
- [ ] Multi-GPU support for faster generation
- [ ] Cloud model hosting (optional)
- [ ] Community prompt sharing

---

## Development Best Practices

### Code Quality:
- Follow PEP 8 for Python code
- Follow C# coding conventions
- Add docstrings to all public methods
- Type hints in Python
- XML documentation comments in C#

### Version Control:
- Meaningful commit messages
- Feature branches for new development
- Pull requests for review (if team grows)
- Semantic versioning (MAJOR.MINOR.PATCH)

### Testing:
- Unit tests for path conversion, VRAM estimation
- Integration tests for subprocess communication
- Manual testing checklist before each release
- Performance regression testing

### Security:
- Input validation (file paths, parameters)
- No eval() or exec() on user input
- Sandboxed subprocess execution
- Local processing only (no network after setup)

---

This plan provides a comprehensive roadmap for building a production-ready image-to-video generator with text prompt control and unrestricted local generation capabilities.
