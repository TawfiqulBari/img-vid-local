# Build Instructions

## Quick Build (Windows)

### Option 1: Run from WSL Path

1. Open **Windows PowerShell** or **Command Prompt**
2. Navigate to the project:
   ```cmd
   cd \\wsl.localhost\Ubuntu\home\tawfiq\personal-projects\image-video-3
   ```
3. Run the build script:
   ```cmd
   build_and_package.bat
   ```

### Option 2: Copy to Windows Drive

1. Open **Windows PowerShell**
2. Copy project to C drive:
   ```powershell
   cp -Recurse \\wsl.localhost\Ubuntu\home\tawfiq\personal-projects\image-video-3 C:\Temp\img-vid-local
   cd C:\Temp\img-vid-local
   ```
3. Run the build script:
   ```cmd
   build_and_package.bat
   ```

## What the Script Does

The `build_and_package.bat` script will:

1. ✅ Restore NuGet packages
2. ✅ Build C# application in Release mode
3. ✅ Copy all files to `release/` directory
4. ✅ Create portable ZIP package
5. ✅ Copy packages to your **Downloads** folder

## Output Files

After running, you'll find:

- **Portable Package:** `release/portable/ImageToVideoGenerator-v1.0.0-Portable.zip`
- **In Downloads:** `C:\Users\<YourUsername>\Downloads\ImageToVideoGenerator-v1.0.0-Portable.zip`

## Creating the Installer (Optional)

The installer requires **Inno Setup** to be installed on Windows.

### Install Inno Setup

1. Download from: https://jrsoftware.org/isinfo.php
2. Install (use default settings)

### Compile Installer

1. Navigate to project directory
2. Right-click `installer\setup.iss`
3. Select **"Compile"**
4. Installer will be created at: `installer\Output\ImageToVideoGenerator-Setup-v1.0.0.exe`
5. Run `build_and_package.bat` again to copy installer to Downloads

## Upload to GitHub Release

After building, upload to GitHub from WSL:

```bash
# From WSL
cd /home/tawfiq/personal-projects/image-video-3

# Upload portable package
gh release upload v1.0.0 release/portable/ImageToVideoGenerator-v1.0.0-Portable.zip

# Upload installer (if created)
gh release upload v1.0.0 installer/Output/ImageToVideoGenerator-Setup-v1.0.0.exe
```

Or upload manually:
1. Go to: https://github.com/TawfiqulBari/img-vid-local/releases/tag/v1.0.0
2. Click **"Edit release"**
3. Drag and drop the files from your Downloads folder
4. Click **"Update release"**

## Troubleshooting

### ".NET SDK not found"

Install .NET 6.0 SDK:
- Download: https://dotnet.microsoft.com/download/dotnet/6.0
- Install: "SDK x64" version

### "PowerShell execution policy"

Run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Access denied" errors

Run Command Prompt or PowerShell as **Administrator**

## Quick Summary

**From Windows Command Prompt:**
```cmd
cd \\wsl.localhost\Ubuntu\home\tawfiq\personal-projects\image-video-3
build_and_package.bat
```

**Result:**
- Portable ZIP in your Downloads folder
- Ready to upload to GitHub
- Ready to distribute!

---

That's it! The script automates everything. Just run it from Windows.
