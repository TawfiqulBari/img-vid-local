using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace VideoGenerator.Models
{
    /// <summary>
    /// CivitAI model information from catalog
    /// </summary>
    public class CivitAIModel
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("version")]
        public string Version { get; set; } = string.Empty;

        [JsonPropertyName("version_id")]
        public int VersionId { get; set; }

        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        [JsonPropertyName("style")]
        public string Style { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("nsfw_level")]
        public int NsfwLevel { get; set; }

        [JsonPropertyName("base_model")]
        public string BaseModel { get; set; } = string.Empty;

        [JsonPropertyName("file_size_mb")]
        public int FileSizeMb { get; set; }

        [JsonPropertyName("download_url")]
        public string DownloadUrl { get; set; } = string.Empty;

        [JsonPropertyName("tags")]
        public List<string> Tags { get; set; } = new();

        [JsonPropertyName("recommended_settings")]
        public RecommendedSettings? Settings { get; set; }

        [JsonPropertyName("pros")]
        public List<string> Pros { get; set; } = new();

        [JsonPropertyName("cons")]
        public List<string> Cons { get; set; } = new();

        /// <summary>
        /// Get display name with version
        /// </summary>
        public string DisplayName => $"{Name} {Version}";

        /// <summary>
        /// Get file size in GB
        /// </summary>
        public string FileSizeDisplay => $"{FileSizeMb / 1024.0:F2} GB";

        /// <summary>
        /// Get NSFW level description
        /// </summary>
        public string NsfwLevelDescription
        {
            get
            {
                return NsfwLevel switch
                {
                    >= 60 => "Very Explicit (May generate NSFW by default)",
                    >= 30 => "Moderate NSFW (Capable but controlled)",
                    >= 15 => "Light NSFW (Supports but requires prompting)",
                    _ => "Minimal NSFW"
                };
            }
        }

        /// <summary>
        /// Get type display name
        /// </summary>
        public string TypeDisplay
        {
            get
            {
                return Type switch
                {
                    "realistic" => "Photorealistic",
                    "anime" => "Anime/Illustration",
                    _ => Type
                };
            }
        }
    }

    /// <summary>
    /// Recommended generation settings for a model
    /// </summary>
    public class RecommendedSettings
    {
        [JsonPropertyName("sampler")]
        public string Sampler { get; set; } = string.Empty;

        [JsonPropertyName("steps")]
        public int Steps { get; set; }

        [JsonPropertyName("cfg_scale")]
        public double CfgScale { get; set; }

        [JsonPropertyName("clip_skip")]
        public int ClipSkip { get; set; }

        [JsonPropertyName("embeddings")]
        public List<string>? Embeddings { get; set; }
    }

    /// <summary>
    /// Models catalog
    /// </summary>
    public class ModelsCatalog
    {
        [JsonPropertyName("version")]
        public string Version { get; set; } = string.Empty;

        [JsonPropertyName("last_updated")]
        public string LastUpdated { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("models")]
        public List<CivitAIModel> Models { get; set; } = new();

        [JsonPropertyName("categories")]
        public Dictionary<string, ModelCategory> Categories { get; set; } = new();

        [JsonPropertyName("recommendations")]
        public Dictionary<string, int> Recommendations { get; set; } = new();

        [JsonPropertyName("notes")]
        public List<string> Notes { get; set; } = new();
    }

    /// <summary>
    /// Model category
    /// </summary>
    public class ModelCategory
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("models")]
        public List<int> Models { get; set; } = new();
    }

    /// <summary>
    /// Model download progress
    /// </summary>
    public class DownloadProgress
    {
        public int ModelId { get; set; }
        public string ModelName { get; set; } = string.Empty;
        public long BytesDownloaded { get; set; }
        public long TotalBytes { get; set; }
        public double PercentComplete => TotalBytes > 0 ? (BytesDownloaded / (double)TotalBytes) * 100 : 0;
        public string Status { get; set; } = "Downloading";
        public bool IsComplete { get; set; }
        public string? ErrorMessage { get; set; }

        public string ProgressDisplay => $"{BytesDownloaded / (1024 * 1024):F1} MB / {TotalBytes / (1024 * 1024):F1} MB ({PercentComplete:F1}%)";
    }
}
