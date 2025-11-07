"""
Model Manager Service

Manages multiple AI models and pipelines for video generation.

Features:
- Model discovery and listing
- Pipeline caching (avoid reloading)
- Automatic model type detection
- Memory management (unload unused models)
- Custom model support from CivitAI
- Path handling for WSL/Windows

Supported Models:
- SVD-XT (Stable Video Diffusion)
- AnimateDiff + SD 1.5 base models
- Custom .safetensors models
"""

import torch
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from pipelines.svd_pipeline import SVDPipeline
from pipelines.animatediff_pipeline import AnimateDiffPipeline
from pipelines.base_pipeline import BasePipeline, ModelLoadError
from utils.path_utils import normalize_path, validate_path_exists
from utils.vram_utils import VRAMMonitor


class ModelInfo:
    """Information about a discovered model"""

    def __init__(
        self,
        name: str,
        path: Path,
        model_type: str,
        description: str = "",
        size_mb: float = 0.0,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize model info

        Args:
            name: Model name
            path: Path to model
            model_type: Type ("svd", "animatediff", "sd15")
            description: Human-readable description
            size_mb: Model size in MB
            metadata: Additional metadata
        """
        self.name = name
        self.path = path
        self.model_type = model_type
        self.description = description
        self.size_mb = size_mb
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'path': str(self.path),
            'type': self.model_type,
            'description': self.description,
            'size_mb': self.size_mb,
            'metadata': self.metadata
        }


class ModelManager:
    """Manages AI models and pipelines"""

    def __init__(
        self,
        models_dir: str = "/mnt/d/VideoGenerator/models",
        device: str = "cuda",
        enable_caching: bool = True
    ):
        """
        Initialize model manager

        Args:
            models_dir: Base directory for models
            device: Device to use (cuda or cpu)
            enable_caching: Enable pipeline caching
        """
        self.models_dir = Path(models_dir)
        self.device = device
        self.enable_caching = enable_caching

        # Pipeline cache: {model_name: pipeline}
        self.pipeline_cache: Dict[str, BasePipeline] = {}

        # Current active pipeline
        self.current_pipeline: Optional[BasePipeline] = None
        self.current_model_name: Optional[str] = None

        # Discovered models
        self.available_models: Dict[str, ModelInfo] = {}

        # VRAM monitor
        self.vram_monitor = VRAMMonitor(device=device)

        # Discover models
        self._discover_models()

    def _discover_models(self) -> None:
        """Discover available models in models directory"""
        print(f"🔍 Discovering models in: {self.models_dir}\n")

        if not self.models_dir.exists():
            print(f"⚠️  Models directory not found: {self.models_dir}")
            print(f"   Run download_models.py to download models\n")
            return

        # Look for SVD model
        svd_path = self.models_dir / "svd-xt"
        if svd_path.exists() and svd_path.is_dir():
            size_mb = self._get_directory_size(svd_path)
            self.available_models['svd-xt'] = ModelInfo(
                name='svd-xt',
                path=svd_path,
                model_type='svd',
                description='Stable Video Diffusion XT - Fast image-to-video',
                size_mb=size_mb,
                metadata={'resolution': '1024x576', 'max_frames': 60}
            )
            print(f"  ✅ Found SVD-XT model ({size_mb:.0f} MB)")

        # Look for AnimateDiff motion adapter
        animatediff_path = self.models_dir / "animatediff"
        if animatediff_path.exists() and animatediff_path.is_dir():
            size_mb = self._get_directory_size(animatediff_path)
            print(f"  ✅ Found AnimateDiff motion adapter ({size_mb:.0f} MB)")

            # Look for SD 1.5 base models in realistic-vision directory
            realistic_vision_dir = self.models_dir / "realistic-vision"
            if realistic_vision_dir.exists():
                for model_file in realistic_vision_dir.glob("*.safetensors"):
                    model_name = f"animatediff-{model_file.stem}"
                    size_mb = model_file.stat().st_size / (1024 * 1024)

                    self.available_models[model_name] = ModelInfo(
                        name=model_name,
                        path=model_file,
                        model_type='animatediff',
                        description=f'AnimateDiff with {model_file.stem}',
                        size_mb=size_mb,
                        metadata={
                            'base_model': model_file.stem,
                            'motion_adapter': str(animatediff_path),
                            'resolution': '512x512',
                            'max_frames': 64
                        }
                    )
                    print(f"  ✅ Found AnimateDiff model: {model_file.name} ({size_mb:.0f} MB)")

        # Look for other custom models
        custom_dirs = [d for d in self.models_dir.iterdir() if d.is_dir() and d.name not in ['svd-xt', 'animatediff', 'realistic-vision']]
        for custom_dir in custom_dirs:
            for model_file in custom_dir.glob("*.safetensors"):
                model_name = f"custom-{model_file.stem}"
                size_mb = model_file.stat().st_size / (1024 * 1024)

                # Check if AnimateDiff adapter exists
                if animatediff_path.exists():
                    self.available_models[model_name] = ModelInfo(
                        name=model_name,
                        path=model_file,
                        model_type='animatediff',
                        description=f'Custom model: {model_file.stem}',
                        size_mb=size_mb,
                        metadata={
                            'base_model': model_file.stem,
                            'motion_adapter': str(animatediff_path),
                            'source': 'custom'
                        }
                    )
                    print(f"  ✅ Found custom model: {model_file.name} ({size_mb:.0f} MB)")

        if not self.available_models:
            print("  ⚠️  No models found")
            print("  Run download_models.py to download models\n")
        else:
            print(f"\n📦 Total models discovered: {len(self.available_models)}\n")

    def _get_directory_size(self, directory: Path) -> float:
        """
        Get total size of directory in MB

        Args:
            directory: Directory path

        Returns:
            Size in MB
        """
        total_size = 0
        for file in directory.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size / (1024 * 1024)

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models

        Returns:
            List of model info dictionaries
        """
        return [model.to_dict() for model in self.available_models.values()]

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model

        Args:
            model_name: Model name

        Returns:
            ModelInfo or None if not found
        """
        return self.available_models.get(model_name)

    def load_pipeline(
        self,
        model_name: str,
        **kwargs
    ) -> BasePipeline:
        """
        Load pipeline for specified model

        Args:
            model_name: Model name
            **kwargs: Additional pipeline arguments

        Returns:
            Loaded pipeline

        Raises:
            ModelLoadError: If model not found or loading fails
        """
        # Check if model exists
        if model_name not in self.available_models:
            raise ModelLoadError(
                f"Model '{model_name}' not found. Available models: {list(self.available_models.keys())}"
            )

        # Check cache
        if self.enable_caching and model_name in self.pipeline_cache:
            print(f"📦 Using cached pipeline: {model_name}")
            pipeline = self.pipeline_cache[model_name]
            self.current_pipeline = pipeline
            self.current_model_name = model_name
            return pipeline

        # Unload current pipeline if different
        if self.current_pipeline and self.current_model_name != model_name:
            print(f"🗑️  Unloading current pipeline: {self.current_model_name}")
            self.current_pipeline.unload_model()

        # Load new pipeline
        model_info = self.available_models[model_name]
        print(f"📦 Loading pipeline: {model_name} ({model_info.model_type})")

        if model_info.model_type == 'svd':
            pipeline = self._load_svd_pipeline(model_info, **kwargs)
        elif model_info.model_type == 'animatediff':
            pipeline = self._load_animatediff_pipeline(model_info, **kwargs)
        else:
            raise ModelLoadError(f"Unsupported model type: {model_info.model_type}")

        # Load model
        pipeline.load_model()

        # Cache if enabled
        if self.enable_caching:
            self.pipeline_cache[model_name] = pipeline

        # Set as current
        self.current_pipeline = pipeline
        self.current_model_name = model_name

        return pipeline

    def _load_svd_pipeline(
        self,
        model_info: ModelInfo,
        **kwargs
    ) -> SVDPipeline:
        """
        Load SVD pipeline

        Args:
            model_info: Model information
            **kwargs: Additional pipeline arguments

        Returns:
            SVD pipeline
        """
        return SVDPipeline(
            model_path=str(model_info.path),
            device=self.device,
            **kwargs
        )

    def _load_animatediff_pipeline(
        self,
        model_info: ModelInfo,
        **kwargs
    ) -> AnimateDiffPipeline:
        """
        Load AnimateDiff pipeline

        Args:
            model_info: Model information
            **kwargs: Additional pipeline arguments

        Returns:
            AnimateDiff pipeline
        """
        motion_adapter_path = model_info.metadata.get('motion_adapter')
        if not motion_adapter_path:
            raise ModelLoadError("Motion adapter path not found in model metadata")

        return AnimateDiffPipeline(
            model_path=str(model_info.path),
            motion_adapter_path=motion_adapter_path,
            device=self.device,
            **kwargs
        )

    def get_current_pipeline(self) -> Optional[BasePipeline]:
        """
        Get currently loaded pipeline

        Returns:
            Current pipeline or None
        """
        return self.current_pipeline

    def unload_all(self) -> None:
        """Unload all pipelines and clear cache"""
        print("🗑️  Unloading all pipelines...")

        for model_name, pipeline in self.pipeline_cache.items():
            pipeline.unload_model()

        self.pipeline_cache.clear()
        self.current_pipeline = None
        self.current_model_name = None

        print("✅ All pipelines unloaded\n")

    def get_vram_stats(self) -> Dict[str, float]:
        """
        Get current VRAM statistics

        Returns:
            Dictionary with VRAM stats
        """
        return self.vram_monitor.get_vram_stats()


# Example usage
if __name__ == "__main__":
    print("Model Manager Test\n")

    # Initialize manager
    manager = ModelManager(
        models_dir="/mnt/d/VideoGenerator/models",
        device="cuda",
        enable_caching=True
    )

    # List models
    print("Available models:")
    for model in manager.list_models():
        print(f"  - {model['name']} ({model['type']}) - {model['description']}")
        print(f"    Path: {model['path']}")
        print(f"    Size: {model['size_mb']:.0f} MB\n")

    # VRAM stats
    stats = manager.get_vram_stats()
    print("\nVRAM Status:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nModel manager ready!")
    print("Use manager.load_pipeline('model_name') to load a pipeline")
