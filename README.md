# Image-to-Video Generator

An offline AI-powered desktop application that transforms static images into animated videos using text prompts. Features dual model support (SVD-XT + AnimateDiff) with unrestricted local generation for private use.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)
![Python](https://img.shields.io/badge/python-3.10-green.svg)
![.NET](https://img.shields.io/badge/.NET-6.0-purple.svg)

---

## ✨ Features

- **🎬 Dual AI Models**: Choose between SVD-XT (fast) or AnimateDiff (high control)
- **✍️ Text Prompt Control**: Guide animations with detailed text descriptions
- **🎨 Custom Models**: Load .safetensors models from CivitAI
- **🔒 100% Offline**: All processing happens locally on your device
- **🚫 No Content Filters**: Unrestricted generation for private use
- **⚡ GPU Accelerated**: Optimized for RTX 3060 12GB VRAM
- **🖥️ Desktop UI**: User-friendly WPF application for Windows

---

## 🎯 Quick Start

### Prerequisites

- **Windows 10/11** (64-bit)
- **NVIDIA GPU** with 12GB+ VRAM (RTX 3060 or better)
- **NVIDIA Drivers** (525.x or newer)
- **15GB+ free disk space** (for AI models)

### Installation

**Option A: Installer** (Recommended)
```
1. Download VideoGenerator-Setup-v1.0.0.exe from Releases
2. Run installer
3. Launch application
4. Follow first-run setup wizard to download models
```

**Option B: Portable**
```
1. Download VideoGenerator-Portable-v1.0.0.zip
2. Extract to desired location
3. Run VideoGenerator.exe
4. Download models on first launch
```

### First Run

1. **Launch Application**: Double-click VideoGenerator.exe
2. **Download Models** (~15GB): Application will download required AI models
   - SVD-XT (~10GB)
   - AnimateDiff Motion Adapter (~3GB)
   - Realistic Vision v5.1 (~2GB)
3. **Wait 10-20 minutes**: Depends on internet speed
4. **Start Creating**: Load an image, write a prompt, generate!

---

## 🚀 Usage

### Basic Workflow

1. **Load Image**: Drag-drop or browse for an image
2. **Select Model**: Choose SVD-XT or AnimateDiff
3. **Write Prompt** (Required): Describe the desired animation
   ```
   Examples:
   - "slow cinematic zoom in, dramatic lighting"
   - "person turning head, wind blowing hair, golden hour"
   - "camera panning left to right, smooth motion"
   ```
4. **Adjust Settings**: Duration, FPS, motion intensity, quality
5. **Generate**: Click "Generate Video" and wait 2-10 minutes
6. **Preview & Save**: Play video, export when satisfied

### Prompt Examples

**Camera Movements**:
- "slow zoom in, cinematic"
- "pan from left to right, smooth"
- "dolly shot forward, dramatic"
- "rotate clockwise, steady motion"

**Subject Actions**:
- "person walking forward, natural gait"
- "hair blowing in wind, gentle movement"
- "eyes blinking, slight head turn"
- "hands moving expressively"

**Scene Changes**:
- "day to night transition, warm to cool tones"
- "clouds moving across sky, time lapse"
- "seasons changing, leaves falling"
- "water rippling, gentle waves"

**Artistic Style**:
- "cinematic, film grain, dramatic lighting"
- "dreamy, soft focus, ethereal atmosphere"
- "hyper realistic, 8k, ultra detailed"
- "slow motion, high frame rate"

---

## 📊 Performance

### Generation Times (RTX 3060 12GB)

| Model | Resolution | Frames | Steps | Time | VRAM |
|-------|-----------|--------|-------|------|------|
| SVD-XT | 512x512 | 25 | 25 | ~2-3 min | ~8GB |
| SVD-XT | 1024x576 | 50 | 40 | ~5-6 min | ~11GB |
| AnimateDiff | 512x512 | 48 | 30 | ~4-5 min | ~10GB |
| AnimateDiff | 768x768 | 32 | 25 | ~6-7 min | ~11GB |

### Recommended Settings

**For Speed**:
- Resolution: 512x512
- Frames: 25
- Steps: 15-20
- FPS: 8
- Model: SVD-XT

**For Quality**:
- Resolution: 768x768 or 1024x576
- Frames: 48
- Steps: 30-50
- FPS: 16-24
- Model: AnimateDiff

---

## 🎨 Custom Models

### Adding CivitAI Models

1. Visit [CivitAI](https://civitai.com)
2. Filter by **"SD 1.5"** base model
3. Download `.safetensors` file
4. Move to `D:\VideoGenerator\models\custom\`
5. Restart application
6. Select from model dropdown

### Recommended Models

| Model | Style | NSFW | Best For |
|-------|-------|------|----------|
| Realistic Vision v5.1 | Photorealistic | ✅ | Realistic humans |
| DreamShaper 8 | Artistic | ✅ | Cinematic style |
| ChilloutMix | Portraits | ✅ | Soft aesthetic |
| Anything V5 | Anime | ✅ | Anime characters |

See [`plans/MODELS.md`](plans/MODELS.md) for complete guide.

---

## ⚙️ Configuration

### Model Storage

Default: `D:\VideoGenerator\models\`

To change location, edit `D:\VideoGenerator\config.json`:
```json
{
  "modelPath": "E:\\MyModels\\",
  "outputPath": "D:\\Videos\\Generated\\"
}
```

### Advanced Settings

```json
{
  "advanced": {
    "enableXformers": true,
    "enableCPUOffload": true,
    "maxVRAMUsage": 11.0,
    "decodeChunkSize": 4
  }
}
```

---

## 🛠️ Development

### Building from Source

**Prerequisites**:
- WSL 2 (Ubuntu 22.04)
- Python 3.10
- .NET 6.0 SDK
- CUDA 11.8

**Setup**:
```bash
# Clone repository
git clone https://github.com/TawfiqulBari/image-video-3.git
cd image-video-3

# Run setup script
bash scripts/setup_wsl.sh

# Download models
source backend/venv/bin/activate
python backend/download_models.py

# Build C# application
cd frontend
dotnet build VideoGenerator.sln
```

See [`plans/wsl-windows-guide.md`](plans/wsl-windows-guide.md) for detailed development guide.

---

## 📝 Documentation

- **[Development Plan](plans/PLAN.md)** - Complete development roadmap
- **[Technical Specification](plans/SPEC.md)** - System architecture and API
- **[Model Guide](plans/MODELS.md)** - CivitAI models and prompt tips
- **[WSL Development](plans/wsl-windows-guide.md)** - Cross-platform development
- **[User Guide](docs/USER_GUIDE.md)** - Complete usage documentation *(coming soon)*

---

## 🔒 Privacy & Legal

### Privacy Guarantee

**100% Local Processing**:
- ✅ All AI generation happens on your device
- ✅ No internet connection required after setup
- ✅ No telemetry, analytics, or tracking
- ✅ Your images and prompts never leave your computer
- ✅ Generated content stays private

**What We Don't Collect**:
- ❌ No user data
- ❌ No usage statistics
- ❌ No generated content
- ❌ No prompts or images
- ❌ No personal information

### Legal Disclaimer

**Age Restriction**:
This application is intended for **adults only (18+)**. By using this software, you confirm that you are of legal age in your jurisdiction.

**User Responsibility**:
- You are solely responsible for all content you generate
- You must comply with all applicable local, state, and federal laws
- Generated content is for **private, personal use only**
- Do not generate content depicting real people without consent
- Do not use for harassment, defamation, or illegal purposes

**No Warranty**:
This software is provided "AS IS" without warranty of any kind. The developers:
- Do NOT host or distribute AI models
- Are NOT responsible for generated content
- Are NOT affiliated with model creators or CivitAI
- Do NOT endorse any specific models or use cases
- Provide NO guarantees of model behavior or output

**Model Licenses**:
Users must comply with licenses of downloaded models. Most models allow personal use but may restrict commercial use. Check each model's license on CivitAI before use.

**Content Responsibility**:
- The application intentionally disables safety checkers for user autonomy
- Users have full control and full responsibility for generated content
- Generated content should not be shared publicly without careful consideration
- Respect intellectual property and privacy rights of others

---

## ⚠️ Important Notes

### NSFW Content

This application is designed for unrestricted private use:
- Safety checkers are **intentionally disabled**
- No content filtering or moderation
- Full user control over generation
- **For personal use only** - do not distribute generated content

### System Requirements

**Minimum**:
- GPU: NVIDIA RTX 3060 (12GB VRAM)
- RAM: 16GB
- Storage: 50GB free (including models and outputs)
- OS: Windows 10/11 64-bit

**Recommended**:
- GPU: NVIDIA RTX 3080 or better (16GB+ VRAM)
- RAM: 32GB
- Storage: 100GB+ free SSD
- OS: Windows 11 64-bit

### Known Limitations

- **Windows Only**: WPF requires Windows (no macOS/Linux support)
- **NVIDIA GPU Required**: CUDA-only (no AMD/Intel GPU support)
- **12GB VRAM Minimum**: Lower VRAM will fail or produce errors
- **Generation Time**: 2-10 minutes per video depending on settings
- **Model Compatibility**: Only SD 1.5 models work with AnimateDiff

---

## 🐛 Troubleshooting

### GPU Not Detected

```
Error: CUDA not available
```

**Solution**:
1. Update NVIDIA drivers to 525.x or newer
2. Restart computer
3. Run: `python backend/check_gpu.py`

### Out of Memory Error

```
Error: CUDA out of memory
```

**Solution**:
1. Reduce resolution (512x512 instead of 768x768)
2. Reduce frames (25 instead of 50)
3. Lower decode_chunk_size in settings
4. Close other GPU applications

### Model Download Failed

```
Error: Failed to download model
```

**Solution**:
1. Check internet connection
2. Retry download (resumes automatically)
3. Download manually from links in `plans/MODELS.md`
4. Place in `D:\VideoGenerator\models\`

### Video Quality Poor

**Solutions**:
- Increase inference steps (30-50)
- Use higher resolution
- Try different model (AnimateDiff vs SVD)
- Improve prompt (add quality tags like "masterpiece", "highly detailed")
- Use negative prompts ("blurry", "low quality", "distorted")

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines (coming soon).

### Development Setup

See [`plans/wsl-windows-guide.md`](plans/wsl-windows-guide.md) for complete development environment setup.

### Reporting Issues

Please report bugs via [GitHub Issues](https://github.com/TawfiqulBari/image-video-3/issues) with:
- System specs (GPU, RAM, OS)
- Steps to reproduce
- Error messages
- Screenshots if applicable

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **PyTorch**: BSD-style license
- **Diffusers**: Apache 2.0
- **.NET**: MIT License
- **AI Models**: Various (check individual model licenses)

---

## 🌟 Acknowledgments

- **Stability AI** - Stable Video Diffusion model
- **Guoyw** - AnimateDiff motion adapter
- **CivitAI Community** - Custom model ecosystem
- **HuggingFace** - Model hosting and diffusers library

---

## 📧 Support

- **Documentation**: See `docs/` and `plans/` folders
- **Issues**: [GitHub Issues](https://github.com/TawfiqulBari/image-video-3/issues)
- **Discussions**: [GitHub Discussions](https://github.com/TawfiqulBari/image-video-3/discussions)

---

## ⚖️ Final Reminder

**This software is for personal, private use only.**

By using this application, you agree to:
- Use responsibly and legally
- Not distribute generated content publicly without consideration
- Respect privacy and intellectual property rights
- Comply with all applicable laws
- Take full responsibility for generated content

**Use at your own risk. The developers assume no liability for misuse.**

---

*Made with ❤️ for creative freedom and privacy*
