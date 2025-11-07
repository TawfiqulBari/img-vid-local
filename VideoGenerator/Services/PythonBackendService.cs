using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using VideoGenerator.Helpers;
using VideoGenerator.Models;

namespace VideoGenerator.Services
{
    /// <summary>
    /// Service for communicating with Python backend
    /// Spawns Python process and exchanges JSON data
    /// </summary>
    public class PythonBackendService
    {
        private readonly string _pythonExecutable;
        private readonly string _generateScriptPath;
        private readonly string _backendDir;

        /// <summary>
        /// Initialize Python backend service
        /// </summary>
        /// <param name="pythonExecutable">Path to Python executable (default: looks for WSL python or venv)</param>
        /// <param name="backendDir">Path to backend directory</param>
        public PythonBackendService(
            string? pythonExecutable = null,
            string? backendDir = null)
        {
            // Find backend directory (works in both dev and deployed environments)
            _backendDir = backendDir ?? FindBackendDirectory();

            _generateScriptPath = Path.Combine(_backendDir, "generate.py");

            // Validate paths
            if (!File.Exists(_generateScriptPath))
            {
                throw new FileNotFoundException(
                    $"Python backend script not found: {_generateScriptPath}");
            }

            // Default to WSL python in virtual environment
            _pythonExecutable = pythonExecutable ?? FindPythonExecutable();
        }

        /// <summary>
        /// Find backend directory (works in both development and deployed environments)
        /// </summary>
        private string FindBackendDirectory()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;

            // Try development structure first: bin/Debug/net6.0-windows/../../../../backend
            string devPath = Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "..", "backend"));
            if (Directory.Exists(devPath) && Directory.Exists(Path.Combine(devPath, "venv")))
                return devPath;

            // For deployed/portable: Use WSL backend directory where venv exists
            // Check common WSL user paths
            string wslUsername = Environment.UserName.ToLower();
            string[] wslPaths = new[]
            {
                $@"\\wsl$\Ubuntu\home\{wslUsername}\personal-projects\image-video-3\backend",
                $@"\\wsl$\Ubuntu-22.04\home\{wslUsername}\personal-projects\image-video-3\backend",
                @"\\wsl$\Ubuntu\home\tawfiq\personal-projects\image-video-3\backend",
                @"\\wsl$\Ubuntu-22.04\home\tawfiq\personal-projects\image-video-3\backend"
            };

            foreach (var wslPath in wslPaths)
            {
                if (Directory.Exists(wslPath) && Directory.Exists(Path.Combine(wslPath, "venv")))
                    return wslPath;
            }

            // Fallback: try deployed structure (though it won't have venv)
            string deployedPath = Path.GetFullPath(Path.Combine(baseDir, "..", "backend"));
            if (Directory.Exists(deployedPath))
                return deployedPath;

            // Last resort: return first WSL path (will fail validation later)
            return wslPaths[0];
        }

        /// <summary>
        /// Find Python executable (use WSL)
        /// </summary>
        private string FindPythonExecutable()
        {
            // Always use WSL since Python backend is in WSL environment
            return "wsl.exe";
        }

        /// <summary>
        /// Generate video using Python backend
        /// </summary>
        /// <param name="parameters">Generation parameters</param>
        /// <param name="progressCallback">Optional progress callback</param>
        /// <param name="cancellationToken">Cancellation token</param>
        /// <returns>Generation result</returns>
        public async Task<GenerationResult> GenerateVideoAsync(
            GenerationParameters parameters,
            Action<string>? progressCallback = null,
            CancellationToken cancellationToken = default)
        {
            // Validate parameters
            var (isValid, errorMessage) = parameters.Validate();
            if (!isValid)
            {
                return new GenerationResult
                {
                    Success = false,
                    Error = errorMessage
                };
            }

            // Convert Windows paths to WSL
            var paramsForBackend = PrepareParametersForBackend(parameters);

            // Serialize to JSON
            string jsonParams = JsonSerializer.Serialize(paramsForBackend, new JsonSerializerOptions
            {
                WriteIndented = false
            });

            // Build command - use relative path since we cd into backend directory
            string arguments = $"generate.py '{jsonParams}'";

            progressCallback?.Invoke("Starting Python backend...");

            try
            {
                // Run Python process
                var result = await RunPythonProcessAsync(
                    arguments,
                    progressCallback,
                    cancellationToken);

                // Parse response
                var generationResult = JsonSerializer.Deserialize<GenerationResult>(result);

                if (generationResult == null)
                {
                    return new GenerationResult
                    {
                        Success = false,
                        Error = "Failed to parse response from backend"
                    };
                }

                progressCallback?.Invoke("Generation complete!");

                return generationResult;
            }
            catch (OperationCanceledException)
            {
                return new GenerationResult
                {
                    Success = false,
                    Error = "Generation cancelled by user"
                };
            }
            catch (Exception ex)
            {
                return new GenerationResult
                {
                    Success = false,
                    Error = $"Backend error: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// List available models
        /// </summary>
        public async Task<ListModelsResponse> ListModelsAsync()
        {
            try
            {
                // Use relative path since we cd into backend directory
                string arguments = "generate.py --list-models";
                string result = await RunPythonProcessAsync(arguments);

                var response = JsonSerializer.Deserialize<ListModelsResponse>(result);
                return response ?? new ListModelsResponse { Success = false };
            }
            catch (Exception ex)
            {
                return new ListModelsResponse
                {
                    Success = false,
                    Models = new List<ModelInfo>()
                };
            }
        }

        /// <summary>
        /// Get VRAM statistics
        /// </summary>
        public async Task<VramStatsResponse> GetVramStatsAsync()
        {
            try
            {
                // Use relative path since we cd into backend directory
                string arguments = "generate.py --vram-stats";
                string result = await RunPythonProcessAsync(arguments);

                var response = JsonSerializer.Deserialize<VramStatsResponse>(result);
                return response ?? new VramStatsResponse { Success = false };
            }
            catch (Exception ex)
            {
                return new VramStatsResponse
                {
                    Success = false,
                    Vram = null
                };
            }
        }

        /// <summary>
        /// Prepare parameters for backend (convert paths to WSL)
        /// </summary>
        private GenerationParameters PrepareParametersForBackend(GenerationParameters parameters)
        {
            var prepared = new GenerationParameters
            {
                ImagePath = PathConverter.WindowsToWsl(parameters.ImagePath),
                Prompt = parameters.Prompt,
                NegativePrompt = parameters.NegativePrompt,
                ModelName = parameters.ModelName,
                NumFrames = parameters.NumFrames,
                Fps = parameters.Fps,
                Width = parameters.Width,
                Height = parameters.Height,
                Seed = parameters.Seed,
                MotionBucketId = parameters.MotionBucketId,
                NoiseAugStrength = parameters.NoiseAugStrength,
                DecodeChunkSize = parameters.DecodeChunkSize,
                GuidanceScale = parameters.GuidanceScale,
                NumInferenceSteps = parameters.NumInferenceSteps,
                ClipSkip = parameters.ClipSkip
            };

            if (!string.IsNullOrEmpty(parameters.OutputPath))
            {
                prepared.OutputPath = PathConverter.WindowsToWsl(parameters.OutputPath);
            }

            return prepared;
        }

        /// <summary>
        /// Run Python process and capture output
        /// </summary>
        private async Task<string> RunPythonProcessAsync(
            string arguments,
            Action<string>? progressCallback = null,
            CancellationToken cancellationToken = default)
        {
            // Convert Windows backend path to WSL path
            string wslBackendPath = PathConverter.WindowsToWsl(_backendDir);

            // Build WSL command to activate venv and run Python
            string wslCommand = $"bash -c \"cd {wslBackendPath} && source venv/bin/activate && python {arguments}\"";

            var startInfo = new ProcessStartInfo
            {
                FileName = _pythonExecutable, // wsl.exe
                Arguments = wslCommand,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = new Process { StartInfo = startInfo };

            var outputBuilder = new StringBuilder();
            var errorBuilder = new StringBuilder();

            process.OutputDataReceived += (sender, args) =>
            {
                if (args.Data != null)
                {
                    outputBuilder.AppendLine(args.Data);
                    progressCallback?.Invoke(args.Data);
                }
            };

            process.ErrorDataReceived += (sender, args) =>
            {
                if (args.Data != null)
                {
                    errorBuilder.AppendLine(args.Data);
                    progressCallback?.Invoke($"[Error] {args.Data}");
                }
            };

            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            // Wait for process to complete or cancellation
            await Task.Run(() =>
            {
                while (!process.WaitForExit(100))
                {
                    if (cancellationToken.IsCancellationRequested)
                    {
                        process.Kill();
                        throw new OperationCanceledException();
                    }
                }
            }, cancellationToken);

            string output = outputBuilder.ToString();
            string error = errorBuilder.ToString();

            if (process.ExitCode != 0)
            {
                throw new Exception(
                    $"Python process failed with exit code {process.ExitCode}\n" +
                    $"Error: {error}"
                );
            }

            // Return the last line (JSON response)
            var lines = output.Split('\n', StringSplitOptions.RemoveEmptyEntries);
            string jsonResponse = lines.LastOrDefault() ?? "{}";

            return jsonResponse;
        }

        /// <summary>
        /// Check if Python backend is available
        /// </summary>
        public async Task<bool> CheckBackendAvailableAsync()
        {
            try
            {
                var response = await ListModelsAsync();
                return response.Success;
            }
            catch
            {
                return false;
            }
        }
    }
}
