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
            // Default to WSL python in virtual environment
            _pythonExecutable = pythonExecutable ?? FindPythonExecutable();

            // Default to backend directory in project
            _backendDir = backendDir ?? Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory,
                "..", "..", "..", "..", "backend"
            );

            _generateScriptPath = Path.Combine(_backendDir, "generate.py");

            // Validate paths
            if (!File.Exists(_generateScriptPath))
            {
                throw new FileNotFoundException(
                    $"Python backend script not found: {_generateScriptPath}");
            }
        }

        /// <summary>
        /// Find Python executable (prefer venv, fallback to system)
        /// </summary>
        private string FindPythonExecutable()
        {
            // Try venv first
            string venvPython = Path.Combine(_backendDir, "venv", "bin", "python");
            if (File.Exists(venvPython))
                return venvPython;

            // Fallback to system python3
            return "python3";
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

            // Build command
            string arguments = $"\"{_generateScriptPath}\" '{jsonParams}'";

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
                string arguments = $"\"{_generateScriptPath}\" --list-models";
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
                string arguments = $"\"{_generateScriptPath}\" --vram-stats";
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
            var startInfo = new ProcessStartInfo
            {
                FileName = _pythonExecutable,
                Arguments = arguments,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = _backendDir
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
