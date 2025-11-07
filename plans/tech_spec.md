# Updated Technical Specification: Offline Image-to-Video Generator

Understood - since this is a local, offline application for personal use, I'll focus on the technical implementation without content filtering layers.

---

## Key Changes for Offline Personal Use

### 1. Model Selection for Unrestricted Use

**Primary Recommendation: Stable Video Diffusion (SVD)**
- No built-in content filtering when run locally
- Open-source, runs entirely offline
- Full control over generation parameters

**Alternative Models (No filters when local)**:
- AnimateDiff + Stable Diffusion 1.5 base
- ModelScope text-to-video
- Custom fine-tuned models from CivitAI

---

## 2. Simplified Architecture (No Cloud/API)

```
Local Application Structure:
├── Frontend (WPF/C#)
│   └── Directly calls Python backend via subprocess
├── Backend (Python)
│   ├── Model inference
│   └── Video encoding
└── Models (Local storage)
    └── No external API calls
```

### 2.1 Direct Python Integration (No Web Server)

**Option A: Python.NET Integration**
```csharp
// C# calling Python directly
using Python.Runtime;

public class LocalVideoGenerator
{
    private dynamic _pythonModule;
    
    public void Initialize()
    {
        Runtime.PythonDLL = @"C:\Python310\python310.dll";
        PythonEngine.Initialize();
        
        _pythonModule = Py.Import("video_generator");
    }
    
    public async Task<string> GenerateVideo(
        string imagePath, 
        string prompt, 
        GenerationParams parameters)
    {
        using (Py.GIL())
        {
            dynamic result = _pythonModule.generate_video(
                imagePath, 
                prompt,
                parameters.NumFrames,
                parameters.FPS,
                parameters.GuidanceScale
            );
            return result.ToString();
        }
    }
}
```

**Option B: Subprocess (Simpler, Recommended)**
```csharp
public class PythonBackend
{
    private Process _pythonProcess;
    
    public string GenerateVideo(GenerationRequest request)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = "python.exe",
            Arguments = $"generate.py \"{request.ToJson()}\"",
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
        
        using var process = Process.Start(startInfo);
        string output = process.StandardOutput.ReadToEnd();
        process.WaitForExit();
        
        return output;
    }
}
```

---

## 3. Complete Python Backend (No Filters)

### 3.1 Core Generation Script

```python
# generate.py - Standalone generation script

import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image, export_to_video
from PIL import Image
import sys
import json

class VideoGenerator:
    def __init__(self, model_path="./models/svd-xt"):
        """Initialize with local model path"""
        self.device = "cuda"
        self.dtype = torch.float16
        
        # Load model from local directory
        self.pipe = StableVideoDiffusionPipeline.from_pretrained(
            model_path,
            torch_dtype=self.dtype,
            variant="fp16",
            local_files_only=True  # No internet required
        )
        
        # Move to GPU with optimizations
        self.pipe.to(self.device)
        
        # Critical optimizations for 12GB VRAM
        self.pipe.enable_model_cpu_offload()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        
        # Use xformers if available
        try:
            self.pipe.enable_xformers_memory_efficient_attention()
        except:
            pass
    
    def generate(self, 
                 image_path,
                 prompt="",  # SVD doesn't use text prompts heavily
                 num_frames=25,
                 fps=8,
                 motion_bucket_id=127,
                 noise_aug_strength=0.02,
                 decode_chunk_size=4,
                 num_inference_steps=25,
                 guidance_scale=1.0,
                 seed=-1,
                 output_path="output.mp4"):
        """
        Generate video from image
        
        Args:
            image_path: Path to input image
            num_frames: Number of frames (25 = ~1 sec at 25fps)
            fps: Frames per second for output video
            motion_bucket_id: Controls motion amount (1-255, 127=default)
            decode_chunk_size: Lower = less VRAM but slower
        """
        
        # Set seed for reproducibility
        if seed != -1:
            torch.manual_seed(seed)
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = None
        
        # Load and preprocess image
        image = load_image(image_path)
        image = image.resize((1024, 576))  # 16:9 aspect ratio
        
        # Generate frames
        frames = self.pipe(
            image=image,
            num_frames=num_frames,
            decode_chunk_size=decode_chunk_size,
            num_inference_steps=num_inference_steps,
            motion_bucket_id=motion_bucket_id,
            noise_aug_strength=noise_aug_strength,
            generator=generator,
            guidance_scale=guidance_scale
        ).frames[0]
        
        # Export to video
        export_to_video(frames, output_path, fps=fps)
        
        return output_path

def main():
    # Parse command line arguments
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        print("Usage: python generate.py '{json_params}'")
        return
    
    # Initialize generator
    generator = VideoGenerator()
    
    # Generate video
    output = generator.generate(
        image_path=params['image_path'],
        num_frames=params.get('num_frames', 25),
        fps=params.get('fps', 8),
        motion_bucket_id=params.get('motion_bucket_id', 127),
        decode_chunk_size=params.get('decode_chunk_size', 4),
        num_inference_steps=params.get('num_inference_steps', 25),
        seed=params.get('seed', -1),
        output_path=params.get('output_path', 'output.mp4')
    )
    
    print(json.dumps({"status": "success", "output": output}))

if __name__ == "__main__":
    main()
```

---

## 4. Using Alternative Base Models

If you want more control over the type of content (including fine-tuned models from communities):

### 4.1 AnimateDiff + Custom SD Models

```python
from diffusers import AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
from diffusers.utils import export_to_video
import torch

class AnimateDiffGenerator:
    def __init__(self, 
                 base_model="runwayml/stable-diffusion-v1-5",
                 motion_adapter="guoyww/animatediff-motion-adapter-v1-5-2"):
        
        # Load motion adapter
        adapter = MotionAdapter.from_pretrained(
            motion_adapter, 
            torch_dtype=torch.float16
        )
        
        # Load pipeline with custom base model
        self.pipe = AnimateDiffPipeline.from_pretrained(
            base_model,
            motion_adapter=adapter,
            torch_dtype=torch.float16,
            local_files_only=True
        )
        
        # Scheduler
        self.pipe.scheduler = EulerDiscreteScheduler.from_config(
            self.pipe.scheduler.config,
            timestep_spacing="trailing",
            beta_schedule="linear"
        )
        
        # Optimizations
        self.pipe.enable_model_cpu_offload()
        self.pipe.enable_vae_slicing()
    
    def generate(self,
                 prompt,
                 negative_prompt="",
                 num_frames=16,
                 guidance_scale=7.5,
                 num_inference_steps=25,
                 seed=-1):
        
        if seed != -1:
            generator = torch.Generator("cuda").manual_seed(seed)
        else:
            generator = None
        
        frames = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator
        ).frames[0]
        
        return frames
```

### 4.2 Loading Custom Models from CivitAI

```python
def load_custom_checkpoint(checkpoint_path):
    """Load custom .safetensors or .ckpt models"""
    from diffusers import StableDiffusionPipeline
    
    pipe = StableDiffusionPipeline.from_single_file(
        checkpoint_path,
        torch_dtype=torch.float16,
        load_safety_checker=False,  # No safety checker
    )
    
    return pipe

# Example usage
custom_pipe = load_custom_checkpoint("./models/custom_model.safetensors")
```

---

## 5. Maximum Video Length Calculations for RTX 3060

### 5.1 VRAM Budget Table

```python
# Realistic limits for 12GB VRAM

VRAM_LIMITS = {
    # Resolution: (max_frames, recommended_fps)
    
    # SVD Limits
    'svd_512x512':   (250, 25),  # 10 seconds
    'svd_576x1024':  (120, 24),  # 5 seconds (16:9)
    'svd_768x768':   (80, 24),   # 3.3 seconds
    'svd_1024x576':  (60, 24),   # 2.5 seconds
    
    # AnimateDiff Limits (uses less VRAM)
    'ad_512x512':    (32, 8),    # 4 seconds
    'ad_768x768':    (24, 8),    # 3 seconds
}

def calculate_max_video_length(resolution, model_type='svd'):
    """Calculate maximum video duration"""
    key = f"{model_type}_{resolution}"
    max_frames, fps = VRAM_LIMITS.get(key, (25, 8))
    
    duration = max_frames / fps
    return {
        'max_frames': max_frames,
        'fps': fps,
        'duration_seconds': duration
    }
```

### 5.2 Dynamic VRAM Management

```python
import torch

def get_available_vram():
    """Check available GPU memory"""
    if torch.cuda.is_available():
        free_memory = torch.cuda.mem_get_info()[0] / 1024**3  # GB
        return free_memory
    return 0

def optimize_for_vram(target_frames, resolution):
    """Adjust settings based on available VRAM"""
    available = get_available_vram()
    
    settings = {
        'decode_chunk_size': 8,
        'enable_cpu_offload': False,
        'use_fp16': True
    }
    
    # Adjust based on VRAM
    if available < 8:
        settings['decode_chunk_size'] = 2
        settings['enable_cpu_offload'] = True
        settings['max_frames'] = 50
    elif available < 10:
        settings['decode_chunk_size'] = 4
        settings['enable_cpu_offload'] = True
        settings['max_frames'] = 100
    else:
        settings['decode_chunk_size'] = 8
        settings['max_frames'] = 250
    
    return settings
```

---

## 6. Complete Desktop Application UI

### 6.1 MainWindow.xaml (WPF)

```xml
<Window x:Class="VideoGenerator.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Image to Video Generator" Height="800" Width="1200"
        Background="#1E1E1E">
    
    <Grid>
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width="400"/>
            <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>
        
        <!-- Control Panel -->
        <StackPanel Grid.Column="0" Margin="20">
            <TextBlock Text="Image to Video Generator" 
                      FontSize="24" FontWeight="Bold"
                      Foreground="White" Margin="0,0,0,20"/>
            
            <!-- Image Upload -->
            <Border BorderBrush="#333" BorderThickness="2" 
                   Height="200" Margin="0,0,0,20"
                   AllowDrop="True" Drop="Border_Drop">
                <Grid>
                    <Image x:Name="PreviewImage" Stretch="Uniform"/>
                    <TextBlock Text="Drop image here or click to browse"
                              HorizontalAlignment="Center"
                              VerticalAlignment="Center"
                              Foreground="#666"
                              Visibility="{Binding ImageVisibility}"/>
                </Grid>
            </Border>
            
            <Button Content="Browse Image..." Click="BrowseImage_Click"
                   Height="35" Margin="0,0,0,20"/>
            
            <!-- Generation Settings -->
            <TextBlock Text="Video Settings" FontWeight="Bold" 
                      Foreground="White" Margin="0,0,0,10"/>
            
            <TextBlock Text="Video Length (seconds):" Foreground="#CCC"/>
            <Slider x:Name="DurationSlider" Minimum="1" Maximum="10" 
                   Value="2" TickFrequency="1" IsSnapToTickEnabled="True"/>
            <TextBlock Text="{Binding ElementName=DurationSlider, Path=Value, StringFormat='{}{0:F0} seconds'}"
                      Foreground="#CCC" Margin="0,0,0,10"/>
            
            <TextBlock Text="Frame Rate (FPS):" Foreground="#CCC"/>
            <ComboBox x:Name="FPSComboBox" SelectedIndex="1" Margin="0,0,0,10">
                <ComboBoxItem Content="8 FPS"/>
                <ComboBoxItem Content="12 FPS"/>
                <ComboBoxItem Content="16 FPS"/>
                <ComboBoxItem Content="24 FPS"/>
            </ComboBox>
            
            <TextBlock Text="Resolution:" Foreground="#CCC"/>
            <ComboBox x:Name="ResolutionComboBox" SelectedIndex="0" Margin="0,0,0,10">
                <ComboBoxItem Content="512x512"/>
                <ComboBoxItem Content="576x1024 (16:9)"/>
                <ComboBoxItem Content="768x768"/>
                <ComboBoxItem Content="1024x576 (16:9)"/>
            </ComboBox>
            
            <TextBlock Text="Motion Intensity:" Foreground="#CCC"/>
            <Slider x:Name="MotionSlider" Minimum="1" Maximum="255" 
                   Value="127" Margin="0,0,0,10"/>
            
            <TextBlock Text="Inference Steps:" Foreground="#CCC"/>
            <Slider x:Name="StepsSlider" Minimum="10" Maximum="50" 
                   Value="25" TickFrequency="5" IsSnapToTickEnabled="True"/>
            <TextBlock Text="{Binding ElementName=StepsSlider, Path=Value, StringFormat='{}{0:F0} steps'}"
                      Foreground="#CCC" Margin="0,0,0,10"/>
            
            <TextBlock Text="Seed (0 = random):" Foreground="#CCC"/>
            <TextBox x:Name="SeedTextBox" Text="0" Margin="0,0,0,20"/>
            
            <!-- Generate Button -->
            <Button Content="Generate Video" Click="Generate_Click"
                   Height="45" FontSize="16" FontWeight="Bold"
                   Background="#0078D4" Foreground="White"/>
            
            <!-- Progress -->
            <ProgressBar x:Name="ProgressBar" Height="25" 
                        Margin="0,20,0,10" Visibility="Collapsed"/>
            <TextBlock x:Name="StatusText" Foreground="#CCC" 
                      TextAlignment="Center"/>
        </StackPanel>
        
        <!-- Preview Panel -->
        <Grid Grid.Column="1" Background="#2D2D30">
            <MediaElement x:Name="VideoPlayer" 
                         LoadedBehavior="Manual"
                         UnloadedBehavior="Manual"
                         Stretch="Uniform"/>
            
            <!-- Playback Controls -->
            <StackPanel VerticalAlignment="Bottom" 
                       Background="#CC000000" Height="60">
                <StackPanel Orientation="Horizontal" 
                           HorizontalAlignment="Center">
                    <Button Content="▶ Play" Click="Play_Click" 
                           Margin="5" Padding="15,5"/>
                    <Button Content="⏸ Pause" Click="Pause_Click" 
                           Margin="5" Padding="15,5"/>
                    <Button Content="⏹ Stop" Click="Stop_Click" 
                           Margin="5" Padding="15,5"/>
                    <Button Content="Save As..." Click="SaveAs_Click" 
                           Margin="5" Padding="15,5"/>
                </StackPanel>
            </StackPanel>
        </Grid>
    </Grid>
</Window>
```

### 6.2 MainWindow.xaml.cs

```csharp
using System;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;

namespace VideoGenerator
{
    public partial class MainWindow : Window
    {
        private string _currentImagePath;
        private string _currentVideoPath;
        
        public MainWindow()
        {
            InitializeComponent();
        }
        
        private void BrowseImage_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Filter = "Image files (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg",
                Title = "Select an image"
            };
            
            if (dialog.ShowDialog() == true)
            {
                LoadImage(dialog.FileName);
            }
        }
        
        private void Border_Drop(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                string[] files = (string[])e.Data.GetData(DataFormats.FileDrop);
                if (files.Length > 0)
                {
                    LoadImage(files[0]);
                }
            }
        }
        
        private void LoadImage(string path)
        {
            _currentImagePath = path;
            PreviewImage.Source = new System.Windows.Media.Imaging.BitmapImage(
                new Uri(path));
        }
        
        private async void Generate_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentImagePath))
            {
                MessageBox.Show("Please select an image first.");
                return;
            }
            
            // Show progress
            ProgressBar.Visibility = Visibility.Visible;
            ProgressBar.IsIndeterminate = true;
            StatusText.Text = "Generating video...";
            
            // Prepare parameters
            int duration = (int)DurationSlider.Value;
            int fps = int.Parse(((ComboBoxItem)FPSComboBox.SelectedItem)
                .Content.ToString().Split(' ')[0]);
            int numFrames = duration * fps;
            
            var request = new
            {
                image_path = _currentImagePath,
                num_frames = numFrames,
                fps = fps,
                motion_bucket_id = (int)MotionSlider.Value,
                num_inference_steps = (int)StepsSlider.Value,
                seed = int.Parse(SeedTextBox.Text),
                output_path = Path.Combine(Path.GetTempPath(), 
                    $"video_{Guid.NewGuid()}.mp4")
            };
            
            try
            {
                // Call Python backend
                _currentVideoPath = await GenerateVideoAsync(request);
                
                // Load video
                VideoPlayer.Source = new Uri(_currentVideoPath);
                VideoPlayer.Play();
                
                StatusText.Text = "Video generated successfully!";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error generating video: {ex.Message}");
                StatusText.Text = "Generation failed.";
            }
            finally
            {
                ProgressBar.Visibility = Visibility.Collapsed;
            }
        }
        
        private async Task<string> GenerateVideoAsync(object request)
        {
            return await Task.Run(() =>
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = "python.exe",
                    Arguments = $"generate.py \"{JsonSerializer.Serialize(request)}\"",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = @"C:\VideoGenerator\backend"
                };
                
                using var process = Process.Start(startInfo);
                string output = process.StandardOutput.ReadToEnd();
                string error = process.StandardError.ReadToEnd();
                process.WaitForExit();
                
                if (process.ExitCode != 0)
                {
                    throw new Exception($"Python error: {error}");
                }
                
                var result = JsonSerializer.Deserialize<JsonElement>(output);
                return result.GetProperty("output").GetString();
            });
        }
        
        private void Play_Click(object sender, RoutedEventArgs e) 
            => VideoPlayer.Play();
        
        private void Pause_Click(object sender, RoutedEventArgs e) 
            => VideoPlayer.Pause();
        
        private void Stop_Click(object sender, RoutedEventArgs e)
        {
            VideoPlayer.Stop();
            VideoPlayer.Position = TimeSpan.Zero;
        }
        
        private void SaveAs_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentVideoPath))
            {
                MessageBox.Show("No video to save.");
                return;
            }
            
            var dialog = new SaveFileDialog
            {
                Filter = "MP4 Video (*.mp4)|*.mp4",
                FileName = $"generated_{DateTime.Now:yyyyMMdd_HHmmss}.mp4"
            };
            
            if (dialog.ShowDialog() == true)
            {
                File.Copy(_currentVideoPath, dialog.FileName, true);
                MessageBox.Show("Video saved successfully!");
            }
        }
    }
}
```

---

## 7. Installation Script

### 7.1 setup_environment.bat

```batch
@echo off
echo ====================================
echo Video Generator Setup
echo ====================================

:: Create directories
mkdir models
mkdir output
mkdir backend

:: Setup Python environment
echo Setting up Python environment...
python -m venv venv
call venv\Scripts\activate

:: Install PyTorch with CUDA
echo Installing PyTorch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

:: Install required packages
echo Installing dependencies...
pip install diffusers==0.24.0
pip install transformers==4.36.0
pip install accelerate==0.25.0
pip install safetensors==0.4.1
pip install opencv-python==4.8.1.78
pip install pillow==10.1.0
pip install xformers==0.0.23

:: Download models
echo Downloading models...
python download_models.py

echo.
echo Setup complete!
echo Run the application with: VideoGenerator.exe
pause
```

### 7.2 download_models.py

```python
from huggingface_hub import snapshot_download
import os

def download_models():
    models_dir = "./models"
    os.makedirs(models_dir, exist_ok=True)
    
    print("Downloading Stable Video Diffusion...")
    snapshot_download(
        repo_id="stabilityai/stable-video-diffusion-img2vid-xt",
        local_dir=os.path.join(models_dir, "svd-xt"),
        local_dir_use_symlinks=False,
        # No token needed for public models
    )
    
    print("Download complete!")

if __name__ == "__main__":
    download_models()
```

---

## 8. Quick Start Guide

### Step 1: Install Prerequisites
```
1. Install Python 3.10: https://www.python.org/downloads/
2. Install CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive
3. Install Visual Studio 2022 (for C# development)
```

### Step 2: Setup
```batch
1. Run setup_environment.bat
2. Wait for models to download (~10GB)
3. Build the WPF application in Visual Studio
```

### Step 3: Generate Videos
```
1. Launch VideoGenerator.exe
2. Load an image (drag-drop or browse)
3. Adjust settings (duration, FPS, motion intensity)
4. Click "Generate Video"
5. Wait 2-5 minutes depending on length
6. Preview and save your video
```

---

## 9. Performance Tips

**Faster Generation:**
- Use 512x512 resolution (fastest)
- Reduce inference steps to 15-20
- Use 8 FPS instead of 24
- Generate shorter videos (2-3 seconds)

**Higher Quality:**
- Use 1024x576 or higher resolution
- Increase inference steps to 40-50
- Use 24 FPS for smoother motion
- Adjust motion_bucket_id for desired effect

**VRAM Management:**
- Close other GPU-intensive applications
- Use decode_chunk_size=2 if running out of memory
- Enable model CPU offloading for longer videos

---

## 10. Troubleshooting

**Out of Memory Error:**
```python
# In generate.py, reduce these values:
decode_chunk_size = 2  # Instead of 4
num_frames = 50  # Instead of 100
```

**Slow Generation:**
- First run is slow (model loading)
- Subsequent runs are faster
- Consider using FP16 precision (already enabled)

**Video Quality Issues:**
- Increase num_inference_steps
- Try different motion_bucket_id values
- Use higher resolution source images

---

This gives you a complete, offline, unrestricted image-to-video generator running entirely on your local RTX 3060. The models run without any built-in filters, giving you full control over the generation process.

Would you like me to provide more details on any specific component or help with alternative model integrations?