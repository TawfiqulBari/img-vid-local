"""
Base Pipeline for Image-to-Video Generation

Abstract base class defining the common interface and shared functionality
for all video generation pipelines (SVD and AnimateDiff).

Provides:
- Model loading and management
- VRAM optimization strategies
- Progress tracking and callbacks
- Error handling
- Common generation parameters
"""

import torch
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path
from PIL import Image
import gc

from utils.vram_utils import VRAMMonitor, VRAMOptimizer
from utils.prompt_utils import validate_and_prepare_prompts


class BasePipeline(ABC):
    """Abstract base class for video generation pipelines"""

    def __init__(
        self,
        model_path: str,
        device: str = "cuda",
        torch_dtype: torch.dtype = torch.float16,
        enable_xformers: bool = True,
        enable_cpu_offload: bool = True
    ):
        """
        Initialize base pipeline

        Args:
            model_path: Path to model directory
            device: Device to run on (default: "cuda")
            torch_dtype: PyTorch data type (default: float16)
            enable_xformers: Enable memory-efficient attention (default: True)
            enable_cpu_offload: Enable CPU offloading to reduce VRAM (default: True)
        """
        self.model_path = Path(model_path)
        self.device = device
        self.torch_dtype = torch_dtype
        self.enable_xformers = enable_xformers
        self.enable_cpu_offload = enable_cpu_offload

        # Pipeline instance (set by subclass)
        self.pipe = None

        # VRAM monitoring
        self.vram_monitor = VRAMMonitor(device=device)
        self.vram_optimizer = VRAMOptimizer()

        # Progress callback
        self.progress_callback: Optional[Callable] = None

        # Generation state
        self.is_loaded = False
        self.current_generation_id: Optional[str] = None

    @abstractmethod
    def load_model(self) -> None:
        """
        Load model into memory

        Must be implemented by subclass to load specific pipeline
        """
        pass

    @abstractmethod
    def generate(
        self,
        image_path: str,
        prompt: str,
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate video frames from input image

        Must be implemented by subclass

        Args:
            image_path: Path to input image
            prompt: Text prompt describing desired video
            **kwargs: Additional generation parameters

        Returns:
            List of PIL Image frames
        """
        pass

    @abstractmethod
    def get_default_params(self) -> Dict[str, Any]:
        """
        Get default generation parameters for this pipeline

        Must be implemented by subclass

        Returns:
            Dictionary of default parameters
        """
        pass

    def apply_optimizations(self) -> None:
        """
        Apply memory optimizations to pipeline

        Applies:
        1. Xformers (memory-efficient attention)
        2. CPU offloading
        3. VAE slicing
        4. VAE tiling
        """
        if self.pipe is None:
            raise RuntimeError("Pipeline not loaded. Call load_model() first.")

        print("🔧 Applying VRAM optimizations...")

        # 1. Enable xformers (30-40% VRAM reduction)
        if self.enable_xformers:
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
                print("  ✅ Xformers enabled (memory-efficient attention)")
            except Exception as e:
                print(f"  ⚠️  Xformers not available: {e}")

        # 2. CPU offloading (moves unused components to RAM)
        if self.enable_cpu_offload:
            try:
                self.pipe.enable_model_cpu_offload()
                print("  ✅ CPU offloading enabled")
            except Exception as e:
                print(f"  ⚠️  CPU offload failed: {e}")

        # 3. VAE slicing (processes VAE in slices)
        if hasattr(self.pipe, 'enable_vae_slicing'):
            try:
                self.pipe.enable_vae_slicing()
                print("  ✅ VAE slicing enabled")
            except Exception as e:
                print(f"  ⚠️  VAE slicing failed: {e}")

        # 4. VAE tiling (processes images in tiles)
        if hasattr(self.pipe, 'enable_vae_tiling'):
            try:
                self.pipe.enable_vae_tiling()
                print("  ✅ VAE tiling enabled")
            except Exception as e:
                print(f"  ⚠️  VAE tiling failed: {e}")

        # Report VRAM stats
        stats = self.vram_monitor.get_vram_stats()
        print(f"\n📊 VRAM Status:")
        print(f"  Total: {stats['total_gb']:.2f} GB")
        print(f"  Used: {stats['used_gb']:.2f} GB ({stats['percent_used']:.1f}%)")
        print(f"  Available: {stats['available_gb']:.2f} GB\n")

    def optimize_params_for_vram(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize generation parameters to fit within VRAM constraints

        Args:
            params: Original generation parameters

        Returns:
            Optimized parameters
        """
        optimized, message = self.vram_optimizer.optimize_params(params)
        print(f"🔍 {message}")
        return optimized

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate generation parameters

        Args:
            params: Generation parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if 'image_path' not in params:
            return False, "Missing required parameter: image_path"

        if 'prompt' not in params:
            return False, "Missing required parameter: prompt"

        # Validate prompt
        prompt = params['prompt']
        is_valid, error = validate_and_prepare_prompts(
            prompt=prompt,
            negative_prompt=params.get('negativePrompt'),
            pipeline=self.get_pipeline_type()
        )[:2]

        if not is_valid:
            return False, error

        # Validate image path
        image_path = Path(params['image_path'])
        if not image_path.exists():
            return False, f"Image file not found: {image_path}"

        if not image_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            return False, f"Unsupported image format: {image_path.suffix}"

        return True, None

    def load_and_preprocess_image(
        self,
        image_path: str,
        target_width: int,
        target_height: int
    ) -> Image.Image:
        """
        Load and preprocess input image

        Args:
            image_path: Path to input image
            target_width: Target width (must be divisible by 8)
            target_height: Target height (must be divisible by 8)

        Returns:
            Preprocessed PIL Image
        """
        # Load image
        image = Image.open(image_path).convert("RGB")

        print(f"📷 Input image: {image.size[0]}x{image.size[1]}")

        # Resize to target resolution
        if image.size != (target_width, target_height):
            # Use high-quality Lanczos resampling
            image = image.resize(
                (target_width, target_height),
                Image.LANCZOS
            )
            print(f"   Resized to: {target_width}x{target_height}")

        return image

    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        Set progress callback function

        Args:
            callback: Function with signature (current_step, total_steps, message)
        """
        self.progress_callback = callback

    def report_progress(self, current: int, total: int, message: str = "") -> None:
        """
        Report progress to callback if set

        Args:
            current: Current step
            total: Total steps
            message: Optional status message
        """
        if self.progress_callback:
            self.progress_callback(current, total, message)

    def clear_cache(self) -> None:
        """Clear PyTorch CUDA cache and run garbage collection"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    def get_vram_stats(self) -> Dict[str, float]:
        """
        Get current VRAM statistics

        Returns:
            Dictionary with VRAM stats (total_gb, used_gb, available_gb, percent_used)
        """
        return self.vram_monitor.get_vram_stats()

    def estimate_vram_usage(self, params: Dict[str, Any]) -> float:
        """
        Estimate VRAM usage for given parameters

        Args:
            params: Generation parameters

        Returns:
            Estimated VRAM usage in GB
        """
        return self.vram_optimizer.estimate_vram_usage(params)

    def unload_model(self) -> None:
        """Unload model from memory and free VRAM"""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
            self.is_loaded = False

        self.clear_cache()
        print("🗑️  Model unloaded, VRAM cleared")

    @abstractmethod
    def get_pipeline_type(self) -> str:
        """
        Get pipeline type identifier

        Must be implemented by subclass

        Returns:
            Pipeline type string ("svd" or "animatediff")
        """
        pass

    def get_recommended_settings(self) -> Dict[str, Any]:
        """
        Get recommended settings based on available VRAM

        Returns:
            Dictionary of recommended settings
        """
        return self.vram_optimizer.get_recommended_settings(
            pipeline=self.get_pipeline_type()
        )

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"{self.__class__.__name__}("
            f"model_path={self.model_path}, "
            f"device={self.device}, "
            f"loaded={self.is_loaded})"
        )


class PipelineError(Exception):
    """Custom exception for pipeline errors"""
    pass


class VRAMError(Exception):
    """Custom exception for VRAM-related errors"""
    pass


class ModelLoadError(Exception):
    """Custom exception for model loading errors"""
    pass
