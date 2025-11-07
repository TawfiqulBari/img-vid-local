#!/usr/bin/env python3
"""
Model Download Script for Image-to-Video Generator

Downloads required AI models to D:\\VideoGenerator\\models\\:
1. SVD-XT (Stable Video Diffusion) - ~10GB
2. AnimateDiff Motion Adapter - ~3GB
3. Realistic Vision v5.1 (SD 1.5 base) - ~2GB

Total download: ~15GB

Usage:
    python backend/download_models.py
    python backend/download_models.py --models svd  # Download only SVD
    python backend/download_models.py --output /custom/path  # Custom output location
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from tqdm import tqdm
from huggingface_hub import snapshot_download, hf_hub_download
from typing import Optional


class ModelDownloader:
    """Handles downloading AI models with progress tracking and resume capability"""

    def __init__(self, base_path: str = "/mnt/d/VideoGenerator/models"):
        """
        Initialize downloader

        Args:
            base_path: Base directory for model storage (default: D:\\VideoGenerator\\models)
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        print(f"📦 Models will be downloaded to: {self.base_path}")
        print(f"   (Windows path: {self.wsl_to_windows_path(str(self.base_path))})\n")

    @staticmethod
    def wsl_to_windows_path(wsl_path: str) -> str:
        """Convert WSL path to Windows path for display"""
        if wsl_path.startswith('/mnt/'):
            parts = wsl_path[5:].split('/', 1)
            if len(parts) >= 1:
                drive = parts[0].upper()
                rest = parts[1] if len(parts) > 1 else ''
                return f"{drive}:\\{rest.replace('/', '\\')}"
        return wsl_path

    def check_disk_space(self, required_gb: float = 20) -> bool:
        """
        Check if enough disk space is available

        Args:
            required_gb: Required space in GB

        Returns:
            True if enough space, False otherwise
        """
        try:
            stat = os.statvfs(self.base_path)
            available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

            print(f"💾 Disk Space Check:")
            print(f"   Available: {available_gb:.2f} GB")
            print(f"   Required:  {required_gb:.2f} GB")

            if available_gb < required_gb:
                print(f"   ❌ Insufficient space!")
                return False
            else:
                print(f"   ✅ Sufficient space\n")
                return True
        except Exception as e:
            print(f"   ⚠️  Could not check disk space: {e}\n")
            return True  # Continue anyway

    def download_from_huggingface(
        self,
        repo_id: str,
        local_dir: str,
        repo_type: str = "model",
        allow_patterns: Optional[list] = None,
        ignore_patterns: Optional[list] = None
    ) -> Path:
        """
        Download model from HuggingFace Hub

        Args:
            repo_id: HuggingFace repository ID (e.g., "stabilityai/stable-video-diffusion-img2vid-xt")
            local_dir: Local directory name (relative to base_path)
            repo_type: Type of repository ("model" or "dataset")
            allow_patterns: Patterns to include
            ignore_patterns: Patterns to exclude

        Returns:
            Path to downloaded model
        """
        output_dir = self.base_path / local_dir

        print(f"📥 Downloading {repo_id}")
        print(f"   To: {output_dir}")
        print(f"   This may take 10-30 minutes depending on your internet speed...\n")

        try:
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(output_dir),
                local_dir_use_symlinks=False,
                repo_type=repo_type,
                resume_download=True,  # Resume interrupted downloads
                allow_patterns=allow_patterns,
                ignore_patterns=ignore_patterns
            )

            print(f"   ✅ Successfully downloaded {repo_id}\n")
            return output_dir

        except Exception as e:
            print(f"   ❌ Failed to download {repo_id}: {e}\n")
            raise

    def download_from_civitai(
        self,
        model_id: int,
        output_filename: str,
        local_dir: str
    ) -> Path:
        """
        Download model from CivitAI

        Args:
            model_id: CivitAI model ID
            output_filename: Output filename (e.g., "model.safetensors")
            local_dir: Local directory name (relative to base_path)

        Returns:
            Path to downloaded model
        """
        output_dir = self.base_path / local_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / output_filename

        # Check if already downloaded
        if output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024**2)
            print(f"📁 Model already exists: {output_path}")
            print(f"   Size: {file_size_mb:.2f} MB")

            response = input("   Re-download? (y/n): ").strip().lower()
            if response != 'y':
                print(f"   ✅ Using existing file\n")
                return output_path

        url = f"https://civitai.com/api/download/models/{model_id}"

        print(f"📥 Downloading from CivitAI (Model ID: {model_id})")
        print(f"   URL: {url}")
        print(f"   To: {output_path}")
        print(f"   This may take 5-15 minutes...\n")

        try:
            # Stream download with progress bar
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192

            with open(output_path, 'wb') as f, tqdm(
                desc=output_filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as progress_bar:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))

            file_size_mb = output_path.stat().st_size / (1024**2)
            print(f"   ✅ Successfully downloaded ({file_size_mb:.2f} MB)\n")
            return output_path

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Failed to download from CivitAI: {e}\n")
            if output_path.exists():
                output_path.unlink()  # Delete partial download
            raise

    def download_svd_xt(self) -> Path:
        """Download Stable Video Diffusion XT model (~10GB)"""
        print("=" * 70)
        print("📦 MODEL 1/3: Stable Video Diffusion XT (SVD-XT)")
        print("=" * 70)
        print("Source: Stability AI (HuggingFace)")
        print("Size: ~10 GB")
        print("Purpose: Fast image-to-video generation\n")

        return self.download_from_huggingface(
            repo_id="stabilityai/stable-video-diffusion-img2vid-xt",
            local_dir="svd-xt",
            ignore_patterns=["*.md", "*.txt", ".gitattributes"]  # Skip docs
        )

    def download_animatediff(self) -> Path:
        """Download AnimateDiff motion adapter (~3GB)"""
        print("=" * 70)
        print("📦 MODEL 2/3: AnimateDiff Motion Adapter")
        print("=" * 70)
        print("Source: guoyww (HuggingFace)")
        print("Size: ~3 GB")
        print("Purpose: Motion module for Stable Diffusion models\n")

        return self.download_from_huggingface(
            repo_id="guoyww/animatediff-motion-adapter-v1-5-2",
            local_dir="animatediff",
            ignore_patterns=["*.md", "*.txt", ".gitattributes"]
        )

    def download_realistic_vision(self) -> Path:
        """Download Realistic Vision v5.1 from CivitAI (~2GB)"""
        print("=" * 70)
        print("📦 MODEL 3/3: Realistic Vision v5.1 (SD 1.5 Base)")
        print("=" * 70)
        print("Source: CivitAI (Model ID: 130072)")
        print("Size: ~2 GB")
        print("Purpose: Photorealistic base model for AnimateDiff")
        print("NSFW: Capable (no safety filter)\n")

        return self.download_from_civitai(
            model_id=130072,  # Realistic Vision v5.1
            output_filename="realisticVision_v51.safetensors",
            local_dir="realistic-vision"
        )

    def verify_downloads(self) -> bool:
        """Verify all models are downloaded correctly"""
        print("\n" + "=" * 70)
        print("🔍 Verifying Downloads")
        print("=" * 70 + "\n")

        models = {
            "SVD-XT": self.base_path / "svd-xt",
            "AnimateDiff": self.base_path / "animatediff",
            "Realistic Vision": self.base_path / "realistic-vision" / "realisticVision_v51.safetensors"
        }

        all_valid = True

        for name, path in models.items():
            if path.exists():
                if path.is_dir():
                    # Check if directory has files
                    file_count = len(list(path.glob("**/*")))
                    if file_count > 0:
                        print(f"✅ {name}: Found ({file_count} files)")
                    else:
                        print(f"❌ {name}: Directory empty")
                        all_valid = False
                else:
                    # Check file size
                    size_mb = path.stat().st_size / (1024**2)
                    if size_mb > 100:  # Should be at least 100MB
                        print(f"✅ {name}: Found ({size_mb:.0f} MB)")
                    else:
                        print(f"❌ {name}: File too small ({size_mb:.0f} MB)")
                        all_valid = False
            else:
                print(f"❌ {name}: Not found")
                all_valid = False

        return all_valid

    def download_all(self, models: list = None) -> bool:
        """
        Download all models or specific models

        Args:
            models: List of model names to download (None = all)
                    Options: "svd", "animatediff", "realistic-vision"

        Returns:
            True if all downloads successful, False otherwise
        """
        if models is None:
            models = ["svd", "animatediff", "realistic-vision"]

        print("\n" + "=" * 70)
        print("🚀 IMAGE-TO-VIDEO GENERATOR - MODEL DOWNLOADER")
        print("=" * 70)
        print(f"\nModels to download: {', '.join(models)}")
        print(f"Total size: ~15 GB (may vary)")
        print(f"Estimated time: 20-60 minutes (depends on internet speed)\n")

        # Check disk space
        if not self.check_disk_space(required_gb=20):
            print("❌ Insufficient disk space. Please free up space and try again.")
            return False

        input("Press Enter to start downloading, or Ctrl+C to cancel...")
        print()

        try:
            if "svd" in models:
                self.download_svd_xt()

            if "animatediff" in models:
                self.download_animatediff()

            if "realistic-vision" in models:
                self.download_realistic_vision()

            # Verify all downloads
            if self.verify_downloads():
                print("\n" + "=" * 70)
                print("✅ ALL MODELS DOWNLOADED SUCCESSFULLY!")
                print("=" * 70)
                print("\nNext steps:")
                print("  1. Verify GPU access: python scripts/check_gpu.py")
                print("  2. Test generation: python backend/test_generation.py")
                print("  3. Start developing!\n")
                return True
            else:
                print("\n" + "=" * 70)
                print("⚠️  SOME MODELS MAY BE INCOMPLETE")
                print("=" * 70)
                print("\nPlease re-run this script to retry failed downloads.\n")
                return False

        except KeyboardInterrupt:
            print("\n\n⚠️  Download cancelled by user")
            print("You can resume by running this script again.\n")
            return False
        except Exception as e:
            print(f"\n\n❌ Download failed: {e}")
            print("You can retry by running this script again.\n")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download AI models for Image-to-Video Generator"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="/mnt/d/VideoGenerator/models",
        help="Output directory (default: /mnt/d/VideoGenerator/models)"
    )
    parser.add_argument(
        "--models",
        "-m",
        nargs="+",
        choices=["svd", "animatediff", "realistic-vision"],
        help="Specific models to download (default: all)"
    )

    args = parser.parse_args()

    # Create downloader
    downloader = ModelDownloader(base_path=args.output)

    # Download models
    success = downloader.download_all(models=args.models)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
