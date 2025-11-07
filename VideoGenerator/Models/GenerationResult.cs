using System.Text.Json.Serialization;

namespace VideoGenerator.Models
{
    /// <summary>
    /// Result from video generation
    /// Deserialized from JSON response from Python backend
    /// </summary>
    public class GenerationResult
    {
        /// <summary>
        /// Whether generation succeeded
        /// </summary>
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        /// <summary>
        /// Path to output video (WSL format)
        /// </summary>
        [JsonPropertyName("output_path")]
        public string? OutputPath { get; set; }

        /// <summary>
        /// Path to output video (Windows format)
        /// </summary>
        [JsonPropertyName("output_path_windows")]
        public string? OutputPathWindows { get; set; }

        /// <summary>
        /// Number of frames generated
        /// </summary>
        [JsonPropertyName("num_frames")]
        public int NumFrames { get; set; }

        /// <summary>
        /// Video duration in seconds
        /// </summary>
        [JsonPropertyName("duration")]
        public double Duration { get; set; }

        /// <summary>
        /// Frames per second
        /// </summary>
        [JsonPropertyName("fps")]
        public int Fps { get; set; }

        /// <summary>
        /// Video resolution [width, height]
        /// </summary>
        [JsonPropertyName("resolution")]
        public int[]? Resolution { get; set; }

        /// <summary>
        /// Model name used
        /// </summary>
        [JsonPropertyName("model_name")]
        public string? ModelName { get; set; }

        /// <summary>
        /// Generation time in seconds
        /// </summary>
        [JsonPropertyName("generation_time")]
        public double GenerationTime { get; set; }

        /// <summary>
        /// Error message if failed
        /// </summary>
        [JsonPropertyName("error")]
        public string? Error { get; set; }

        /// <summary>
        /// Additional metadata
        /// </summary>
        [JsonPropertyName("metadata")]
        public Dictionary<string, object>? Metadata { get; set; }

        /// <summary>
        /// Get resolution as string (e.g., "1024x576")
        /// </summary>
        public string ResolutionString
        {
            get
            {
                if (Resolution != null && Resolution.Length >= 2)
                    return $"{Resolution[0]}x{Resolution[1]}";
                return "Unknown";
            }
        }

        /// <summary>
        /// Get formatted generation time
        /// </summary>
        public string FormattedGenerationTime
        {
            get
            {
                if (GenerationTime < 60)
                    return $"{GenerationTime:F1}s";
                else
                {
                    var minutes = (int)(GenerationTime / 60);
                    var seconds = GenerationTime % 60;
                    return $"{minutes}m {seconds:F0}s";
                }
            }
        }

        /// <summary>
        /// Get summary string
        /// </summary>
        public string GetSummary()
        {
            if (!Success)
                return $"Failed: {Error}";

            return $"Success! Generated {NumFrames} frames ({Duration:F2}s @ {Fps} FPS) " +
                   $"at {ResolutionString} in {FormattedGenerationTime}";
        }
    }

    /// <summary>
    /// Model information from backend
    /// </summary>
    public class ModelInfo
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("path")]
        public string Path { get; set; } = string.Empty;

        [JsonPropertyName("size_mb")]
        public double SizeMb { get; set; }

        [JsonPropertyName("metadata")]
        public Dictionary<string, object>? Metadata { get; set; }

        public override string ToString()
        {
            return $"{Name} - {Description}";
        }
    }

    /// <summary>
    /// Response from list models command
    /// </summary>
    public class ListModelsResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("models")]
        public List<ModelInfo> Models { get; set; } = new();

        [JsonPropertyName("count")]
        public int Count { get; set; }
    }

    /// <summary>
    /// VRAM statistics
    /// </summary>
    public class VramStats
    {
        [JsonPropertyName("total_gb")]
        public double TotalGb { get; set; }

        [JsonPropertyName("used_gb")]
        public double UsedGb { get; set; }

        [JsonPropertyName("available_gb")]
        public double AvailableGb { get; set; }

        [JsonPropertyName("percent_used")]
        public double PercentUsed { get; set; }

        public string GetSummary()
        {
            return $"VRAM: {UsedGb:F2}GB / {TotalGb:F2}GB ({PercentUsed:F1}% used, {AvailableGb:F2}GB available)";
        }
    }

    /// <summary>
    /// Response from VRAM stats command
    /// </summary>
    public class VramStatsResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("vram")]
        public VramStats? Vram { get; set; }
    }
}
