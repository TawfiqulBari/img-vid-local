# Model Guide: CivitAI and Custom Models

## Overview

This application supports multiple AI models for image-to-video generation:
1. **SVD-XT** (Stable Video Diffusion) - Official Stability AI model
2. **AnimateDiff** - Motion module that works with any Stable Diffusion 1.5 base model
3. **Custom Models** - Load .safetensors files from CivitAI and other sources

This guide focuses on finding, downloading, and using custom models from CivitAI for unrestricted generation (including NSFW content).

---

## Included Models

### Default Models (Downloaded on Setup)

**1. SVD-XT**
- **Source**: HuggingFace (stabilityai/stable-video-diffusion-img2vid-xt)
- **Size**: ~10GB
- **Location**: `D:\VideoGenerator\models\svd-xt\`
- **Type**: Image-to-video (limited text conditioning)
- **NSFW**: Capable (no safety checker)
- **Speed**: Fast
- **Best For**: Quick generations, moderate prompt control

**2. AnimateDiff Motion Adapter**
- **Source**: HuggingFace (guoyww/animatediff-motion-adapter-v1-5-2)
- **Size**: ~3GB
- **Location**: `D:\VideoGenerator\models\animatediff\`
- **Type**: Motion module (requires SD 1.5 base)
- **Note**: This is NOT a standalone model - requires a base SD model

**3. Realistic Vision v5.1**
- **Source**: CivitAI (Model ID: 130072)
- **Size**: ~2GB
- **Location**: `D:\VideoGenerator\models\realistic-vision\model.safetensors`
- **Type**: Stable Diffusion 1.5 base model
- **NSFW**: Yes
- **Style**: Photorealistic
- **Best For**: Realistic human figures, portraits, NSFW content

---

## Finding Models on CivitAI

### What is CivitAI?

Civ

itAI is a community platform for sharing custom Stable Diffusion models. Many models are fine-tuned for specific styles, including photorealistic and NSFW content without filters.

**Website**: https://civitai.com

### Model Requirements

For AnimateDiff support, you MUST use:
- ✅ **Stable Diffusion 1.5** base models
- ❌ **NOT** SDXL models
- ❌ **NOT** SD 2.x models

### How to Find Compatible Models

1. Go to https://civitai.com/models
2. Filter by:
   - **Type**: "Checkpoint"
   - **Base Model**: "SD 1.5"
   - **Sort**: "Highest Rated" or "Most Downloaded"
3. Look for tags: "photorealistic", "anime", "artistic", etc.
4. Check "NSFW" toggle to see adult content models

---

## Recommended NSFW-Capable Models

### For Realistic/Photorealistic Content

**1. Realistic Vision v5.1** ⭐ (Included)
- **Model ID**: 130072
- **Style**: Photorealistic, natural skin tones
- **NSFW**: Yes
- **Best For**: Realistic human subjects, portraits
- **Download**: https://civitai.com/models/4201/realistic-vision-v51

**2. DreamShaper 8**
- **Model ID**: 128713
- **Style**: Versatile, slightly stylized
- **NSFW**: Yes
- **Best For**: Artistic + realistic blend, good motion
- **Download**: https://civitai.com/models/4384/dreamshaper

**3. ChilloutMix**
- **Model ID**: 59241
- **Style**: Asian features, soft lighting
- **NSFW**: Yes
- **Best For**: Portraits, soft aesthetic
- **Download**: https://civitai.com/models/6424/chilloutmix

**4. AbsoluteReality v1.8.1**
- **Model ID**: 81458
- **Style**: Ultra-realistic, high detail
- **NSFW**: Yes
- **Best For**: Hyper-realistic subjects
- **Download**: https://civitai.com/models/81458/absolutereality

**5. epiCRealism**
- **Model ID**: 143906
- **Style**: Cinematic realism
- **NSFW**: Yes
- **Best For**: Cinematic shots, dramatic lighting
- **Download**: https://civitai.com/models/25694/epicrealism

### For Anime/Illustrated Content

**6. Anything V5**
- **Model ID**: 30163
- **Style**: Anime/manga style
- **NSFW**: Yes
- **Best For**: Anime characters, illustrated style
- **Download**: https://civitai.com/models/9409/anything-v5

**7. ReV Animated**
- **Model ID**: 7371
- **Style**: Animated/cartoon
- **NSFW**: Yes
- **Best For**: Animation-style videos
- **Download**: https://civitai.com/models/7371/rev-animated

### For Artistic/Stylized Content

**8. Deliberate v2**
- **Model ID**: 159163
- **Style**: Artistic, painterly
- **NSFW**: Yes
- **Best For**: Artistic interpretations
- **Download**: https://civitai.com/models/4823/deliberate

---

## Downloading Models from CivitAI

### Method 1: Automatic Download (Via Application)

*Coming in v1.1 - in-app model browser*

### Method 2: Manual Download (Current Method)

**Step 1**: Find your desired model on CivitAI
**Step 2**: Click the model page
**Step 3**: Select the version (usually latest)
**Step 4**: Click **Download** button (large blue button)
**Step 5**: Choose the `.safetensors` file (NOT `.ckpt` or `.pt`)
**Step 6**: Wait for download (2-7GB typically)

**Step 7**: Move the file to:
```
D:\VideoGenerator\models\custom\
```

**Step 8**: Rename for easy identification (optional):
```
realistic-vision-v5.1.safetensors
dreamshaper-8.safetensors
```

### Method 3: Command Line Download (Python Script)

Use the included download script:

```bash
# In WSL
cd /mnt/d/VideoGenerator
source backend/venv/bin/activate
python backend/download_models.py --civitai-id 130072 --output models/custom/
```

---

## Using Custom Models

### In the Application

1. Launch VideoGenerator
2. Select **"AnimateDiff"** pipeline
3. Click **"Select Base Model"** dropdown
4. Choose your custom model from the list
5. Enter your prompt
6. Click **"Generate Video"**

### Model Loading Order

First generation with a new model will take 30-60 seconds to load.
Subsequent generations with the same model are much faster (model stays in memory).

---

## Model Compatibility

### ✅ Compatible (SD 1.5 Base)

- Realistic Vision v5.1
- DreamShaper 8
- ChilloutMix
- AbsoluteReality
- Anything V5
- Deliberate v2
- Most models tagged "SD 1.5"

### ❌ Not Compatible

- **SDXL models** (different architecture)
  - Example: Juggernaut XL, RealVisXL
- **SD 2.x models** (different architecture)
  - Example: Stable Diffusion 2.1
- **Pony Diffusion** (SDXL-based)
- **LoRA files** (not standalone models)

### How to Check Compatibility

On the CivitAI model page, look for:
- **Base Model**: Must say "SD 1.5" or "SD 1.4"
- **File Type**: Must be `.safetensors` (preferred) or `.ckpt`
- **Size**: Usually 2-7GB for SD 1.5 models

---

## Model Performance

### VRAM Usage by Model Type

| Base Model | Resolution | Max Frames | VRAM Usage |
|------------|-----------|-----------|------------|
| SD 1.5 (any) | 512x512 | 64 | ~8GB |
| SD 1.5 | 768x768 | 32 | ~11GB |
| SD 1.5 | 512x768 | 48 | ~10GB |

All models based on SD 1.5 use similar VRAM.
Performance difference is mainly in generation quality, not speed.

---

## Prompt Tips by Model

### Realistic Vision v5.1
```
Good prompts:
- "RAW photo, 8k uhd, dslr, soft lighting, high quality, film grain"
- "professional photography, natural lighting, detailed skin texture"
- "cinematic shot, shallow depth of field, bokeh background"

Negative prompts:
- "cartoon, painting, illustration, (worst quality, low quality, normal quality:2)"
- "deformed, ugly, blurry, bad anatomy"
```

### DreamShaper 8
```
Good prompts:
- "masterpiece, best quality, highly detailed"
- "cinematic lighting, dramatic shadows"
- "ethereal atmosphere, dreamy"

Negative prompts:
- "low quality, blurry, distorted"
- "ugly, deformed, duplicate"
```

### Anime Models (Anything V5)
```
Good prompts:
- "anime style, highly detailed, vibrant colors"
- "manga art, clean lines, cel shading"
- "beautiful anime character, expressive eyes"

Negative prompts:
- "realistic, photo, 3d render"
- "low quality, bad anatomy"
```

---

## Advanced: Model Mixing (Future Feature)

*Coming in v1.2*

Ability to blend multiple models for unique styles:
- 70% Realistic Vision + 30% DreamShaper = Slightly stylized realism
- 50% Anything V5 + 50% Realistic = Semi-realistic anime

---

## Legal & Ethical Guidelines

### Age Verification

This application is for **adults only** (18+).
If generating NSFW content, you must:
- Be of legal age in your jurisdiction
- Use only for personal, private purposes
- Not share or distribute generated content publicly

### Model Licenses

Check each model's license on CivitAI:
- **CreativeML Open RAIL-M**: Free for personal/commercial use
- **CreativeML Open RAIL++-M**: Free with restrictions
- **Custom Licenses**: Read carefully before use

Most models allow:
- ✅ Personal use
- ✅ Private viewing
- ❌ Commercial use without permission
- ❌ Claiming as original work

### Responsible Use

- Do not generate content depicting real people without consent
- Do not generate illegal content
- Do not use for harassment or harmful purposes
- Follow your local laws and regulations

### Privacy

All generation happens locally on your device:
- No uploads to cloud services
- No telemetry or tracking
- Your prompts and outputs stay private
- No external API calls after model download

---

## Troubleshooting

### "Model failed to load"

**Cause**: Incompatible model (SDXL or SD 2.x)
**Solution**: Download an SD 1.5 model instead

### "Out of memory" error

**Cause**: Model + video generation exceeds 12GB VRAM
**Solution**:
- Reduce resolution (512x512 instead of 768x768)
- Reduce num_frames (24 instead of 48)
- Close other GPU applications

### Model generates poor quality

**Cause**: Incompatible or corrupted download
**Solution**:
- Verify file size matches CivitAI listing
- Re-download the model
- Try a different version

### Prompt not working as expected

**Cause**: Different models respond differently to prompts
**Solution**:
- Check model's example prompts on CivitAI
- Add quality tags ("masterpiece", "best quality")
- Use negative prompts to exclude unwanted elements

---

## Model Organization Tips

### Recommended Folder Structure

```
D:\VideoGenerator\models\
├── svd-xt\                          # SVD model
├── animatediff\                     # Motion module
├── realistic\                       # Realistic models
│   ├── realistic-vision-v5.1.safetensors
│   ├── absolutereality-v1.8.1.safetensors
│   └── epicrealism.safetensors
├── artistic\                        # Artistic models
│   ├── dreamshaper-8.safetensors
│   └── deliberate-v2.safetensors
├── anime\                           # Anime models
│   ├── anything-v5.safetensors
│   └── rev-animated.safetensors
└── custom\                          # Other custom models
```

### Naming Convention

Use descriptive names:
- `model-name-version.safetensors`
- `realistic-vision-v5.1.safetensors` ✅
- `realisticVision_v51.safetensors` ✅
- `model (1).safetensors` ❌

---

## Model Updates

### Checking for New Versions

1. Visit the model's CivitAI page
2. Check "Versions" tab
3. Compare version numbers
4. Read changelog for improvements

### Updating Models

1. Download new version
2. Move to `models/custom/`
3. Delete old version (optional)
4. Restart application to refresh model list

---

## Community Resources

### Finding More Models

- **CivitAI**: https://civitai.com (primary source)
- **HuggingFace**: https://huggingface.co/models (some SD 1.5 models)
- **Reddit**: r/StableDiffusion (model recommendations)

### Learning Prompt Engineering

- CivitAI model pages (example prompts)
- https://prompthero.com (prompt database)
- https://lexica.art (SD prompt search)

### Getting Help

- Check `docs/USER_GUIDE.md` for general usage
- GitHub Issues: [repository URL]
- Discord/Community forums (if available)

---

## Disclaimer

**Important**: This guide is for educational purposes. The developers of this application:
- Do NOT host any AI models
- Do NOT endorse any specific models
- Are NOT responsible for content generated by users
- Are NOT affiliated with CivitAI or model creators

**Users are solely responsible for**:
- Verifying model licenses
- Using models legally and ethically
- Following local laws regarding generated content
- Respecting intellectual property rights

---

## Quick Reference

### Best Models by Use Case

| Use Case | Recommended Model | Alternative |
|----------|------------------|-------------|
| Realistic humans | Realistic Vision v5.1 | AbsoluteReality |
| Artistic/cinematic | DreamShaper 8 | epiCRealism |
| Anime characters | Anything V5 | ReV Animated |
| Portraits | ChilloutMix | Realistic Vision |
| Creative/fantasy | Deliberate v2 | DreamShaper |

### File Size Reference

- SD 1.5 full: ~4-7GB (.safetensors)
- SD 1.5 pruned: ~2-4GB (.safetensors)
- SDXL: ~6-13GB (NOT compatible)

### Performance Targets

| Model + Settings | Expected Time | VRAM |
|-----------------|--------------|------|
| SD 1.5, 512x512, 25 frames, 20 steps | ~2-3 min | ~8GB |
| SD 1.5, 512x512, 48 frames, 30 steps | ~4-6 min | ~10GB |
| SD 1.5, 768x768, 32 frames, 25 steps | ~5-7 min | ~11GB |

*Times based on RTX 3060 12GB*

---

This guide will be updated as new models and features become available. Check the repository for the latest version.
