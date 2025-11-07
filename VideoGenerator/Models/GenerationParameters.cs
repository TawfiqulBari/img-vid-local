using System.IO;
using System.Text.Json.Serialization;

namespace VideoGenerator.Models
{
    /// <summary>
    /// Parameters for video generation
    /// Serialized to JSON and passed to Python backend
    /// </summary>
    public class GenerationParameters
    {
        /// <summary>
        /// Path to input image (REQUIRED)
        /// </summary>
        [JsonPropertyName("image_path")]
        public string ImagePath { get; set; } = string.Empty;

        /// <summary>
        /// Text prompt describing desired video (REQUIRED)
        /// </summary>
        [JsonPropertyName("prompt")]
        public string Prompt { get; set; } = string.Empty;

        /// <summary>
        /// Negative prompt (optional)
        /// </summary>
        [JsonPropertyName("negative_prompt")]
        public string? NegativePrompt { get; set; }

        /// <summary>
        /// Model to use (e.g., "svd-xt", "animatediff-realisticVision_v51")
        /// </summary>
        [JsonPropertyName("model_name")]
        public string ModelName { get; set; } = "svd-xt";

        /// <summary>
        /// Number of frames to generate
        /// </summary>
        [JsonPropertyName("num_frames")]
        public int NumFrames { get; set; } = 25;

        /// <summary>
        /// Frames per second
        /// </summary>
        [JsonPropertyName("fps")]
        public int Fps { get; set; } = 8;

        /// <summary>
        /// Output video width (must be divisible by 8)
        /// </summary>
        [JsonPropertyName("width")]
        public int Width { get; set; } = 1024;

        /// <summary>
        /// Output video height (must be divisible by 8)
        /// </summary>
        [JsonPropertyName("height")]
        public int Height { get; set; } = 576;

        /// <summary>
        /// Random seed (-1 for random)
        /// </summary>
        [JsonPropertyName("seed")]
        public int Seed { get; set; } = -1;

        /// <summary>
        /// Output video path (optional, auto-generated if not provided)
        /// </summary>
        [JsonPropertyName("output_path")]
        public string? OutputPath { get; set; }

        // SVD-specific parameters

        /// <summary>
        /// Motion intensity for SVD (1-255, default 127)
        /// </summary>
        [JsonPropertyName("motion_bucket_id")]
        public int? MotionBucketId { get; set; }

        /// <summary>
        /// Noise augmentation strength for SVD (0.0-0.1)
        /// </summary>
        [JsonPropertyName("noise_aug_strength")]
        public double? NoiseAugStrength { get; set; }

        /// <summary>
        /// Decode chunk size for VRAM management (2-8)
        /// </summary>
        [JsonPropertyName("decode_chunk_size")]
        public int? DecodeChunkSize { get; set; }

        // AnimateDiff-specific parameters

        /// <summary>
        /// Guidance scale for AnimateDiff (1.0-20.0)
        /// </summary>
        [JsonPropertyName("guidance_scale")]
        public double? GuidanceScale { get; set; }

        /// <summary>
        /// Number of inference steps (15-50)
        /// </summary>
        [JsonPropertyName("num_inference_steps")]
        public int? NumInferenceSteps { get; set; }

        /// <summary>
        /// CLIP skip layers (1-3)
        /// </summary>
        [JsonPropertyName("clip_skip")]
        public int? ClipSkip { get; set; }

        /// <summary>
        /// Get default parameters for SVD pipeline
        /// </summary>
        public static GenerationParameters GetSvdDefaults()
        {
            return new GenerationParameters
            {
                ModelName = "svd-xt",
                NumFrames = 25,
                Fps = 8,
                Width = 1024,
                Height = 576,
                MotionBucketId = 127,
                NoiseAugStrength = 0.02,
                DecodeChunkSize = 4
            };
        }

        /// <summary>
        /// Get default parameters for AnimateDiff pipeline
        /// </summary>
        public static GenerationParameters GetAnimateDiffDefaults()
        {
            return new GenerationParameters
            {
                ModelName = "animatediff-realisticVision_v51",
                NumFrames = 24,
                Fps = 16,
                Width = 512,
                Height = 512,
                GuidanceScale = 7.5,
                NumInferenceSteps = 25,
                ClipSkip = 1
            };
        }

        /// <summary>
        /// Validate parameters
        /// </summary>
        public (bool IsValid, string? ErrorMessage) Validate()
        {
            if (string.IsNullOrWhiteSpace(ImagePath))
                return (false, "Image path is required");

            if (!File.Exists(ImagePath))
                return (false, $"Image file not found: {ImagePath}");

            if (string.IsNullOrWhiteSpace(Prompt))
                return (false, "Prompt is required and cannot be empty");

            if (Prompt.Length < 3)
                return (false, "Prompt must be at least 3 characters");

            if (NumFrames < 1 || NumFrames > 250)
                return (false, "Number of frames must be between 1 and 250");

            if (Fps < 1 || Fps > 60)
                return (false, "FPS must be between 1 and 60");

            if (Width < 64 || Width > 2048 || Width % 8 != 0)
                return (false, "Width must be between 64 and 2048 and divisible by 8");

            if (Height < 64 || Height > 2048 || Height % 8 != 0)
                return (false, "Height must be between 64 and 2048 and divisible by 8");

            return (true, null);
        }
    }
}
