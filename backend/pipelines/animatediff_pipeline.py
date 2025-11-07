"""
AnimateDiff Pipeline

Implements image-to-video generation using AnimateDiff motion adapter
with Stable Diffusion 1.5 base models.

Features:
- Strong text prompt conditioning
- Custom model support (.safetensors from CivitAI)
- Motion adapter for temporal consistency
- NO safety checker (NSFW-capable for private use)
- Optimized for 12GB VRAM (RTX 3060)

Model Requirements:
- Base: Stable Diffusion 1.5 (NOT SDXL or SD 2.x)
- Motion Adapter: AnimateDiff v1.5-2
- Compatible with CivitAI custom models
"""

import torch
from typing import List, Dict, Any, Optional
from pathlib import Path
from PIL import Image
import numpy as np

try:
    from diffusers import (
        AnimateDiffPipeline as DiffusersAnimateDiffPipeline,
        MotionAdapter,
        DDIMScheduler,
        DPMSolverMultistepScheduler,
        EulerAncestralDiscreteScheduler
    )
    from diffusers.utils import load_image, export_to_video
except ImportError:
    raise ImportError(
        "diffusers not installed. Install with: pip install diffusers==0.24.0"
    )

from .base_pipeline import BasePipeline, ModelLoadError, VRAMError
from utils.prompt_utils import validate_and_prepare_prompts, PromptValidator


class AnimateDiffPipeline(BasePipeline):
    """AnimateDiff pipeline for text-guided image-to-video generation"""

    # AnimateDiff-specific defaults
    DEFAULT_WIDTH = 512
    DEFAULT_HEIGHT = 512
    DEFAULT_NUM_FRAMES = 24
    DEFAULT_FPS = 16
    DEFAULT_NUM_INFERENCE_STEPS = 25
    DEFAULT_GUIDANCE_SCALE = 7.5
    DEFAULT_CLIP_SKIP = 1

    def __init__(
        self,
        model_path: str,
        motion_adapter_path: str,
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.float16,
        enable_xformers: bool = True,
        enable_cpu_offload: bool = True,
        scheduler_type: str = "dpm++"
    ):
        """
        Initialize AnimateDiff pipeline

        Args:
            model_path: Path to SD 1.5 base model (.safetensors or directory)
            motion_adapter_path: Path to motion adapter directory
            device: Device to run on
            torch_dtype: Data type for model weights
            enable_xformers: Enable memory-efficient attention
            enable_cpu_offload: Enable CPU offloading
            scheduler_type: Scheduler type ("dpm++", "euler", or "ddim")
        """
        super().__init__(
            model_path=model_path,
            device=device,
            torch_dtype=torch_dtype,
            enable_xformers=enable_xformers,
            enable_cpu_offload=enable_cpu_offload
        )

        self.motion_adapter_path = Path(motion_adapter_path)
        self.scheduler_type = scheduler_type
        self.motion_adapter = None

    def load_model(self) -> None:
        """
        Load AnimateDiff model into memory

        Raises:
            ModelLoadError: If model loading fails
        """
        if self.is_loaded:
            print("⚠️  Model already loaded")
            return

        print(f"📦 Loading AnimateDiff pipeline:")
        print(f"   Base model: {self.model_path}")
        print(f"   Motion adapter: {self.motion_adapter_path}")

        # Check if paths exist
        if not self.model_path.exists():
            raise ModelLoadError(f"Base model not found: {self.model_path}")

        if not self.motion_adapter_path.exists():
            raise ModelLoadError(f"Motion adapter not found: {self.motion_adapter_path}")

        # Check VRAM availability
        stats = self.vram_monitor.get_vram_stats()
        if stats['available_gb'] < 5.0:
            raise VRAMError(
                f"Insufficient VRAM. Need at least 5GB, have {stats['available_gb']:.2f}GB"
            )

        try:
            # Step 1: Load motion adapter
            print("  Loading motion adapter...")
            self.motion_adapter = MotionAdapter.from_pretrained(
                str(self.motion_adapter_path),
                torch_dtype=self.torch_dtype,
                local_files_only=True
            )
            print("  ✅ Motion adapter loaded")

            # Step 2: Load base model
            print("  Loading base model...")

            # Check if it's a .safetensors file (custom model) or directory
            if self.model_path.suffix == ".safetensors":
                # Load from single file (CivitAI models)
                print(f"  Loading custom model from .safetensors file")

                # Load AnimateDiffPipeline from base SD 1.5, then inject custom weights
                import warnings
                from safetensors.torch import load_file

                # Suppress deprecation warnings
                warnings.filterwarnings('ignore', category=FutureWarning)
                warnings.filterwarnings('ignore', category=UserWarning)

                # Load AnimateDiff pipeline with base SD 1.5 model
                print("  Loading base AnimateDiff pipeline with SD 1.5...")
                self.pipe = DiffusersAnimateDiffPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    motion_adapter=self.motion_adapter,
                    torch_dtype=self.torch_dtype
                )

                # Load custom model weights from .safetensors file
                print(f"  Loading custom weights from {self.model_path.name}...")
                state_dict = load_file(str(self.model_path))

                # Inject custom weights into UNet
                self.pipe.unet.load_state_dict(state_dict, strict=False)
                print("  ✅ Custom model weights loaded")

                # Disable safety checker for NSFW
                self.pipe.safety_checker = None
                print("  🔓 Safety checker disabled (NSFW-capable)")

            else:
                # Load from pretrained directory
                self.pipe = DiffusersAnimateDiffPipeline.from_pretrained(
                    str(self.model_path),
                    motion_adapter=self.motion_adapter,
                    torch_dtype=self.torch_dtype,
                    local_files_only=True
                )

                # CRITICAL: Disable safety checker for NSFW support
                self.pipe.safety_checker = None
                print("  🔓 Safety checker disabled (NSFW-capable)")

            # Step 3: Configure scheduler
            print(f"  Configuring scheduler: {self.scheduler_type}")
            self._configure_scheduler()

            # Step 4: Apply optimizations
            self.apply_optimizations()

            self.is_loaded = True
            print(f"✅ AnimateDiff pipeline loaded successfully\n")

        except Exception as e:
            raise ModelLoadError(f"Failed to load AnimateDiff pipeline: {e}")

    def _configure_scheduler(self) -> None:
        """Configure scheduler based on type"""
        if self.scheduler_type == "dpm++":
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipe.scheduler.config,
                algorithm_type="dpmsolver++",
                use_karras_sigmas=True
            )
        elif self.scheduler_type == "euler":
            self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                self.pipe.scheduler.config
            )
        elif self.scheduler_type == "ddim":
            self.pipe.scheduler = DDIMScheduler.from_config(
                self.pipe.scheduler.config
            )
        else:
            print(f"  ⚠️  Unknown scheduler type: {self.scheduler_type}, using default")

    def generate(
        self,
        image_path: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: int = DEFAULT_NUM_FRAMES,
        fps: int = DEFAULT_FPS,
        num_inference_steps: int = DEFAULT_NUM_INFERENCE_STEPS,
        guidance_scale: float = DEFAULT_GUIDANCE_SCALE,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        seed: int = -1,
        clip_skip: int = DEFAULT_CLIP_SKIP,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate video frames from input image with text prompt

        Args:
            image_path: Path to input image
            prompt: Text prompt describing desired video (REQUIRED)
            negative_prompt: Negative prompt (optional, uses default if not provided)
            num_frames: Number of frames to generate (16-64)
            fps: Frames per second (8-30)
            num_inference_steps: Number of denoising steps (20-50)
            guidance_scale: Prompt adherence (1.0-20.0, higher = stronger)
            width: Output width (must be divisible by 8, recommend 512)
            height: Output height (must be divisible by 8, recommend 512)
            seed: Random seed (-1 for random)
            clip_skip: CLIP skip layers (1-3)
            **kwargs: Additional parameters

        Returns:
            List of PIL Image frames

        Raises:
            RuntimeError: If model not loaded
            VRAMError: If insufficient VRAM
            ValueError: If prompt is invalid
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Validate and prepare prompts
        validator = PromptValidator()
        is_valid, proc_prompt, proc_negative, error = validate_and_prepare_prompts(
            prompt=prompt,
            negative_prompt=negative_prompt,
            pipeline="animatediff"
        )

        if not is_valid:
            raise ValueError(f"Prompt validation failed: {error}")

        # Optionally enhance prompt with quality tags
        proc_prompt = validator.enhance_prompt(
            proc_prompt,
            add_quality_tags=True,
            pipeline="animatediff"
        )

        print(f"🎬 Generating video with AnimateDiff:")
        print(f"   Prompt: {proc_prompt}")
        print(f"   Negative: {proc_negative}")
        print(f"   Frames: {num_frames} @ {fps} FPS")
        print(f"   Resolution: {width}x{height}")
        print(f"   Guidance Scale: {guidance_scale}")
        print(f"   Inference Steps: {num_inference_steps}")

        # Check VRAM before generation
        params = {
            'pipeline': 'animatediff',
            'width': width,
            'height': height,
            'numFrames': num_frames
        }
        estimated_vram = self.estimate_vram_usage(params)
        available_vram = self.vram_monitor.get_available_vram()

        print(f"   Estimated VRAM: {estimated_vram:.2f}GB / {available_vram:.2f}GB available")

        if estimated_vram > available_vram:
            raise VRAMError(
                f"Insufficient VRAM. Estimated {estimated_vram:.2f}GB, "
                f"available {available_vram:.2f}GB. "
                f"Try reducing num_frames, resolution, or num_inference_steps."
            )

        # Load and preprocess image
        image = self.load_and_preprocess_image(image_path, width, height)

        # Set random seed if specified
        generator = None
        if seed >= 0:
            generator = torch.Generator(device=self.device).manual_seed(seed)
            print(f"   Seed: {seed}")
        else:
            print(f"   Seed: Random")

        # Clear cache before generation
        self.clear_cache()

        try:
            # Report start
            self.report_progress(0, num_inference_steps, "Starting generation...")

            # Generate frames with strong text conditioning
            output = self.pipe(
                prompt=proc_prompt,
                negative_prompt=proc_negative,
                image=image,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                generator=generator,
            )

            frames = output.frames[0]

            # Report completion
            self.report_progress(
                num_inference_steps,
                num_inference_steps,
                "Generation complete!"
            )

            print(f"✅ Generated {len(frames)} frames\n")

            return frames

        except torch.cuda.OutOfMemoryError:
            self.clear_cache()
            raise VRAMError(
                "Out of VRAM during generation. Try:\n"
                "  - Reducing num_frames\n"
                "  - Reducing resolution (512x512 recommended)\n"
                "  - Reducing num_inference_steps\n"
                "  - Reducing batch size (if using multiple prompts)"
            )
        except Exception as e:
            self.clear_cache()
            raise RuntimeError(f"Generation failed: {e}")

    def get_default_params(self) -> Dict[str, Any]:
        """
        Get default generation parameters

        Returns:
            Dictionary of default parameters
        """
        return {
            'width': self.DEFAULT_WIDTH,
            'height': self.DEFAULT_HEIGHT,
            'num_frames': self.DEFAULT_NUM_FRAMES,
            'fps': self.DEFAULT_FPS,
            'num_inference_steps': self.DEFAULT_NUM_INFERENCE_STEPS,
            'guidance_scale': self.DEFAULT_GUIDANCE_SCALE,
            'clip_skip': self.DEFAULT_CLIP_SKIP,
            'seed': -1
        }

    def get_pipeline_type(self) -> str:
        """
        Get pipeline type identifier

        Returns:
            "animatediff"
        """
        return "animatediff"


# Example usage
if __name__ == "__main__":
    print("AnimateDiff Pipeline Test\n")

    # Initialize pipeline with custom model
    pipeline = AnimateDiffPipeline(
        model_path="/mnt/d/VideoGenerator/models/realistic-vision/realisticVision_v51.safetensors",
        motion_adapter_path="/mnt/d/VideoGenerator/models/animatediff",
        device="cuda",
        enable_xformers=True,
        enable_cpu_offload=True,
        scheduler_type="dpm++"
    )

    # Load model
    print("Loading model...")
    pipeline.load_model()

    # Get recommended settings
    print("\nRecommended settings:")
    rec = pipeline.get_recommended_settings()
    for key, value in rec.items():
        print(f"  {key}: {value}")

    # Test parameters
    test_params = {
        'image_path': 'test_image.jpg',
        'prompt': 'slow cinematic zoom in, woman turning head, wind blowing through hair, dramatic lighting, masterpiece, highly detailed',
        'negative_prompt': 'blurry, distorted, low quality, static, ugly, deformed',
        'num_frames': 24,
        'fps': 16,
        'guidance_scale': 7.5,
        'width': 512,
        'height': 512
    }

    # Estimate VRAM
    estimated = pipeline.estimate_vram_usage({
        'pipeline': 'animatediff',
        'width': test_params['width'],
        'height': test_params['height'],
        'numFrames': test_params['num_frames']
    })
    print(f"\nEstimated VRAM usage: {estimated:.2f}GB")

    print("\nPipeline ready for generation!")
    print("Call pipeline.generate(**params) to generate video frames")
