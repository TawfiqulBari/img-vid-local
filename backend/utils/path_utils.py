"""
Path Conversion Utilities for WSL/Windows Hybrid Development

Handles conversion between WSL paths (/mnt/d/) and Windows paths (D:\)
Critical for proper operation in hybrid WSL development + Windows deployment environment.
"""

import os
import platform
from pathlib import Path
from typing import Union


def windows_to_wsl_path(windows_path: str) -> str:
    """
    Convert Windows path to WSL path

    Examples:
        D:\\VideoGenerator\\models -> /mnt/d/VideoGenerator/models
        C:\\Users\\Name\\file.txt -> /mnt/c/Users/Name/file.txt

    Args:
        windows_path: Windows-style path (D:\\path or D:/path)

    Returns:
        WSL-style path (/mnt/d/path)
    """
    if not windows_path:
        return windows_path

    # Normalize backslashes to forward slashes
    path = windows_path.replace('\\', '/')

    # Remove trailing slashes
    path = path.rstrip('/')

    # Check if it's a drive letter path (e.g., D:/ or D:\)
    if len(path) >= 2 and path[1] == ':':
        drive = path[0].lower()
        rest = path[2:]  # Everything after "D:"

        # Remove leading slash if present
        if rest.startswith('/'):
            rest = rest[1:]

        return f"/mnt/{drive}/{rest}" if rest else f"/mnt/{drive}"

    # Already a WSL path or relative path
    return path


def wsl_to_windows_path(wsl_path: str) -> str:
    """
    Convert WSL path to Windows path

    Examples:
        /mnt/d/VideoGenerator/models -> D:\\VideoGenerator\\models
        /mnt/c/Users/Name/file.txt -> C:\\Users\\Name\\file.txt

    Args:
        wsl_path: WSL-style path (/mnt/d/path)

    Returns:
        Windows-style path (D:\\path)
    """
    if not wsl_path:
        return wsl_path

    # Check if it's a /mnt/ path
    if wsl_path.startswith('/mnt/'):
        # Split: /mnt/d/path/to/file -> ['', 'mnt', 'd', 'path', 'to', 'file']
        parts = wsl_path.split('/')

        if len(parts) >= 3:
            drive = parts[2].upper()  # 'd' -> 'D'
            rest = '/'.join(parts[3:]) if len(parts) > 3 else ''

            # Convert to Windows backslashes
            rest = rest.replace('/', '\\')

            return f"{drive}:\\{rest}" if rest else f"{drive}:\\"

    # Already a Windows path or relative path
    return wsl_path.replace('/', '\\')


def normalize_path(path: str, target_system: str = None) -> str:
    """
    Normalize path for current or target system

    Args:
        path: Path to normalize
        target_system: Target system ('windows', 'wsl', or None for auto-detect)

    Returns:
        Normalized path for target system
    """
    if not path:
        return path

    # Auto-detect if not specified
    if target_system is None:
        system = platform.system()

        if system == "Windows":
            target_system = "windows"
        elif system == "Linux":
            # Check if running in WSL
            if os.path.exists('/mnt/c'):
                target_system = "wsl"
            else:
                target_system = "linux"
        else:
            target_system = "linux"

    target_system = target_system.lower()

    if target_system == "windows":
        # Convert to Windows format
        if path.startswith('/mnt/'):
            return wsl_to_windows_path(path)
        return path.replace('/', '\\')

    elif target_system == "wsl":
        # Convert to WSL format
        if len(path) >= 2 and path[1] == ':':
            return windows_to_wsl_path(path)
        return path.replace('\\', '/')

    else:  # linux
        # Just use forward slashes
        return path.replace('\\', '/')


def ensure_path_exists(path: Union[str, Path], is_file: bool = False) -> Path:
    """
    Ensure path exists, creating directories if needed

    Args:
        path: Path to ensure exists
        is_file: If True, create parent directory; if False, create directory itself

    Returns:
        Path object
    """
    path = Path(path)

    if is_file:
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path.mkdir(parents=True, exist_ok=True)

    return path


def get_model_path(model_name: str, base_dir: str = "/mnt/d/VideoGenerator/models") -> str:
    """
    Get full path to a model directory

    Args:
        model_name: Name of model subdirectory (e.g., "svd-xt", "animatediff")
        base_dir: Base models directory

    Returns:
        Full path to model
    """
    return os.path.join(base_dir, model_name)


def get_output_path(filename: str, base_dir: str = "/mnt/d/VideoGenerator/output") -> str:
    """
    Get full path for output file

    Args:
        filename: Output filename (e.g., "video_001.mp4")
        base_dir: Base output directory

    Returns:
        Full path for output file
    """
    ensure_path_exists(base_dir, is_file=False)
    return os.path.join(base_dir, filename)


def validate_path_exists(path: str, path_type: str = "file") -> bool:
    """
    Validate that a path exists

    Args:
        path: Path to validate
        path_type: Type of path ("file", "directory", or "any")

    Returns:
        True if path exists and matches type, False otherwise
    """
    if not path or not os.path.exists(path):
        return False

    if path_type == "file":
        return os.path.isfile(path)
    elif path_type == "directory":
        return os.path.isdir(path)
    else:  # "any"
        return True


# Example usage and testing
if __name__ == "__main__":
    print("Path Conversion Utilities Test\n")

    # Test Windows -> WSL
    test_windows_paths = [
        "D:\\VideoGenerator\\models\\svd-xt",
        "C:\\Users\\Test\\image.jpg",
        "D:/VideoGenerator/output/video.mp4"
    ]

    print("Windows → WSL:")
    for wp in test_windows_paths:
        wsl = windows_to_wsl_path(wp)
        print(f"  {wp}")
        print(f"  → {wsl}\n")

    # Test WSL -> Windows
    test_wsl_paths = [
        "/mnt/d/VideoGenerator/models/svd-xt",
        "/mnt/c/Users/Test/image.jpg",
        "/mnt/d/VideoGenerator/output/video.mp4"
    ]

    print("WSL → Windows:")
    for wsl in test_wsl_paths:
        win = wsl_to_windows_path(wsl)
        print(f"  {wsl}")
        print(f"  → {win}\n")

    # Test round-trip
    print("Round-trip test:")
    original = "D:\\VideoGenerator\\models\\svd-xt"
    wsl = windows_to_wsl_path(original)
    back = wsl_to_windows_path(wsl)
    print(f"  Original: {original}")
    print(f"  → WSL:    {wsl}")
    print(f"  → Back:   {back}")
    print(f"  Match: {original.replace('\\\\', '\\') == back}")
