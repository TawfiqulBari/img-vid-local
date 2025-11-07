"""
VRAM Management Utilities for RTX 3060 (12GB VRAM)

Provides VRAM monitoring, estimation, and dynamic optimization
to ensure video generation stays within hardware constraints.
"""

import torch
from typing import Dict, Any, Optional, Tuple


class VRAMMonitor:
    """Monitor and manage GPU VRAM usage"""

    def __init__(self, device: str = "cuda", target_vram_gb: float = 11.0):
        """
        Initialize VRAM monitor

        Args:
            device: CUDA device (default: "cuda")
            target_vram_gb: Target maximum VRAM usage in GB (default: 11.0, leaving 1GB headroom)
        """
        self.device = device
        self.target_vram = target_vram_gb
        self.total_vram = self._get_total_vram()

    def _get_total_vram(self) -> float:
        """
        Get total VRAM available on GPU

        Returns:
            Total VRAM in GB
        """
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        return 0.0

    def get_available_vram(self) -> float:
        """
        Get currently available VRAM

        Returns:
            Available VRAM in GB
        """
        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            return free / (1024 ** 3)
        return 0.0

    def get_used_vram(self) -> float:
        """
        Get currently used VRAM

        Returns:
            Used VRAM in GB
        """
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024 ** 3)
            return allocated
        return 0.0

    def get_vram_stats(self) -> Dict[str, float]:
        """
        Get comprehensive VRAM statistics

        Returns:
            Dictionary with total, used, available, and percentage used
        """
        if torch.cuda.is_available():
            total = self.total_vram
            used = self.get_used_vram()
            available = self.get_available_vram()
            percent_used = (used / total * 100) if total > 0 else 0

            return {
                "total_gb": round(total, 2),
                "used_gb": round(used, 2),
                "available_gb": round(available, 2),
                "percent_used": round(percent_used, 1)
            }
        return {
            "total_gb": 0.0,
            "used_gb": 0.0,
            "available_gb": 0.0,
            "percent_used": 0.0
        }

    def clear_cache(self):
        """Clear PyTorch CUDA cache"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def is_vram_available(self, required_gb: float) -> bool:
        """
        Check if required VRAM is available

        Args:
            required_gb: Required VRAM in GB

        Returns:
            True if enough VRAM available, False otherwise
        """
        available = self.get_available_vram()
        return available >= required_gb


class VRAMOptimizer:
    """Optimize generation parameters based on available VRAM"""

    # VRAM estimates based on testing (RTX 3060 12GB)
    VRAM_ESTIMATES = {
        "svd": {
            "base_model": 6.0,  # SVD model loaded
            "overhead": 1.5      # System overhead
        },
        "animatediff": {
            "base_model": 5.0,  # SD 1.5 + motion adapter
            "overhead": 1.5      # System overhead
        }
    }

    def __init__(self, target_vram_gb: float = 11.0):
        """
        Initialize VRAM optimizer

        Args:
            target_vram_gb: Target maximum VRAM usage
        """
        self.target_vram = target_vram_gb
        self.monitor = VRAMMonitor(target_vram_gb=target_vram_gb)

    def estimate_vram_usage(self, params: Dict[str, Any]) -> float:
        """
        Estimate VRAM usage for given generation parameters

        Args:
            params: Generation parameters dictionary

        Returns:
            Estimated VRAM usage in GB
        """
        pipeline = params.get('pipeline', 'svd')
        width = params.get('width', 512)
        height = params.get('height', 512)
        num_frames = params.get('numFrames', 25)
        decode_chunk_size = params.get('decodeChunkSize', 4)

        # Get base estimates
        estimates = self.VRAM_ESTIMATES.get(pipeline, self.VRAM_ESTIMATES['svd'])
        base = estimates['base_model']
        overhead = estimates['overhead']

        # Calculate frame buffer memory
        # Formula: (width * height * num_frames * bytes_per_pixel) / (1024^3) / decode_chunk_size
        # bytes_per_pixel = 4 (float32)
        frame_buffer = (width * height * num_frames * 4) / (1024 ** 3)
        frame_buffer /= decode_chunk_size  # Chunked decoding reduces memory

        total = base + frame_buffer + overhead
        return round(total, 2)

    def optimize_params(self, params: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Optimize parameters to fit within VRAM constraints

        Args:
            params: Original generation parameters

        Returns:
            Tuple of (optimized_params, optimization_message)
        """
        estimated = self.estimate_vram_usage(params)
        available = self.monitor.get_available_vram()

        optimized = params.copy()
        optimizations = []

        if estimated > available or estimated > self.target_vram:
            # Strategy 1: Reduce decode_chunk_size
            if optimized.get('decodeChunkSize', 4) > 2:
                old_val = optimized.get('decodeChunkSize', 4)
                optimized['decodeChunkSize'] = 2
                optimizations.append(f"Reduced decode_chunk_size from {old_val} to 2")

                # Re-estimate
                estimated = self.estimate_vram_usage(optimized)

            # Strategy 2: Reduce num_frames
            if estimated > available or estimated > self.target_vram:
                old_frames = optimized.get('numFrames', 25)
                max_frames = int(old_frames * (available / estimated) * 0.9)  # 90% safety margin
                max_frames = max(16, min(max_frames, old_frames))  # At least 16 frames

                if max_frames < old_frames:
                    optimized['numFrames'] = max_frames
                    optimizations.append(f"Reduced num_frames from {old_frames} to {max_frames}")

                    # Re-estimate
                    estimated = self.estimate_vram_usage(optimized)

            # Strategy 3: Reduce resolution (last resort)
            if estimated > available or estimated > self.target_vram:
                width = optimized.get('width', 512)
                height = optimized.get('height', 512)

                if width > 512 or height > 512:
                    optimized['width'] = 512
                    optimized['height'] = 512
                    optimizations.append(f"Reduced resolution from {width}x{height} to 512x512")

        if optimizations:
            message = "VRAM optimizations applied: " + "; ".join(optimizations)
        else:
            message = f"Parameters within VRAM budget ({estimated:.2f}GB / {available:.2f}GB available)"

        return optimized, message

    def get_max_frames(
        self,
        pipeline: str = "svd",
        width: int = 512,
        height: int = 512,
        decode_chunk_size: int = 4
    ) -> int:
        """
        Calculate maximum frames for given parameters

        Args:
            pipeline: Pipeline type ("svd" or "animatediff")
            width: Frame width
            height: Frame height
            decode_chunk_size: Decode chunk size

        Returns:
            Maximum number of frames possible
        """
        available = self.monitor.get_available_vram()

        estimates = self.VRAM_ESTIMATES.get(pipeline, self.VRAM_ESTIMATES['svd'])
        base = estimates['base_model']
        overhead = estimates['overhead']

        # Available for frames
        available_for_frames = available - base - overhead

        # Calculate max frames
        # frame_buffer = (width * height * num_frames * 4) / (1024^3) / decode_chunk_size
        # Solve for num_frames
        bytes_per_frame = (width * height * 4) / (1024 ** 3) / decode_chunk_size
        max_frames = int(available_for_frames / bytes_per_frame)

        # Apply safety margin
        max_frames = int(max_frames * 0.9)

        # Reasonable bounds
        max_frames = max(16, min(max_frames, 250))

        return max_frames

    def get_recommended_settings(self, pipeline: str = "svd") -> Dict[str, Any]:
        """
        Get recommended settings for given pipeline based on available VRAM

        Args:
            pipeline: Pipeline type

        Returns:
            Dictionary of recommended settings
        """
        available = self.monitor.get_available_vram()

        if pipeline == "svd":
            if available >= 10.0:
                return {
                    "width": 1024,
                    "height": 576,
                    "numFrames": 60,
                    "decodeChunkSize": 4,
                    "numInferenceSteps": 40,
                    "description": "High quality (16:9)"
                }
            elif available >= 8.0:
                return {
                    "width": 768,
                    "height": 768,
                    "numFrames": 50,
                    "decodeChunkSize": 4,
                    "numInferenceSteps": 30,
                    "description": "Medium quality"
                }
            else:
                return {
                    "width": 512,
                    "height": 512,
                    "numFrames": 25,
                    "decodeChunkSize": 2,
                    "numInferenceSteps": 25,
                    "description": "Low quality (safe)"
                }

        else:  # animatediff
            if available >= 10.0:
                return {
                    "width": 512,
                    "height": 512,
                    "numFrames": 64,
                    "numInferenceSteps": 30,
                    "description": "High quality"
                }
            elif available >= 8.0:
                return {
                    "width": 512,
                    "height": 512,
                    "numFrames": 48,
                    "numInferenceSteps": 25,
                    "description": "Medium quality"
                }
            else:
                return {
                    "width": 512,
                    "height": 512,
                    "numFrames": 24,
                    "numInferenceSteps": 20,
                    "description": "Low quality (safe)"
                }


# Example usage and testing
if __name__ == "__main__":
    print("VRAM Utilities Test\n")

    # Create monitor
    monitor = VRAMMonitor()
    print("VRAM Statistics:")
    stats = monitor.get_vram_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 50 + "\n")

    # Create optimizer
    optimizer = VRAMOptimizer()

    # Test parameters
    test_params = {
        "pipeline": "svd",
        "width": 1024,
        "height": 576,
        "numFrames": 100,
        "decodeChunkSize": 8,
        "numInferenceSteps": 40
    }

    print("Original Parameters:")
    for key, value in test_params.items():
        print(f"  {key}: {value}")

    estimated = optimizer.estimate_vram_usage(test_params)
    print(f"\nEstimated VRAM: {estimated:.2f} GB")

    # Optimize
    optimized, message = optimizer.optimize_params(test_params)
    print(f"\n{message}")

    print("\nOptimized Parameters:")
    for key, value in optimized.items():
        if key in test_params and test_params[key] != value:
            print(f"  {key}: {test_params[key]} → {value} ⚠️")
        else:
            print(f"  {key}: {value}")

    estimated_opt = optimizer.estimate_vram_usage(optimized)
    print(f"\nEstimated VRAM (optimized): {estimated_opt:.2f} GB")

    # Max frames
    print("\n" + "=" * 50 + "\n")
    max_frames_svd = optimizer.get_max_frames("svd", 512, 512, 4)
    max_frames_ad = optimizer.get_max_frames("animatediff", 512, 512, 4)

    print(f"Maximum frames (512x512, chunk_size=4):")
    print(f"  SVD: {max_frames_svd} frames")
    print(f"  AnimateDiff: {max_frames_ad} frames")

    # Recommended settings
    print("\n" + "=" * 50 + "\n")
    print("Recommended settings (SVD):")
    rec_svd = optimizer.get_recommended_settings("svd")
    for key, value in rec_svd.items():
        print(f"  {key}: {value}")

    print("\nRecommended settings (AnimateDiff):")
    rec_ad = optimizer.get_recommended_settings("animatediff")
    for key, value in rec_ad.items():
        print(f"  {key}: {value}")
