"""
Stable Video Diffusion (SVD) Pipeline

Implements image-to-video generation using Stability AI's SVD-XT model.

Features:
- Fast video generation (25-60 frames)
- Limited text conditioning (primarily image-driven)
- Motion bucket control for motion intensity
- NO safety checker (NSFW-capable for private use)
- Optimized for 12GB VRAM (RTX 3060)

Model: stabilityai/stable-video-diffusion-img2vid-xt
"""

import torch
from typing import List, Dict, Any, Optional
from pathlib import Path
from PIL import Image
import numpy as np

try:
    from diffusers import StableVideoDiffusionPipeline
    from diffusers.utils import load_image, export_to_video
except ImportError:
    raise ImportError(
        "diffusers not installed. Install with: pip install diffusers==0.24.0"
    )

from .base_pipeline import BasePipeline, ModelLoadError, VRAMError
from utils.prompt_utils import validate_and_prepare_prompts


class SVDPipeline(BasePipeline):
    """Stable Video Diffusion pipeline for image-to-video generation"""

    # SVD-specific defaults
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 576
    DEFAULT_NUM_FRAMES = 25
    DEFAULT_FPS = 8
    DEFAULT_MOTION_BUCKET_ID = 127
    DEFAULT_NOISE_AUG_STRENGTH = 0.02
    DEFAULT_DECODE_CHUNK_SIZE = 4
    DEFAULT_NUM_INFERENCE_STEPS = 25

    def __init__(
        self,
        model_path: str,
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.float16,
        enable_xformers: bool = True,
        enable_cpu_offload: bool = True
    ):
        """
        Initialize SVD pipeline

        Args:
            model_path: Path to SVD model directory
            device: Device to run on
            torch_dtype: Data type for model weights
            enable_xformers: Enable memory-efficient attention
            enable_cpu_offload: Enable CPU offloading
        """
        super().__init__(
            model_path=model_path,
            device=device,
            torch_dtype=torch_dtype,
            enable_xformers=enable_xformers,
            enable_cpu_offload=enable_cpu_offload
        )

    def load_model(self) -> None:
        """
        Load SVD model into memory

        Raises:
            ModelLoadError: If model loading fails
        """
        if self.is_loaded:
            print("⚠️  Model already loaded")
            return

        print(f"📦 Loading Stable Video Diffusion model from: {self.model_path}")

        # Check if model directory exists
        if not self.model_path.exists():
            raise ModelLoadError(f"Model directory not found: {self.model_path}")

        # Check VRAM availability
        stats = self.vram_monitor.get_vram_stats()
        if stats['available_gb'] < 6.0:
            raise VRAMError(
                f"Insufficient VRAM. Need at least 6GB, have {stats['available_gb']:.2f}GB"
            )

        try:
            # Load pipeline
            self.pipe = StableVideoDiffusionPipeline.from_pretrained(
                str(self.model_path),
                torch_dtype=self.torch_dtype,
                variant="fp16",
                local_files_only=True  # Critical for offline operation
            )

            # CRITICAL: Disable safety checker for NSFW support
            # This is intentional for private, local use
            self.pipe.safety_checker = None
            print("  🔓 Safety checker disabled (NSFW-capable)")

            # Apply optimizations
            self.apply_optimizations()

            self.is_loaded = True
            print(f"✅ SVD model loaded successfully\n")

        except Exception as e:
            raise ModelLoadError(f"Failed to load SVD model: {e}")

    def generate(
        self,
        image_path: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: int = DEFAULT_NUM_FRAMES,
        fps: int = DEFAULT_FPS,
        motion_bucket_id: int = DEFAULT_MOTION_BUCKET_ID,
        noise_aug_strength: float = DEFAULT_NOISE_AUG_STRENGTH,
        decode_chunk_size: int = DEFAULT_DECODE_CHUNK_SIZE,
        num_inference_steps: int = DEFAULT_NUM_INFERENCE_STEPS,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        seed: int = -1,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate video frames from input image

        Args:
            image_path: Path to input image
            prompt: Text prompt (note: SVD has limited text conditioning)
            negative_prompt: Negative prompt (optional)
            num_frames: Number of frames to generate (14-60)
            fps: Frames per second (6-30)
            motion_bucket_id: Motion intensity (1-255, default 127)
            noise_aug_strength: Noise augmentation strength (0.0-0.1)
            decode_chunk_size: Chunk size for decoding (lower = less VRAM)
            num_inference_steps: Number of denoising steps (15-50)
            width: Output width (must be divisible by 8)
            height: Output height (must be divisible by 8)
            seed: Random seed (-1 for random)
            **kwargs: Additional parameters

        Returns:
            List of PIL Image frames

        Raises:
            RuntimeError: If model not loaded
            VRAMError: If insufficient VRAM
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Validate and prepare prompts
        is_valid, proc_prompt, proc_negative, error = validate_and_prepare_prompts(
            prompt=prompt,
            negative_prompt=negative_prompt,
            pipeline="svd"
        )

        if not is_valid:
            raise ValueError(f"Prompt validation failed: {error}")

        print(f"🎬 Generating video with SVD:")
        print(f"   Prompt: {proc_prompt}")
        print(f"   Frames: {num_frames} @ {fps} FPS")
        print(f"   Resolution: {width}x{height}")
        print(f"   Motion Bucket ID: {motion_bucket_id}")
        print(f"   Inference Steps: {num_inference_steps}")

        # Check VRAM before generation
        params = {
            'pipeline': 'svd',
            'width': width,
            'height': height,
            'numFrames': num_frames,
            'decodeChunkSize': decode_chunk_size
        }
        estimated_vram = self.estimate_vram_usage(params)
        available_vram = self.vram_monitor.get_available_vram()

        print(f"   Estimated VRAM: {estimated_vram:.2f}GB / {available_vram:.2f}GB available")

        if estimated_vram > available_vram:
            raise VRAMError(
                f"Insufficient VRAM. Estimated {estimated_vram:.2f}GB, "
                f"available {available_vram:.2f}GB. "
                f"Try reducing num_frames, resolution, or decode_chunk_size."
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

            # Generate frames
            # Note: SVD has limited text conditioning, so prompt is mainly informational
            # The model is primarily driven by the input image
            frames = self.pipe(
                image=image,
                num_frames=num_frames,
                motion_bucket_id=motion_bucket_id,
                noise_aug_strength=noise_aug_strength,
                decode_chunk_size=decode_chunk_size,
                num_inference_steps=num_inference_steps,
                generator=generator,
                # SVD doesn't directly use text prompts, but we log it
            ).frames[0]

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
                "  - Reducing decode_chunk_size to 2\n"
                "  - Reducing resolution\n"
                "  - Reducing num_inference_steps"
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
            'motion_bucket_id': self.DEFAULT_MOTION_BUCKET_ID,
            'noise_aug_strength': self.DEFAULT_NOISE_AUG_STRENGTH,
            'decode_chunk_size': self.DEFAULT_DECODE_CHUNK_SIZE,
            'num_inference_steps': self.DEFAULT_NUM_INFERENCE_STEPS,
            'seed': -1
        }

    def get_pipeline_type(self) -> str:
        """
        Get pipeline type identifier

        Returns:
            "svd"
        """
        return "svd"


# Example usage
if __name__ == "__main__":
    print("SVD Pipeline Test\n")

    # Initialize pipeline
    pipeline = SVDPipeline(
        model_path="/mnt/d/VideoGenerator/models/svd-xt",
        device="cuda",
        enable_xformers=True,
        enable_cpu_offload=True
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
        'prompt': 'slow cinematic zoom in, dramatic lighting, smooth camera movement',
        'num_frames': 25,
        'fps': 8,
        'motion_bucket_id': 127,
        'width': 1024,
        'height': 576
    }

    # Estimate VRAM
    estimated = pipeline.estimate_vram_usage({
        'pipeline': 'svd',
        'width': test_params['width'],
        'height': test_params['height'],
        'numFrames': test_params['num_frames'],
        'decodeChunkSize': 4
    })
    print(f"\nEstimated VRAM usage: {estimated:.2f}GB")

    # Optimize if needed
    optimized = pipeline.optimize_params_for_vram({
        'pipeline': 'svd',
        'width': test_params['width'],
        'height': test_params['height'],
        'numFrames': test_params['num_frames'],
        'decodeChunkSize': 4
    })

    print("\nPipeline ready for generation!")
    print("Call pipeline.generate(**params) to generate video frames")
