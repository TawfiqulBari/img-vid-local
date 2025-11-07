# Technical Specification: Image-to-Video Generator

## System Architecture

### High-Level Overview

```
┌────────────────────────────────────────────────────────────┐
│                     Windows User                            │
└───────────────────────┬────────────────────────────────────┘
                        │
             ┌──────────▼──────────┐
             │  WPF Desktop App    │
             │  (C# / .NET 6.0)    │
             │                     │
             │  - Image Upload     │
             │  - Prompt Input     │
             │  - Model Selection  │
             │  - Video Preview    │
             └──────────┬──────────┘
                        │
                Subprocess Call
               (JSON Parameters)
                        │
             ┌──────────▼──────────┐
             │  Python Backend     │
             │  (generate.py)      │
             │                     │
             │  - Pipeline Router  │
             │  - Model Manager    │
             │  - Video Service    │
             └──────────┬──────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
    ┌───────▼────────┐    ┌────────▼────────┐
    │  SVD Pipeline  │    │ AnimateDiff     │
    │                │    │ Pipeline        │
    │ - Limited text │    │ - Strong text   │
    │   conditioning │    │   conditioning  │
    │ - Fast         │    │ - Customizable  │
    └───────┬────────┘    └────────┬────────┘
            │                      │
            └───────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │  D:\VideoGenerator   │
             │  \models\            │
             │                     │
             │  - svd-xt\          │
             │  - animatediff\     │
             │  - realistic-vision\│
             │  - custom\          │
             └─────────────────────┘
```

---

## Component Specifications

### 1. Frontend: WPF Desktop Application

**Technology Stack**:
- **.NET 6.0** (net6.0-windows, x64 only)
- **WPF** for UI
- **System.Text.Json** for JSON serialization
- **MediaElement** for video playback

**Project Structure**:
```
frontend/VideoGenerator/
├── VideoGenerator.csproj
├── App.xaml                        # Application definition
├── App.xaml.cs                     # Application startup
├── MainWindow.xaml                 # Main UI definition
├── MainWindow.xaml.cs              # Main UI logic
├── Models/
│   ├── GenerationParams.cs        # Request parameters
│   ├── GenerationResult.cs        # Response data
│   └── PipelineType.cs            # Enum: SVD, AnimateDiff
├── Services/
│   ├── PythonBackend.cs           # Subprocess management
│   ├── PathUtils.cs               # Path conversion
│   └── ConfigService.cs           # Settings persistence
├── ViewModels/
│   └── MainViewModel.cs           # MVVM data binding
├── Views/
│   ├── PromptExamplesDialog.xaml
│   ├── PromptExamplesDialog.xaml.cs
│   ├── ModelBrowserDialog.xaml
│   └── ModelBrowserDialog.xaml.cs
├── Resources/
│   ├── Icons/
│   └── Styles.xaml                # WPF styles
└── Properties/
    └── AssemblyInfo.cs
```

**Key Classes**:

#### `GenerationParams.cs`
```csharp
using System.Text.Json.Serialization;

namespace VideoGenerator.Models
{
    public class GenerationParams
    {
        [JsonPropertyName("pipeline")]
        public string Pipeline { get; set; } // "svd" or "animatediff"

        [JsonPropertyName("baseModel")]
        public string BaseModel { get; set; } // Path to model

        [JsonPropertyName("motionAdapter")]
        public string MotionAdapter { get; set; } // For AnimateDiff only

        [JsonPropertyName("imagePath")]
        public string ImagePath { get; set; }

        [JsonPropertyName("prompt")]
        public string Prompt { get; set; } // REQUIRED

        [JsonPropertyName("negativePrompt")]
        public string NegativePrompt { get; set; }

        [JsonPropertyName("numFrames")]
        public int NumFrames { get; set; } = 25;

        [JsonPropertyName("fps")]
        public int FPS { get; set; } = 8;

        [JsonPropertyName("guidanceScale")]
        public float GuidanceScale { get; set; } = 7.5f;

        [JsonPropertyName("motionBucketId")]
        public int MotionBucketId { get; set; } = 127;

        [JsonPropertyName("numInferenceSteps")]
        public int NumInferenceSteps { get; set; } = 25;

        [JsonPropertyName("decodeChunkSize")]
        public int DecodeChunkSize { get; set; } = 4;

        [JsonPropertyName("seed")]
        public int Seed { get; set; } = -1;

        [JsonPropertyName("outputPath")]
        public string OutputPath { get; set; }

        public string ToJson()
        {
            return JsonSerializer.Serialize(this, new JsonSerializerOptions
            {
                WriteIndented = false
            });
        }
    }
}
```

#### `PythonBackend.cs`
```csharp
using System;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace VideoGenerator.Services
{
    public class PythonBackend
    {
        private readonly string _pythonExePath;
        private readonly string _generateScriptPath;

        public PythonBackend(string pythonExePath, string generateScriptPath)
        {
            _pythonExePath = pythonExePath;
            _generateScriptPath = generateScriptPath;
        }

        public async Task<GenerationResult> GenerateVideoAsync(
            GenerationParams parameters,
            IProgress<ProgressUpdate> progress,
            CancellationToken cancellationToken)
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = _pythonExePath,
                Arguments = $\"{_generateScriptPath} \\\"{parameters.ToJson().Replace(\"\\\"\", \"\\\\\\\"\")}\\\" \",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = Path.GetDirectoryName(_generateScriptPath)
            };

            using var process = new Process { StartInfo = startInfo };

            process.ErrorDataReceived += (sender, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    // Parse progress updates from stderr
                    try
                    {
                        var progressUpdate = JsonSerializer.Deserialize<ProgressUpdate>(e.Data);
                        progress?.Report(progressUpdate);
                    }
                    catch
                    {
                        // Not JSON, just log message
                        Console.WriteLine(e.Data);
                    }
                }
            };

            process.Start();
            process.BeginErrorReadLine();

            var output = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync(cancellationToken);

            if (process.ExitCode != 0)
            {
                throw new Exception($"Video generation failed: {output}");
            }

            var result = JsonSerializer.Deserialize<GenerationResult>(output);
            return result;
        }
    }

    public class ProgressUpdate
    {
        [JsonPropertyName("progress")]
        public int Progress { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; }
    }
}
```

---

### 2. Backend: Python AI Inference Engine

**Technology Stack**:
- **Python 3.10**
- **PyTorch 2.1.0** with CUDA 11.8
- **diffusers 0.24.0** (SVD + AnimateDiff pipelines)
- **transformers 4.36.0**
- **accelerate 0.25.0**
- **xformers 0.0.23** (memory optimization)
- **opencv-python 4.8.1.78** (video encoding)
- **Pillow 10.1.0** (image processing)

**Project Structure**:
```
backend/
├── generate.py                    # CLI entry point
├── pipelines/
│   ├── __init__.py
│   ├── base_pipeline.py          # Abstract base
│   ├── svd_pipeline.py           # SVD implementation
│   └── animatediff_pipeline.py   # AnimateDiff implementation
├── services/
│   ├── __init__.py
│   ├── video_service.py          # High-level API
│   └── model_manager.py          # Model loading/caching
├── utils/
│   ├── __init__.py
│   ├── path_utils.py             # Path conversion
│   ├── vram_utils.py             # VRAM management
│   ├── prompt_utils.py           # Prompt processing
│   ├── config.py                 # Configuration
│   └── model_validator.py        # Model compatibility
├── download_models.py             # Model downloader
├── check_gpu.py                   # CUDA verification
├── test_generation.py             # Testing utility
└── requirements.txt
```

**Key Classes**:

#### `base_pipeline.py`
```python
from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any
import torch

class BasePipeline(ABC):
    def __init__(self, model_path: str, device: str = "cuda"):
        self.model_path = model_path
        self.device = device
        self.pipe = None

    @abstractmethod
    def load_model(self):
        """Load the AI model"""
        pass

    @abstractmethod
    def generate(
        self,
        image_path: str,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate video from image with text prompt"""
        pass

    def apply_optimizations(self):
        """Apply VRAM optimizations"""
        if self.pipe is None:
            return

        # CPU offloading for non-critical components
        self.pipe.enable_model_cpu_offload()

        # VAE optimizations
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()

        # Memory-efficient attention
        try:
            self.pipe.enable_xformers_memory_efficient_attention()
        except:
            print("xformers not available, using standard attention")

    def get_vram_usage(self) -> float:
        """Get current VRAM usage in GB"""
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024 ** 3)
            return round(allocated, 2)
        return 0.0
```

#### `svd_pipeline.py`
```python
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video
from PIL import Image
from .base_pipeline import BasePipeline

class SVDPipeline(BasePipeline):
    def load_model(self):
        """Load SVD-XT model WITHOUT safety checker"""
        self.pipe = StableVideoDiffusionPipeline.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            variant="fp16",
            local_files_only=True  # Offline operation
        )

        # CRITICAL: Disable safety checker for NSFW
        self.pipe.safety_checker = None

        self.pipe.to(self.device)
        self.apply_optimizations()

    def generate(
        self,
        image_path: str,
        prompt: str,  # Limited effect in SVD
        num_frames: int = 25,
        fps: int = 8,
        motion_bucket_id: int = 127,
        num_inference_steps: int = 25,
        decode_chunk_size: int = 4,
        seed: int = -1,
        output_path: str = "output.mp4",
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        Generate video using SVD

        Note: SVD has limited text prompt conditioning.
        Prompt is used more as a guide than strict instruction.
        """
        if progress_callback:
            progress_callback(10, "Loading image...")

        # Set seed
        if seed != -1:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = None

        # Load and preprocess image
        image = load_image(image_path)
        image = image.resize((1024, 576))  # 16:9 aspect ratio

        if progress_callback:
            progress_callback(20, "Generating frames...")

        # Generate frames
        frames = self.pipe(
            image=image,
            num_frames=num_frames,
            decode_chunk_size=decode_chunk_size,
            num_inference_steps=num_inference_steps,
            motion_bucket_id=motion_bucket_id,
            generator=generator
        ).frames[0]

        if progress_callback:
            progress_callback(90, "Encoding video...")

        # Export to video
        export_to_video(frames, output_path, fps=fps)

        if progress_callback:
            progress_callback(100, "Complete!")

        return output_path
```

#### `animatediff_pipeline.py`
```python
import torch
from diffusers import AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
from diffusers.utils import export_to_video
from PIL import Image
from .base_pipeline import BasePipeline

class AnimateDiffPipeline(BasePipeline):
    def __init__(self, base_model: str, motion_adapter: str, device: str = "cuda"):
        self.base_model = base_model
        self.motion_adapter_path = motion_adapter
        super().__init__(base_model, device)

    def load_model(self):
        """Load AnimateDiff with custom SD base model WITHOUT safety checker"""
        # Load motion adapter
        adapter = MotionAdapter.from_pretrained(
            self.motion_adapter_path,
            torch_dtype=torch.float16,
            local_files_only=True
        )

        # Load base model (supports .safetensors from CivitAI)
        if self.base_model.endswith('.safetensors') or self.base_model.endswith('.ckpt'):
            # Load from single file (CivitAI models)
            self.pipe = AnimateDiffPipeline.from_single_file(
                self.base_model,
                motion_adapter=adapter,
                torch_dtype=torch.float16,
                load_safety_checker=False  # CRITICAL for NSFW
            )
        else:
            # Load from HuggingFace repo
            self.pipe = AnimateDiffPipeline.from_pretrained(
                self.base_model,
                motion_adapter=adapter,
                torch_dtype=torch.float16,
                safety_checker=None,  # CRITICAL for NSFW
                local_files_only=True
            )

        # Set scheduler
        self.pipe.scheduler = EulerDiscreteScheduler.from_config(
            self.pipe.scheduler.config,
            timestep_spacing="trailing",
            beta_schedule="linear"
        )

        self.pipe.to(self.device)
        self.apply_optimizations()

    def generate(
        self,
        image_path: str,
        prompt: str,  # Strong conditioning
        negative_prompt: str = "",
        num_frames: int = 16,
        fps: int = 8,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 25,
        seed: int = -1,
        output_path: str = "output.mp4",
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        Generate video using AnimateDiff with strong text prompt control
        """
        if progress_callback:
            progress_callback(10, "Loading image...")

        # Set seed
        if seed != -1:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = None

        # Load image
        image = Image.open(image_path).convert("RGB")
        image = image.resize((512, 512))

        if progress_callback:
            progress_callback(20, "Generating frames with prompt...")

        # Generate frames with text conditioning
        frames = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
            # Use image as init image for img2img
            image=image,
            strength=0.8  # How much to transform the image
        ).frames[0]

        if progress_callback:
            progress_callback(90, "Encoding video...")

        # Export to video
        export_to_video(frames, output_path, fps=fps)

        if progress_callback:
            progress_callback(100, "Complete!")

        return output_path
```

---

### 3. Communication Protocol

**Format**: JSON over subprocess stdin/stdout

**Request Structure** (C# → Python):
```json
{
  "pipeline": "animatediff",
  "baseModel": "D:\\VideoGenerator\\models\\realistic-vision\\model.safetensors",
  "motionAdapter": "D:\\VideoGenerator\\models\\animatediff\\",
  "imagePath": "D:\\Images\\photo.jpg",
  "prompt": "slow cinematic zoom in, woman turning head slowly, wind blowing through hair, golden hour lighting, dreamy atmosphere, film grain",
  "negativePrompt": "blurry, distorted, low quality, static, ugly, deformed, low res",
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

**Response Structure** (Python → C#):

Success:
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

Error:
```json
{
  "status": "error",
  "error": "CUDA out of memory",
  "message": "Try reducing decode_chunk_size or num_frames",
  "suggestions": [
    "Set decode_chunk_size to 2",
    "Reduce num_frames to 32",
    "Close other GPU applications"
  ]
}
```

**Progress Updates** (Python → C# via stderr):
```json
{"progress": 10, "message": "Loading model..."}
{"progress": 20, "message": "Processing image..."}
{"progress": 35, "message": "Generating frame 10/48..."}
{"progress": 60, "message": "Generating frame 30/48..."}
{"progress": 90, "message": "Encoding video..."}
{"progress": 100, "message": "Complete!"}
```

---

### 4. Path Conversion System

**Challenge**: WSL uses `/mnt/d/` while Windows uses `D:\`

**Python Implementation** (`utils/path_utils.py`):
```python
import os
import platform

def windows_to_wsl_path(windows_path: str) -> str:
    """
    Convert Windows path to WSL path
    D:\\VideoGenerator\\models -> /mnt/d/VideoGenerator/models
    """
    if not windows_path:
        return windows_path

    # Normalize path
    path = windows_path.replace('\\\\', '\\').rstrip('\\')

    # Check if it's a drive letter path
    if len(path) >= 2 and path[1] == ':':
        drive = path[0].lower()
        rest = path[2:].replace('\\', '/')
        return f"/mnt/{drive}{rest}"

    # Already WSL path or relative path
    return path.replace('\\', '/')

def wsl_to_windows_path(wsl_path: str) -> str:
    """
    Convert WSL path to Windows path
    /mnt/d/VideoGenerator/models -> D:\\VideoGenerator\\models
    """
    if not wsl_path:
        return wsl_path

    # Check if it's a /mnt/ path
    if wsl_path.startswith('/mnt/'):
        parts = wsl_path[5:].split('/', 1)
        if len(parts) >= 1:
            drive = parts[0].upper()
            rest = parts[1] if len(parts) > 1 else ''
            return f"{drive}:\\{rest.replace('/', '\\')}"

    # Already Windows path
    return wsl_path.replace('/', '\\')

def normalize_path(path: str) -> str:
    """
    Normalize path for current system
    """
    system = platform.system()

    if system == "Windows":
        return wsl_to_windows_path(path)
    elif system == "Linux":
        # Check if WSL
        if os.path.exists('/mnt/c'):
            return windows_to_wsl_path(path)

    return path
```

**C# Implementation** (`Services/PathUtils.cs`):
```csharp
using System;
using System.Text.RegularExpressions;

namespace VideoGenerator.Services
{
    public static class PathUtils
    {
        public static string WindowsToWSLPath(string windowsPath)
        {
            if (string.IsNullOrWhiteSpace(windowsPath))
                return windowsPath;

            var path = windowsPath.TrimEnd('\\');

            // Check for drive letter (C:, D:, etc.)
            if (path.Length >= 2 && path[1] == ':')
            {
                var drive = char.ToLower(path[0]);
                var rest = path.Length > 2 ? path.Substring(2).Replace('\\', '/') : "";
                return $"/mnt/{drive}{rest}";
            }

            return path.Replace('\\', '/');
        }

        public static string WSLToWindowsPath(string wslPath)
        {
            if (string.IsNullOrWhiteSpace(wslPath))
                return wslPath;

            // Check for /mnt/X/ pattern
            if (wslPath.StartsWith("/mnt/"))
            {
                var parts = wslPath.Substring(5).Split(new[] { '/' }, 2);
                if (parts.Length >= 1)
                {
                    var drive = parts[0].ToUpper();
                    var rest = parts.Length > 1 ? parts[1].Replace('/', '\\') : "";
                    return $"{drive}:\\{rest}";
                }
            }

            return wslPath.Replace('/', '\\');
        }
    }
}
```

---

### 5. VRAM Management Strategy

**Target Hardware**: RTX 3060 (12GB VRAM)

**VRAM Budget**:
- Base model: ~5-6GB (SVD or SD 1.5)
- Frame buffer: Variable based on resolution and frames
- Overhead: ~1-2GB

**Dynamic Optimization** (`utils/vram_utils.py`):
```python
import torch
from typing import Dict, Any

class VRAMOptimizer:
    def __init__(self, target_vram_gb: float = 11.0):
        self.target_vram = target_vram_gb
        self.total_vram = self._get_total_vram()

    def _get_total_vram(self) -> float:
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        return 0.0

    def get_available_vram(self) -> float:
        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            return free / (1024 ** 3)
        return 0.0

    def estimate_vram_usage(self, params: Dict[str, Any]) -> float:
        """
        Estimate VRAM usage based on parameters
        """
        # Base model size
        pipeline = params.get('pipeline', 'svd')
        if pipeline == 'svd':
            base = 6.0  # SVD model
        else:
            base = 5.0  # SD 1.5 + AnimateDiff

        # Frame buffer calculation
        width = params.get('width', 512)
        height = params.get('height', 512)
        num_frames = params.get('numFrames', 25)
        decode_chunk = params.get('decodeChunkSize', 4)

        # Rough estimate: pixels * frames * bytes per pixel / chunk size
        frame_buffer = (width * height * num_frames * 4) / (1024 ** 3)
        frame_buffer /= decode_chunk

        total = base + frame_buffer + 1.5  # +1.5GB overhead
        return round(total, 2)

    def optimize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically adjust parameters to fit VRAM
        """
        estimated = self.estimate_vram_usage(params)
        available = self.get_available_vram()

        optimized = params.copy()

        if estimated > available:
            print(f"Warning: Estimated VRAM ({estimated}GB) exceeds available ({available}GB)")

            # Strategy 1: Reduce decode_chunk_size
            if optimized.get('decodeChunkSize', 4) > 2:
                optimized['decodeChunkSize'] = 2
                print("Reduced decode_chunk_size to 2")

            # Re-estimate
            estimated = self.estimate_vram_usage(optimized)

            # Strategy 2: Reduce num_frames
            if estimated > available:
                max_frames = int(optimized['numFrames'] * (available / estimated))
                optimized['numFrames'] = max(16, max_frames)
                print(f"Reduced num_frames to {optimized['numFrames']}")

        return optimized
```

**VRAM Limits Table**:

| Pipeline | Resolution | Max Frames | Duration @ 24fps | VRAM |
|----------|-----------|-----------|------------------|------|
| SVD | 512x512 | 250 | 10.4s | ~9GB |
| SVD | 768x768 | 80 | 3.3s | ~11GB |
| SVD | 1024x576 (16:9) | 60 | 2.5s | ~11.5GB |
| AnimateDiff | 512x512 | 64 | 2.7s | ~8GB |
| AnimateDiff | 768x768 | 32 | 1.3s | ~11GB |

---

### 6. Model Management

**Model Registry** (`D:\VideoGenerator\models\models.json`):
```json
{
  "svd": {
    "svd-xt": {
      "path": "D:\\VideoGenerator\\models\\svd-xt",
      "type": "svd",
      "size": "10GB",
      "description": "Stable Video Diffusion XT",
      "source": "stabilityai/stable-video-diffusion-img2vid-xt"
    }
  },
  "animatediff": {
    "motion-adapter": {
      "path": "D:\\VideoGenerator\\models\\animatediff",
      "type": "motion_adapter",
      "size": "3GB",
      "description": "AnimateDiff Motion Adapter v1.5-2",
      "source": "guoyww/animatediff-motion-adapter-v1-5-2"
    },
    "realistic-vision": {
      "path": "D:\\VideoGenerator\\models\\realistic-vision\\model.safetensors",
      "type": "sd15",
      "size": "2GB",
      "description": "Realistic Vision v5.1 (NSFW-capable)",
      "source": "civitai.com/models/4201",
      "nsfw": true
    }
  },
  "custom": []
}
```

---

### 7. Error Handling & Logging

**Error Categories**:

1. **User Input Errors** (show in UI):
   - Empty prompt
   - Invalid image format
   - Parameters out of range

2. **System Errors** (show setup wizard):
   - Python not found
   - CUDA not available
   - Models not downloaded

3. **Generation Errors** (retry with optimizations):
   - Out of VRAM
   - Timeout (>10 minutes)
   - Corrupted output

4. **Critical Errors** (show recovery dialog):
   - GPU driver crash
   - Disk full
   - Process killed

**Logging** (`backend/utils/logger.py`):
```python
import logging
import sys
from datetime import datetime

def setup_logger(log_file: str = None):
    logger = logging.getLogger("video_generator")
    logger.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    logger.addHandler(console)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

    return logger
```

---

### 8. Security & Privacy

**Security Measures**:
1. **Input Validation**: Sanitize all file paths
2. **Subprocess Sandboxing**: No shell=True, no eval()
3. **Resource Limits**: Max VRAM, timeout, file size
4. **Local-Only Processing**: No network after setup

**Privacy Guarantees**:
1. All processing happens locally
2. No telemetry or analytics
3. No cloud uploads
4. User data stays on device

**Disclaimers**:
- Age verification for NSFW features
- User responsibility for generated content
- Compliance with local laws required

---

### 9. Performance Optimization

**Startup**:
- Lazy load models (on first generation)
- Cache models in VRAM between generations
- Preload UI while models load in background

**Generation**:
- FP16 precision (50% memory savings)
- xformers attention (30% speedup)
- CPU offloading for unused components
- Chunked VAE decoding

**UI**:
- Async subprocess calls
- Progress updates every 5%
- Non-blocking video preview
- Background model preloading

---

### 10. Testing Strategy

**Unit Tests**:
- Path conversion (WSL ↔ Windows)
- VRAM estimation accuracy
- Parameter validation logic
- Model compatibility checker

**Integration Tests**:
- C# to Python subprocess communication
- JSON serialization/deserialization
- Progress update streaming
- Error propagation

**Performance Tests**:
- Generation time benchmarks
- VRAM usage profiling
- Concurrent generation stress test
- Memory leak detection

**User Acceptance Tests**:
- Fresh Windows install simulation
- First-run model download
- 10+ consecutive generations
- Error recovery scenarios

---

## Technology Versions (Locked)

### Python Dependencies (`requirements.txt`):
```
torch==2.1.0
torchvision==0.16.0
torchaudio==2.1.0
diffusers==0.24.0
transformers==4.36.0
accelerate==0.25.0
safetensors==0.4.1
xformers==0.0.23
opencv-python==4.8.1.78
Pillow==10.1.0
huggingface-hub==0.19.4
requests==2.31.0
tqdm==4.66.1
```

### C# Dependencies (`.csproj`):
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net6.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
    <PlatformTarget>x64</PlatformTarget>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="System.Text.Json" Version="6.0.0" />
  </ItemGroup>
</Project>
```

---

## Deployment Architecture

```
Windows Installation:
C:\Program Files\VideoGenerator\
├── VideoGenerator.exe              # WPF application
├── VideoGenerator.dll
├── System.Text.Json.dll
└── ... (.NET dependencies)

D:\VideoGenerator\
├── backend\
│   ├── python310.dll               # Embedded Python
│   ├── python.exe
│   ├── Lib\                        # Standard library
│   ├── Lib\site-packages\          # Installed packages
│   ├── generate.py
│   ├── pipelines\
│   ├── services\
│   └── utils\
├── models\
│   ├── svd-xt\                     # ~10GB
│   ├── animatediff\                # ~3GB
│   ├── realistic-vision\           # ~2GB
│   └── custom\                     # User models
├── output\                         # Generated videos
├── logs\
│   └── generation.log
└── config.json                     # User settings
```

---

This specification provides complete technical documentation for implementing the dual-pipeline image-to-video generator with NSFW support and text prompt control.
