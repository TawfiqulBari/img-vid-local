#!/usr/bin/env python3
"""
Video Generation Test Script

Tests both SVD and AnimateDiff pipelines with sample images and prompts.
Validates the complete generation workflow.

Usage:
    python backend/test_generation.py
    python backend/test_generation.py --quick  # Quick test with minimal frames
    python backend/test_generation.py --svd-only  # Test only SVD
    python backend/test_generation.py --animatediff-only  # Test only AnimateDiff
"""

import sys
import argparse
from pathlib import Path
import time

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.video_service import VideoService
from PIL import Image
import numpy as np


def create_test_image(width: int = 512, height: int = 512) -> str:
    """
    Create a test image for generation

    Args:
        width: Image width
        height: Image height

    Returns:
        Path to created image
    """
    # Create a gradient test image
    img = Image.new('RGB', (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            # Create colorful gradient
            r = int(255 * (x / width))
            g = int(255 * (y / height))
            b = int(128 + 127 * np.sin(x / 50))
            pixels[x, y] = (r, g, b)

    # Save to temp directory
    test_image_path = "/tmp/test_image.jpg"
    img.save(test_image_path)
    print(f"📷 Created test image: {test_image_path}")
    return test_image_path


def test_svd_pipeline(service: VideoService, image_path: str, quick: bool = False) -> None:
    """
    Test SVD pipeline

    Args:
        service: Video service instance
        image_path: Path to test image
        quick: Quick test with minimal frames
    """
    print("\n" + "=" * 70)
    print("TEST 1: Stable Video Diffusion (SVD-XT)")
    print("=" * 70 + "\n")

    params = {
        'image_path': image_path,
        'prompt': 'slow cinematic zoom in, smooth camera movement, dramatic lighting',
        'model_name': 'svd-xt',
        'num_frames': 14 if quick else 25,
        'fps': 8,
        'motion_bucket_id': 127,
        'width': 1024,
        'height': 576,
        'seed': 42
    }

    print("Test Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")

    print("\nStarting generation...")
    start = time.time()

    result = service.generate_video(**params)

    elapsed = time.time() - start

    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)

    if result.success:
        print(f"✅ SUCCESS")
        print(f"   Output: {result.output_path}")
        print(f"   Frames: {result.num_frames}")
        print(f"   Duration: {result.duration:.2f}s @ {result.fps} FPS")
        print(f"   Resolution: {result.resolution[0]}x{result.resolution[1]}")
        print(f"   Generation Time: {elapsed:.1f}s")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.error}")


def test_animatediff_pipeline(service: VideoService, image_path: str, quick: bool = False) -> None:
    """
    Test AnimateDiff pipeline

    Args:
        service: Video service instance
        image_path: Path to test image
        quick: Quick test with minimal frames
    """
    print("\n" + "=" * 70)
    print("TEST 2: AnimateDiff with Realistic Vision")
    print("=" * 70 + "\n")

    params = {
        'image_path': image_path,
        'prompt': 'slow cinematic pan, person turning head, wind blowing, golden hour lighting, masterpiece, highly detailed',
        'negative_prompt': 'blurry, distorted, low quality, static, ugly, deformed, bad anatomy',
        'model_name': 'animatediff-realisticVision_v51',
        'num_frames': 16 if quick else 24,
        'fps': 16,
        'guidance_scale': 7.5,
        'num_inference_steps': 20 if quick else 25,
        'width': 512,
        'height': 512,
        'seed': 42
    }

    print("Test Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")

    print("\nStarting generation...")
    start = time.time()

    result = service.generate_video(**params)

    elapsed = time.time() - start

    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)

    if result.success:
        print(f"✅ SUCCESS")
        print(f"   Output: {result.output_path}")
        print(f"   Frames: {result.num_frames}")
        print(f"   Duration: {result.duration:.2f}s @ {result.fps} FPS")
        print(f"   Resolution: {result.resolution[0]}x{result.resolution[1]}")
        print(f"   Generation Time: {elapsed:.1f}s")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.error}")


def test_model_discovery(service: VideoService) -> None:
    """
    Test model discovery

    Args:
        service: Video service instance
    """
    print("\n" + "=" * 70)
    print("MODEL DISCOVERY")
    print("=" * 70 + "\n")

    models = service.list_models()

    if not models:
        print("⚠️  No models found!")
        print("   Run: python backend/download_models.py")
        return

    print(f"Found {len(models)} model(s):\n")

    for model in models:
        print(f"📦 {model['name']}")
        print(f"   Type: {model['type']}")
        print(f"   Description: {model['description']}")
        print(f"   Path: {model['path']}")
        print(f"   Size: {model['size_mb']:.0f} MB\n")


def test_vram_monitoring(service: VideoService) -> None:
    """
    Test VRAM monitoring

    Args:
        service: Video service instance
    """
    print("\n" + "=" * 70)
    print("VRAM MONITORING")
    print("=" * 70 + "\n")

    stats = service.get_vram_stats()

    print("VRAM Statistics:")
    print(f"  Total: {stats['total_gb']:.2f} GB")
    print(f"  Used: {stats['used_gb']:.2f} GB")
    print(f"  Available: {stats['available_gb']:.2f} GB")
    print(f"  Usage: {stats['percent_used']:.1f}%")


def main() -> int:
    """
    Main test entry point

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(description="Test video generation pipelines")
    parser.add_argument('--quick', action='store_true', help='Quick test with minimal frames')
    parser.add_argument('--svd-only', action='store_true', help='Test only SVD pipeline')
    parser.add_argument('--animatediff-only', action='store_true', help='Test only AnimateDiff pipeline')
    parser.add_argument('--no-test-image', help='Use existing image instead of creating test image')

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("VIDEO GENERATION TEST SUITE")
    print("=" * 70)

    # Initialize service
    print("\n🚀 Initializing video service...")
    service = VideoService(
        models_dir="/mnt/d/VideoGenerator/models",
        output_dir="/mnt/d/VideoGenerator/output",
        device="cuda"
    )

    # Test model discovery
    test_model_discovery(service)

    # Test VRAM monitoring
    test_vram_monitoring(service)

    # Create or use test image
    if args.no_test_image:
        image_path = args.no_test_image
        print(f"\n📷 Using provided image: {image_path}")
    else:
        print("\n📷 Creating test image...")
        image_path = create_test_image(512, 512)

    # Run tests
    try:
        if not args.animatediff_only:
            test_svd_pipeline(service, image_path, quick=args.quick)

        if not args.svd_only:
            test_animatediff_pipeline(service, image_path, quick=args.quick)

        # Final summary
        print("\n" + "=" * 70)
        print("TEST SUITE COMPLETE")
        print("=" * 70)

        print("\n✅ All tests completed!")
        print("\nGenerated videos saved to: /mnt/d/VideoGenerator/output/")
        print("   (Windows path: D:\\VideoGenerator\\output\\)\n")

        print("Next steps:")
        print("  1. Check generated videos in output directory")
        print("  2. Proceed to C# WPF frontend development (Phase 4)")
        print("  3. Integrate with generate.py CLI interface\n")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
        return 1

    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        print("\n🗑️  Cleaning up...")
        service.unload_all_models()


if __name__ == '__main__':
    sys.exit(main())
