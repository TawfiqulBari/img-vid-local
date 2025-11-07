# WSL + Windows Development Guide

## Overview

This project uses a **hybrid development approach**:
- **Development Environment**: WSL (Windows Subsystem for Linux) - Ubuntu
- **Deployment Target**: Windows (WPF desktop application)
- **Model Storage**: Windows D:\ drive (accessible from both environments)

This guide covers setting up and working across both environments effectively.

---

## Why WSL for Development?

### Benefits of WSL Development

1. **Better Python/Linux Tooling**: Most AI/ML tools are designed for Linux
2. **Faster File Operations**: Linux filesystem for development files
3. **Native Package Management**: apt, pip work better in Linux
4. **Docker/Container Support**: If needed for future features
5. **Consistent with dup-checker**: Following proven development methodology

### Why Not Develop Entirely in WSL?

1. **WPF is Windows-Only**: No cross-platform support for WPF
2. **Visual Studio**: Best C# IDE is Windows-only
3. **GPU Drivers**: More stable on Windows host
4. **Deployment**: Target platform is Windows

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Host (OS)                         │
│                                                              │
│  ┌────────────────────┐          ┌─────────────────────┐   │
│  │  D:\VideoGenerator │          │  C:\Program Files\  │   │
│  │  \models\          │◄─────────┤  VideoGenerator\    │   │
│  │  \output\          │  Access  │  (WPF App)          │   │
│  │  (Shared Storage)  │          └─────────────────────┘   │
│  └────────┬───────────┘                                     │
│           │                                                  │
│           │ Mounted as /mnt/d/                              │
│           │                                                  │
│  ┌────────▼───────────────────────────────────────────┐    │
│  │              WSL 2 (Ubuntu)                        │    │
│  │                                                     │    │
│  │  /home/tawfiq/personal-projects/image-video-3/    │    │
│  │  ├── backend/  (Python development)                │    │
│  │  ├── frontend/ (C# editing with VS Code)          │    │
│  │  ├── plans/                                        │    │
│  │  └── scripts/                                      │    │
│  │                                                     │    │
│  │  GPU Access: ✅ (via NVIDIA drivers in WSL)       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Windows Side

1. **Windows 10/11** (Build 19044 or higher)
2. **WSL 2 installed** (not WSL 1)
3. **NVIDIA GPU** (RTX 3060 or similar)
4. **NVIDIA Drivers** (525.x or newer)

### WSL Side

1. **Ubuntu 22.04 LTS** (recommended)
2. **Python 3.10**
3. **CUDA support in WSL**
4. **Git**

---

## Initial Setup

### Step 1: Install WSL 2

Open PowerShell as Administrator:

```powershell
# Install WSL with Ubuntu
wsl --install -d Ubuntu-22.04

# Set WSL 2 as default
wsl --set-default-version 2

# Verify installation
wsl --list --verbose
```

### Step 2: Install NVIDIA Drivers for WSL

**On Windows (Host)**:

1. Download latest **Game Ready Driver** from NVIDIA
   - https://www.nvidia.com/Download/index.aspx
2. Install normally on Windows
3. **Do NOT install CUDA toolkit on Windows** (not needed)

**In WSL**:

```bash
# Check if GPU is accessible
nvidia-smi

# Should show your RTX 3060
```

If `nvidia-smi` doesn't work, follow: https://docs.nvidia.com/cuda/wsl-user-guide/index.html

### Step 3: Set Up Development Directory

**In WSL**:

```bash
# Navigate to your projects directory
cd ~/personal-projects

# Clone or initialize project
git clone https://github.com/TawfiqulBari/image-video-3.git
# OR if starting fresh:
mkdir image-video-3 && cd image-video-3
```

### Step 4: Create Shared Model Storage

**On Windows (PowerShell or File Explorer)**:

```powershell
# Create directories on D: drive
New-Item -Path "D:\VideoGenerator" -ItemType Directory
New-Item -Path "D:\VideoGenerator\models" -ItemType Directory
New-Item -Path "D:\VideoGenerator\output" -ItemType Directory
```

**Verify from WSL**:

```bash
# Check access from WSL
ls /mnt/d/VideoGenerator

# Should show: models  output
```

---

## Path Conversion Reference

### Quick Reference Table

| Windows Path | WSL Path | Notes |
|-------------|----------|-------|
| `D:\VideoGenerator\models` | `/mnt/d/VideoGenerator/models` | Model storage |
| `D:\VideoGenerator\output` | `/mnt/d/VideoGenerator/output` | Generated videos |
| `C:\Users\YourName\Pictures` | `/mnt/c/Users/YourName/Pictures` | User files |
| `\\wsl$\Ubuntu\home\tawfiq` | N/A (Windows UNC path) | Access WSL from Windows |

### Conversion Rules

**Windows → WSL**:
```
D:\path\to\file  →  /mnt/d/path/to/file
C:\path\to\file  →  /mnt/c/path/to/file

Rules:
1. Drive letter (D:) becomes /mnt/d/
2. Backslashes (\) become forward slashes (/)
3. Case-sensitive in WSL!
```

**WSL → Windows**:
```
/mnt/d/path/to/file  →  D:\path\to\file
/mnt/c/path/to/file  →  C:\path\to\file

Rules:
1. /mnt/d/ becomes D:\
2. Forward slashes (/) become backslashes (\)
3. Windows is case-insensitive
```

### Command-Line Tools

**In WSL** (convert to Windows path):
```bash
wslpath -w /mnt/d/VideoGenerator/models
# Output: D:\VideoGenerator\models
```

**In Windows** (convert to WSL path):
```powershell
wsl wslpath -u "D:\VideoGenerator\models"
# Output: /mnt/d/VideoGenerator/models
```

---

## Development Workflow

### Daily Development Routine

**1. Start WSL Session**:

```bash
# Open Windows Terminal or WSL terminal
wsl

# Navigate to project
cd ~/personal-projects/image-video-3

# Activate Python environment
source backend/venv/bin/activate
```

**2. Edit Code**:

```bash
# Use VS Code in WSL
code .

# Or use any editor
vim backend/pipelines/svd_pipeline.py
```

**3. Test Python Backend**:

```bash
# Run tests
python backend/test_generation.py

# Test video generation
python backend/generate.py '{"imagePath":"/mnt/d/test.jpg","prompt":"zoom in","pipeline":"svd",...}'
```

**4. Edit C# Frontend** (if needed):

Option A - VS Code in WSL:
```bash
code frontend/VideoGenerator/MainWindow.xaml.cs
```

Option B - Visual Studio on Windows:
```
Open: \\wsl$\Ubuntu\home\tawfiq\personal-projects\image-video-3\frontend\VideoGenerator.sln
```

**5. Build C# Application** (on Windows):

```powershell
# In PowerShell or CMD
cd \\wsl$\Ubuntu\home\tawfiq\personal-projects\image-video-3\frontend
dotnet build VideoGenerator.sln
```

---

## File Access Patterns

### Best Practices

**✅ DO:**
- Store code in WSL filesystem (`~/personal-projects/`)
- Store models on Windows drive (`D:\VideoGenerator\models`)
- Store output on Windows drive (`D:\VideoGenerator\output`)
- Edit code using VS Code in WSL
- Use `/mnt/d/` paths in Python code
- Use `D:\` paths in C# code

**❌ DON'T:**
- Store code on Windows, edit from WSL (slow)
- Store large models in WSL filesystem (limited space)
- Mix path styles in same codebase
- Use relative paths across environments

### Performance Considerations

**Fast** (native filesystem):
```bash
# WSL → WSL files
ls ~/personal-projects/image-video-3/backend/

# Windows → Windows files
dir D:\VideoGenerator\models\
```

**Slow** (cross-filesystem):
```bash
# WSL → Windows files (acceptable for models)
ls /mnt/d/VideoGenerator/models/

# Windows → WSL files (avoid if possible)
dir \\wsl$\Ubuntu\home\tawfiq\personal-projects\
```

### When to Use Each Filesystem

| Data Type | Location | Filesystem | Why |
|-----------|----------|------------|-----|
| Python code | WSL | Linux | Fast development, native tools |
| C# code | WSL | Linux | Version control, fast editing |
| AI Models | Windows D:\ | NTFS | Large files, shared access |
| Generated videos | Windows D:\ | NTFS | User access, video players |
| Temp files | WSL | Linux | Fast I/O, automatic cleanup |
| Config files | Windows D:\ | NTFS | Persistent, user-editable |

---

## Common Tasks

### Running Python Backend Tests

```bash
# In WSL
cd ~/personal-projects/image-video-3
source backend/venv/bin/activate

# Check GPU
python backend/check_gpu.py

# Download models (first time)
python backend/download_models.py

# Test generation
python backend/test_generation.py --pipeline svd --image /mnt/d/test.jpg
```

### Building C# Application

**From WSL**:
```bash
cd frontend
dotnet build VideoGenerator.sln
dotnet run --project VideoGenerator
```

**From Windows**:
```powershell
cd \\wsl$\Ubuntu\home\tawfiq\personal-projects\image-video-3\frontend
dotnet build
.\VideoGenerator\bin\Debug\net6.0-windows\VideoGenerator.exe
```

### Accessing Files Across Environments

**From Windows Explorer**:
```
Address bar: \\wsl$\Ubuntu\home\tawfiq\personal-projects\image-video-3
```

**From WSL**:
```bash
# Open Windows Explorer from current directory
explorer.exe .

# Open specific Windows path
explorer.exe /mnt/d/VideoGenerator/output
```

---

## Git Workflow in WSL

### Initial Setup

```bash
# Configure git (if not done)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set line endings (important for cross-platform)
git config --global core.autocrlf input
```

### Standard Workflow

```bash
# Create feature branch
git checkout -b feature/add-prompt-support

# Make changes, add files
git add backend/pipelines/svd_pipeline.py
git commit -m "Add prompt support to SVD pipeline"

# Push to GitHub
git push origin feature/add-prompt-support
```

### Handling Line Endings

**Issue**: Windows uses `\r\n` (CRLF), Linux uses `\n` (LF)

**Solution**: `.gitattributes` file (already in project):
```
# Auto-detect text files and normalize line endings
* text=auto

# Force LF for Python files
*.py text eol=lf
*.sh text eol=lf

# Force CRLF for Windows files
*.cs text eol=crlf
*.xaml text eol=crlf
*.sln text eol=crlf
```

---

## Troubleshooting

### GPU Not Accessible in WSL

**Symptoms**:
```bash
nvidia-smi
# Error: nvidia-smi: command not found
```

**Solutions**:

1. **Update Windows**:
   ```powershell
   # In PowerShell
   winget upgrade
   ```

2. **Update NVIDIA Drivers**:
   - Download latest from NVIDIA website
   - Restart Windows

3. **Check WSL Version**:
   ```powershell
   wsl --list --verbose
   # Ensure VERSION is 2, not 1
   ```

4. **Reinstall CUDA in WSL** (if needed):
   ```bash
   # Follow: https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=WSL-Ubuntu&target_version=2.0
   ```

### Permission Denied Errors

**Symptoms**:
```bash
bash: ./setup_wsl.sh: Permission denied
```

**Solution**:
```bash
# Make script executable
chmod +x setup_wsl.sh
```

### Path Not Found Errors

**Symptoms**:
```python
FileNotFoundError: D:\VideoGenerator\models\svd-xt
```

**Solution** (in Python):
```python
# Use WSL path
model_path = "/mnt/d/VideoGenerator/models/svd-xt"
```

### Slow File Access

**Symptoms**: Very slow `ls` or file operations on `/mnt/c/` or `/mnt/d/`

**Cause**: Cross-filesystem access is slower

**Solutions**:
1. **Keep code in WSL** filesystem (`~/`)
2. **Keep only large files** (models, videos) on Windows drive
3. **Use fast SSD** for D:\ drive if possible

### Python Module Not Found

**Symptoms**:
```python
ModuleNotFoundError: No module named 'torch'
```

**Solution**:
```bash
# Ensure virtual environment is activated
source backend/venv/bin/activate

# Verify Python path
which python
# Should show: /home/tawfiq/personal-projects/image-video-3/backend/venv/bin/python

# Reinstall if needed
pip install -r backend/requirements.txt
```

---

## Performance Tips

### Optimize WSL Performance

**1. Limit WSL Memory Usage** (create `.wslconfig`):

**Windows**: `C:\Users\YourName\.wslconfig`
```ini
[wsl2]
memory=16GB          # Limit WSL memory
processors=8         # Number of CPU cores
swap=8GB             # Swap file size
localhostForwarding=true
```

**2. Use Fast Storage**:
- Store WSL instance on NVMe/SSD
- Store models on fast drive (D:\ on SSD)

**3. Disable Windows Defender Scanning**:

Add exclusions in Windows Security:
- `\\wsl$\Ubuntu\home\tawfiq\personal-projects\`
- `D:\VideoGenerator\`

---

## IDE Setup

### VS Code in WSL (Recommended)

**Installation**:
```bash
# In WSL
cd ~/personal-projects/image-video-3
code .
```

**Recommended Extensions**:
- Python (ms-python.python)
- C# (ms-dotnettools.csharp)
- GitLens
- Remote - WSL (ms-vscode-remote.remote-wsl)

**Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "files.eol": "\n",
  "editor.formatOnSave": true
}
```

### Visual Studio (for C# only)

**Open from Windows**:
```
File → Open → \\wsl$\Ubuntu\home\tawfiq\personal-projects\image-video-3\frontend\VideoGenerator.sln
```

---

## Deployment from WSL

### Building Release (Windows Target)

**In WSL**:
```bash
cd frontend
dotnet publish VideoGenerator.sln -c Release -r win-x64 --self-contained false

# Output: frontend/VideoGenerator/bin/Release/net6.0-windows/win-x64/publish/
```

**Package Python Backend**:
```bash
cd backend

# Create release folder
mkdir -p ../release/backend

# Copy Python files
cp -r pipelines services utils *.py ../release/backend/

# Copy dependencies
pip freeze > ../release/backend/requirements.txt
```

**Create Release Archive**:
```bash
cd release
tar -czf VideoGenerator-v1.0.0.tar.gz backend/ frontend/

# Or use zip
zip -r VideoGenerator-v1.0.0.zip backend/ frontend/
```

---

## Quick Command Reference

### Path Conversion

```bash
# WSL → Windows
wslpath -w /mnt/d/VideoGenerator
# → D:\VideoGenerator

# Windows → WSL
wslpath -u 'D:\VideoGenerator'
# → /mnt/d/VideoGenerator
```

### File Explorer

```bash
# Open current directory in Windows Explorer
explorer.exe .

# Open specific path
explorer.exe /mnt/d/VideoGenerator/output
```

### Network Access

```bash
# From Windows, access WSL
\\wsl$\Ubuntu\home\tawfiq\

# From WSL, access Windows
/mnt/c/Users/YourName/
```

### Process Management

```bash
# See WSL resource usage
# In Windows PowerShell:
wsl --system -d Ubuntu -- top

# Restart WSL (if needed)
wsl --shutdown
wsl
```

---

## Best Practices Summary

### DO:
✅ Develop all code in WSL filesystem
✅ Store models on Windows D:\ drive
✅ Use `/mnt/d/` paths in Python
✅ Use `D:\` paths in C# code
✅ Commit code from WSL
✅ Build releases from WSL
✅ Keep virtual environments in WSL
✅ Use VS Code with WSL extension

### DON'T:
❌ Edit WSL files from Windows native tools
❌ Store code on Windows drive
❌ Mix path formats in same file
❌ Use WSL 1 (use WSL 2)
❌ Store models in WSL filesystem
❌ Hardcode absolute paths
❌ Forget to activate venv
❌ Use outdated NVIDIA drivers

---

This guide should help you navigate the WSL + Windows hybrid development environment efficiently!
