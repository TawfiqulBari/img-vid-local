"""
Video Generation Service

High-level API for image-to-video generation.

Provides:
- Simple generate_video() interface
- Automatic model loading and management
- Video export to MP4
- Progress tracking
- Error handling
- Generation metadata

Usage:
    service = VideoService()
    result = service.generate_video(
        image_path="input.jpg",
        prompt="slow zoom in, dramatic lighting",
        model_name="svd-xt",
        output_path="output.mp4"
    )
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from PIL import Image
import time
import json

from services.model_manager import ModelManager
from pipelines.base_pipeline import BasePipeline, PipelineError, VRAMError
from utils.path_utils import ensure_path_exists, normalize_path
from utils.prompt_utils import validate_and_prepare_prompts


class GenerationResult:
    """Result of video generation"""

    def __init__(
        self,
        success: bool,
        output_path: Optional[str] = None,
        num_frames: int = 0,
        duration: float = 0.0,
        fps: int = 0,
        resolution: tuple = (0, 0),
        model_name: str = "",
        generation_time: float = 0.0,
        error: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize generation result

        Args:
            success: Whether generation succeeded
            output_path: Path to output video
            num_frames: Number of frames generated
            duration: Video duration in seconds
            fps: Frames per second
            resolution: Video resolution (width, height)
            model_name: Model used
            generation_time: Time taken in seconds
            error: Error message if failed
            metadata: Additional metadata
        """
        self.success = success
        self.output_path = output_path
        self.num_frames = num_frames
        self.duration = duration
        self.fps = fps
        self.resolution = resolution
        self.model_name = model_name
        self.generation_time = generation_time
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'output_path': self.output_path,
            'num_frames': self.num_frames,
            'duration': self.duration,
            'fps': self.fps,
            'resolution': self.resolution,
            'model_name': self.model_name,
            'generation_time': self.generation_time,
            'error': self.error,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class VideoService:
    """High-level video generation service"""

    def __init__(
        self,
        models_dir: str = "/mnt/d/VideoGenerator/models",
        output_dir: str = "/mnt/d/VideoGenerator/output",
        device: str = "cuda"
    ):
        """
        Initialize video service

        Args:
            models_dir: Directory containing models
            output_dir: Directory for output videos
            device: Device to use (cuda or cpu)
        """
        self.models_dir = models_dir
        self.output_dir = Path(output_dir)
        self.device = device

        # Ensure output directory exists
        ensure_path_exists(self.output_dir, is_file=False)

        # Initialize model manager
        self.model_manager = ModelManager(
            models_dir=models_dir,
            device=device,
            enable_caching=True
        )

        # Progress callback
        self.progress_callback: Optional[Callable] = None

    def generate_video(
        self,
        image_path: str,
        prompt: str,
        model_name: str = "svd-xt",
        output_path: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        seed: int = -1,
        **kwargs
    ) -> GenerationResult:
        """
        Generate video from image with text prompt

        Args:
            image_path: Path to input image
            prompt: Text prompt (REQUIRED)
            model_name: Model to use (default: "svd-xt")
            output_path: Output video path (optional, auto-generated if None)
            negative_prompt: Negative prompt (optional)
            num_frames: Number of frames (optional, uses model default)
            fps: Frames per second (optional, uses model default)
            width: Output width (optional, uses model default)
            height: Output height (optional, uses model default)
            seed: Random seed (-1 for random)
            **kwargs: Additional generation parameters

        Returns:
            GenerationResult with success status and metadata

        Example:
            result = service.generate_video(
                image_path="input.jpg",
                prompt="slow zoom in, cinematic lighting",
                model_name="svd-xt",
                num_frames=25,
                fps=8
            )

            if result.success:
                print(f"Video saved to: {result.output_path}")
            else:
                print(f"Error: {result.error}")
        """
        start_time = time.time()

        try:
            # Validate inputs
            if not Path(image_path).exists():
                return GenerationResult(
                    success=False,
                    error=f"Image file not found: {image_path}"
                )

            if not prompt or not prompt.strip():
                return GenerationResult(
                    success=False,
                    error="Prompt is required and cannot be empty"
                )

            # Load pipeline
            print(f"\n{'=' * 70}")
            print(f"VIDEO GENERATION")
            print(f"{'=' * 70}\n")

            pipeline = self.model_manager.load_pipeline(model_name)

            # Get default parameters
            defaults = pipeline.get_default_params()

            # Merge with provided parameters
            gen_params = {
                'image_path': image_path,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'num_frames': num_frames or defaults.get('num_frames'),
                'fps': fps or defaults.get('fps'),
                'width': width or defaults.get('width'),
                'height': height or defaults.get('height'),
                'seed': seed,
                **kwargs
            }

            # Optimize for VRAM if needed
            vram_params = {
                'pipeline': pipeline.get_pipeline_type(),
                'width': gen_params['width'],
                'height': gen_params['height'],
                'numFrames': gen_params['num_frames'],
                'decodeChunkSize': gen_params.get('decode_chunk_size', 4)
            }
            optimized_params = pipeline.optimize_params_for_vram(vram_params)

            # Update generation params with optimized values
            if 'width' in optimized_params:
                gen_params['width'] = optimized_params['width']
            if 'height' in optimized_params:
                gen_params['height'] = optimized_params['height']
            if 'numFrames' in optimized_params:
                gen_params['num_frames'] = optimized_params['numFrames']
            if 'decodeChunkSize' in optimized_params:
                gen_params['decode_chunk_size'] = optimized_params['decodeChunkSize']

            # Set progress callback
            if self.progress_callback:
                pipeline.set_progress_callback(self.progress_callback)

            # Generate frames
            print(f"\n🎬 Starting generation...\n")
            frames = pipeline.generate(**gen_params)

            # Generate output path if not provided
            if output_path is None:
                timestamp = int(time.time())
                output_path = self.output_dir / f"video_{timestamp}.mp4"
            else:
                output_path = Path(output_path)
                # Ensure parent directory exists
                ensure_path_exists(output_path.parent, is_file=False)

            # Export to video
            print(f"\n💾 Exporting video to: {output_path}")
            self._export_video(
                frames=frames,
                output_path=str(output_path),
                fps=gen_params['fps']
            )

            # Calculate stats
            generation_time = time.time() - start_time
            duration = len(frames) / gen_params['fps']
            resolution = (gen_params['width'], gen_params['height'])

            print(f"\n✅ Video generation complete!")
            print(f"   Output: {output_path}")
            print(f"   Frames: {len(frames)}")
            print(f"   Duration: {duration:.2f}s @ {gen_params['fps']} FPS")
            print(f"   Resolution: {resolution[0]}x{resolution[1]}")
            print(f"   Time: {generation_time:.1f}s\n")

            return GenerationResult(
                success=True,
                output_path=str(output_path),
                num_frames=len(frames),
                duration=duration,
                fps=gen_params['fps'],
                resolution=resolution,
                model_name=model_name,
                generation_time=generation_time,
                metadata={
                    'prompt': prompt,
                    'negative_prompt': gen_params.get('negative_prompt'),
                    'seed': gen_params['seed'],
                    'parameters': gen_params
                }
            )

        except VRAMError as e:
            return GenerationResult(
                success=False,
                error=f"VRAM Error: {str(e)}",
                generation_time=time.time() - start_time
            )

        except PipelineError as e:
            return GenerationResult(
                success=False,
                error=f"Pipeline Error: {str(e)}",
                generation_time=time.time() - start_time
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=f"Unexpected Error: {str(e)}",
                generation_time=time.time() - start_time
            )

    def _export_video(
        self,
        frames: List[Image.Image],
        output_path: str,
        fps: int
    ) -> None:
        """
        Export frames to MP4 video

        Args:
            frames: List of PIL Image frames
            output_path: Output video path
            fps: Frames per second
        """
        if not frames:
            raise ValueError("No frames to export")

        # Get frame dimensions
        width, height = frames[0].size

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Write frames
        for i, frame in enumerate(frames):
            # Convert PIL Image to OpenCV format (RGB -> BGR)
            frame_np = np.array(frame)
            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
            writer.write(frame_bgr)

        writer.release()

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models

        Returns:
            List of model info dictionaries
        """
        return self.model_manager.list_models()

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model

        Args:
            model_name: Model name

        Returns:
            Model info dictionary or None
        """
        info = self.model_manager.get_model_info(model_name)
        return info.to_dict() if info else None

    def get_vram_stats(self) -> Dict[str, float]:
        """
        Get current VRAM statistics

        Returns:
            Dictionary with VRAM stats
        """
        return self.model_manager.get_vram_stats()

    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        Set progress callback function

        Args:
            callback: Function with signature (current_step, total_steps, message)
        """
        self.progress_callback = callback

    def unload_all_models(self) -> None:
        """Unload all models and free VRAM"""
        self.model_manager.unload_all()


# Example usage
if __name__ == "__main__":
    print("Video Service Test\n")

    # Initialize service
    service = VideoService(
        models_dir="/mnt/d/VideoGenerator/models",
        output_dir="/mnt/d/VideoGenerator/output",
        device="cuda"
    )

    # List available models
    print("Available models:")
    for model in service.list_models():
        print(f"  - {model['name']} ({model['type']})")

    # VRAM stats
    print("\nVRAM Status:")
    stats = service.get_vram_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nVideo service ready!")
    print("Use service.generate_video(...) to generate videos")
