#!/usr/bin/env python3
"""
Video Generation CLI Entry Point

Command-line interface for image-to-video generation.
Called by C# frontend with JSON parameters.

Usage:
    python generate.py '{"image_path":"input.jpg","prompt":"slow zoom in",...}'

    python generate.py --help
    python generate.py --list-models
    python generate.py --vram-stats

Returns JSON response with generation results.
"""

import sys
import json
import argparse
from typing import Dict, Any
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.video_service import VideoService
from utils.path_utils import windows_to_wsl_path, wsl_to_windows_path


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Image-to-Video Generator - CLI Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate video with SVD
    python generate.py '{"image_path":"input.jpg","prompt":"slow zoom in","model_name":"svd-xt"}'

    # Generate with AnimateDiff and custom parameters
    python generate.py '{"image_path":"input.jpg","prompt":"woman turning head","model_name":"animatediff-realisticVision_v51","num_frames":24,"fps":16}'

    # List available models
    python generate.py --list-models

    # Check VRAM status
    python generate.py --vram-stats
        """
    )

    parser.add_argument(
        'params',
        nargs='?',
        help='JSON string with generation parameters'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available models and exit'
    )

    parser.add_argument(
        '--vram-stats',
        action='store_true',
        help='Show VRAM statistics and exit'
    )

    parser.add_argument(
        '--models-dir',
        default='/mnt/d/VideoGenerator/models',
        help='Models directory (default: /mnt/d/VideoGenerator/models)'
    )

    parser.add_argument(
        '--output-dir',
        default='/mnt/d/VideoGenerator/output',
        help='Output directory (default: /mnt/d/VideoGenerator/output)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def list_models(service: VideoService) -> None:
    """
    List available models and print as JSON

    Args:
        service: Video service instance
    """
    models = service.list_models()
    output = {
        'success': True,
        'models': models,
        'count': len(models)
    }
    print(json.dumps(output, indent=2))


def show_vram_stats(service: VideoService) -> None:
    """
    Show VRAM statistics and print as JSON

    Args:
        service: Video service instance
    """
    stats = service.get_vram_stats()
    output = {
        'success': True,
        'vram': stats
    }
    print(json.dumps(output, indent=2))


def validate_params(params: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate generation parameters

    Args:
        params: Parameters dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Required fields
    required = ['image_path', 'prompt']
    for field in required:
        if field not in params:
            return False, f"Missing required field: {field}"

    # Validate image path
    image_path = params['image_path']

    # Convert Windows path to WSL if needed
    if len(image_path) >= 2 and image_path[1] == ':':
        image_path = windows_to_wsl_path(image_path)
        params['image_path'] = image_path

    if not Path(image_path).exists():
        return False, f"Image file not found: {image_path}"

    # Validate prompt
    if not params['prompt'] or not params['prompt'].strip():
        return False, "Prompt cannot be empty"

    return True, ""


def generate_video(service: VideoService, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate video and return result as dictionary

    Args:
        service: Video service instance
        params: Generation parameters

    Returns:
        Result dictionary
    """
    # Validate parameters
    is_valid, error = validate_params(params)
    if not is_valid:
        return {
            'success': False,
            'error': error
        }

    # Extract parameters
    image_path = params['image_path']
    prompt = params['prompt']
    model_name = params.get('model_name', 'svd-xt')
    output_path = params.get('output_path')
    negative_prompt = params.get('negative_prompt')
    num_frames = params.get('num_frames')
    fps = params.get('fps')
    width = params.get('width')
    height = params.get('height')
    seed = params.get('seed', -1)

    # Additional parameters for specific pipelines
    kwargs = {}

    # SVD-specific
    if 'motion_bucket_id' in params:
        kwargs['motion_bucket_id'] = params['motion_bucket_id']
    if 'noise_aug_strength' in params:
        kwargs['noise_aug_strength'] = params['noise_aug_strength']
    if 'decode_chunk_size' in params:
        kwargs['decode_chunk_size'] = params['decode_chunk_size']

    # AnimateDiff-specific
    if 'guidance_scale' in params:
        kwargs['guidance_scale'] = params['guidance_scale']
    if 'num_inference_steps' in params:
        kwargs['num_inference_steps'] = params['num_inference_steps']
    if 'clip_skip' in params:
        kwargs['clip_skip'] = params['clip_skip']

    # Convert output path from Windows to WSL if needed
    if output_path and len(output_path) >= 2 and output_path[1] == ':':
        output_path = windows_to_wsl_path(output_path)

    # Generate video
    result = service.generate_video(
        image_path=image_path,
        prompt=prompt,
        model_name=model_name,
        output_path=output_path,
        negative_prompt=negative_prompt,
        num_frames=num_frames,
        fps=fps,
        width=width,
        height=height,
        seed=seed,
        **kwargs
    )

    # Convert result to dictionary
    result_dict = result.to_dict()

    # Convert output path back to Windows format for C# if needed
    if result.success and result.output_path:
        result_dict['output_path_wsl'] = result.output_path
        result_dict['output_path_windows'] = wsl_to_windows_path(result.output_path)

    return result_dict


def main() -> int:
    """
    Main entry point

    Returns:
        Exit code (0 for success, 1 for error)
    """
    args = parse_arguments()

    try:
        # Initialize video service
        service = VideoService(
            models_dir=args.models_dir,
            output_dir=args.output_dir,
            device='cuda'
        )

        # Handle special commands
        if args.list_models:
            list_models(service)
            return 0

        if args.vram_stats:
            show_vram_stats(service)
            return 0

        # Parse generation parameters
        if not args.params:
            print(json.dumps({
                'success': False,
                'error': 'No parameters provided. Use --help for usage information.'
            }))
            return 1

        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(json.dumps({
                'success': False,
                'error': f'Invalid JSON parameters: {str(e)}'
            }))
            return 1

        # Generate video
        result = generate_video(service, params)

        # Output result as JSON
        print(json.dumps(result, indent=2 if args.verbose else None))

        # Return exit code based on success
        return 0 if result['success'] else 1

    except KeyboardInterrupt:
        print(json.dumps({
            'success': False,
            'error': 'Generation cancelled by user'
        }))
        return 1

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }))
        return 1


if __name__ == '__main__':
    sys.exit(main())
