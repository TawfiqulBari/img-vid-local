using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using Microsoft.Win32;
using VideoGenerator.Models;
using VideoGenerator.Services;
using VideoGenerator.Helpers;

namespace VideoGenerator
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private readonly PythonBackendService _backendService;
        private CancellationTokenSource? _cancellationTokenSource;
        private DispatcherTimer? _videoTimer;
        private List<ModelInfo> _availableModels = new();

        public MainWindow()
        {
            InitializeComponent();

            // Initialize backend service
            _backendService = new PythonBackendService();

            // Initialize UI
            Loaded += MainWindow_Loaded;
        }

        private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            SetStatus("Initializing...");

            // Check if backend is available
            bool backendAvailable = await _backendService.CheckBackendAvailableAsync();

            if (!backendAvailable)
            {
                MessageBox.Show(
                    "Python backend is not available.\n\n" +
                    "Please ensure:\n" +
                    "1. Python 3.10 is installed in WSL\n" +
                    "2. Virtual environment is activated\n" +
                    "3. All dependencies are installed\n" +
                    "4. Models are downloaded\n\n" +
                    "Run: bash scripts/setup_wsl.sh\n" +
                    "Then: python backend/download_models.py",
                    "Backend Not Available",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
            }

            // Load models
            await RefreshModelsAsync();

            SetStatus("Ready");
        }

        #region Image Selection

        private void BrowseImage_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Title = "Select Input Image",
                Filter = "Image Files (*.jpg;*.jpeg;*.png;*.webp)|*.jpg;*.jpeg;*.png;*.webp|All Files (*.*)|*.*",
                CheckFileExists = true
            };

            if (dialog.ShowDialog() == true)
            {
                ImagePathTextBox.Text = dialog.FileName;

                // Show preview
                try
                {
                    var bitmap = new BitmapImage(new Uri(dialog.FileName));
                    PreviewImage.Source = bitmap;
                    PreviewImage.Visibility = Visibility.Visible;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Failed to load image: {ex.Message}", "Error",
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        #endregion

        #region Model Management

        private async void RefreshModels_Click(object sender, RoutedEventArgs e)
        {
            await RefreshModelsAsync();
        }

        private async Task RefreshModelsAsync()
        {
            SetStatus("Loading models...");

            try
            {
                var response = await _backendService.ListModelsAsync();

                if (response.Success && response.Models.Count > 0)
                {
                    _availableModels = response.Models;

                    ModelComboBox.Items.Clear();

                    foreach (var model in _availableModels)
                    {
                        ModelComboBox.Items.Add(model);
                    }

                    ModelComboBox.SelectedIndex = 0;

                    SetStatus($"Loaded {_availableModels.Count} model(s)");
                }
                else
                {
                    MessageBox.Show(
                        "No models found.\n\n" +
                        "Please download models first:\n" +
                        "python backend/download_models.py",
                        "No Models",
                        MessageBoxButton.OK,
                        MessageBoxImage.Information);

                    SetStatus("No models available");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to load models: {ex.Message}", "Error",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ModelComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (ModelComboBox.SelectedItem is ModelInfo model)
            {
                // Show/hide pipeline-specific parameters
                bool isSvd = model.Type == "svd";
                bool isAnimateDiff = model.Type == "animatediff";

                SvdParametersGroup.Visibility = isSvd ? Visibility.Visible : Visibility.Collapsed;
                AnimateDiffParametersGroup.Visibility = isAnimateDiff ? Visibility.Visible : Visibility.Collapsed;

                // Update default values based on model type
                if (isSvd)
                {
                    NumFramesSlider.Value = 25;
                    FpsSlider.Value = 8;
                    ResolutionComboBox.SelectedIndex = 1; // 1024x576
                }
                else if (isAnimateDiff)
                {
                    NumFramesSlider.Value = 24;
                    FpsSlider.Value = 16;
                    ResolutionComboBox.SelectedIndex = 0; // 512x512
                }
            }
        }

        #endregion

        #region Video Generation

        private async void Generate_Click(object sender, RoutedEventArgs e)
        {
            // Validate inputs
            if (string.IsNullOrWhiteSpace(ImagePathTextBox.Text) ||
                ImagePathTextBox.Text == "No image selected")
            {
                MessageBox.Show("Please select an input image.", "Missing Input",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (string.IsNullOrWhiteSpace(PromptTextBox.Text))
            {
                MessageBox.Show("Prompt is required.\n\nPlease describe the desired video.",
                    "Missing Prompt", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (ModelComboBox.SelectedItem == null)
            {
                MessageBox.Show("Please select a model.", "Missing Model",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            // Get selected model
            var model = (ModelInfo)ModelComboBox.SelectedItem;

            // Get resolution
            var resolutionTag = ((ComboBoxItem)ResolutionComboBox.SelectedItem).Tag.ToString();
            var resolutionParts = resolutionTag!.Split(',');
            int width = int.Parse(resolutionParts[0]);
            int height = int.Parse(resolutionParts[1]);

            // Build parameters
            var parameters = new GenerationParameters
            {
                ImagePath = ImagePathTextBox.Text,
                Prompt = PromptTextBox.Text.Trim(),
                NegativePrompt = string.IsNullOrWhiteSpace(NegativePromptTextBox.Text)
                    ? null : NegativePromptTextBox.Text.Trim(),
                ModelName = model.Name,
                NumFrames = (int)NumFramesSlider.Value,
                Fps = (int)FpsSlider.Value,
                Width = width,
                Height = height,
                Seed = int.TryParse(SeedTextBox.Text, out int seed) ? seed : -1
            };

            // Add pipeline-specific parameters
            if (model.Type == "svd")
            {
                parameters.MotionBucketId = (int)MotionBucketSlider.Value;

                int chunkSizeIndex = DecodeChunkSizeComboBox.SelectedIndex;
                parameters.DecodeChunkSize = chunkSizeIndex == 0 ? 2 : (chunkSizeIndex == 1 ? 4 : 8);
            }
            else if (model.Type == "animatediff")
            {
                parameters.GuidanceScale = GuidanceScaleSlider.Value;
                parameters.NumInferenceSteps = (int)InferenceStepsSlider.Value;
            }

            // Validate
            var (isValid, errorMessage) = parameters.Validate();
            if (!isValid)
            {
                MessageBox.Show(errorMessage, "Invalid Parameters",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            // Start generation
            await StartGenerationAsync(parameters);
        }

        private async Task StartGenerationAsync(GenerationParameters parameters)
        {
            // UI state: generating
            GenerateButton.IsEnabled = false;
            CancelButton.Visibility = Visibility.Visible;
            ProgressBar.Visibility = Visibility.Visible;
            ProgressBar.IsIndeterminate = true;

            // Create cancellation token
            _cancellationTokenSource = new CancellationTokenSource();

            try
            {
                SetStatus("Starting generation...");

                // Generate video
                var result = await _backendService.GenerateVideoAsync(
                    parameters,
                    progressCallback: (message) =>
                    {
                        Dispatcher.Invoke(() => SetStatus(message));
                    },
                    cancellationToken: _cancellationTokenSource.Token
                );

                if (result.Success)
                {
                    // Success!
                    SetStatus("Generation complete!");

                    OutputInfoTextBlock.Text = result.GetSummary();
                    OpenOutputButton.Visibility = Visibility.Visible;

                    // Load video for preview
                    if (!string.IsNullOrEmpty(result.OutputPathWindows))
                    {
                        LoadVideoPreview(result.OutputPathWindows);
                    }

                    MessageBox.Show(
                        $"Video generated successfully!\n\n" +
                        $"Frames: {result.NumFrames}\n" +
                        $"Duration: {result.Duration:F2}s @ {result.Fps} FPS\n" +
                        $"Resolution: {result.ResolutionString}\n" +
                        $"Time: {result.FormattedGenerationTime}\n\n" +
                        $"Output: {result.OutputPathWindows}",
                        "Success",
                        MessageBoxButton.OK,
                        MessageBoxImage.Information);
                }
                else
                {
                    // Failed
                    SetStatus("Generation failed");

                    MessageBox.Show(
                        $"Generation failed:\n\n{result.Error}",
                        "Error",
                        MessageBoxButton.OK,
                        MessageBoxImage.Error);
                }
            }
            catch (OperationCanceledException)
            {
                SetStatus("Generation cancelled");
            }
            catch (Exception ex)
            {
                SetStatus("Generation failed");

                MessageBox.Show(
                    $"An error occurred:\n\n{ex.Message}",
                    "Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
            finally
            {
                // UI state: ready
                GenerateButton.IsEnabled = true;
                CancelButton.Visibility = Visibility.Collapsed;
                ProgressBar.Visibility = Visibility.Collapsed;
                ProgressBar.IsIndeterminate = false;

                _cancellationTokenSource?.Dispose();
                _cancellationTokenSource = null;
            }
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            _cancellationTokenSource?.Cancel();
            SetStatus("Cancelling...");
        }

        #endregion

        #region Video Preview

        private void LoadVideoPreview(string videoPath)
        {
            try
            {
                VideoPlayer.Source = new Uri(videoPath);
                VideoPlayer.Play();

                PlaceholderText.Visibility = Visibility.Collapsed;
                VideoControlsPanel.Visibility = Visibility.Visible;

                // Setup timer for position update
                _videoTimer = new DispatcherTimer();
                _videoTimer.Interval = TimeSpan.FromMilliseconds(100);
                _videoTimer.Tick += VideoTimer_Tick;
                _videoTimer.Start();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to load video: {ex.Message}", "Error",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void VideoTimer_Tick(object? sender, EventArgs e)
        {
            if (VideoPlayer.NaturalDuration.HasTimeSpan)
            {
                var position = VideoPlayer.Position.TotalSeconds;
                var duration = VideoPlayer.NaturalDuration.TimeSpan.TotalSeconds;

                if (duration > 0)
                {
                    VideoPositionSlider.Value = (position / duration) * 100;
                }
            }
        }

        private void PlayVideo_Click(object sender, RoutedEventArgs e)
        {
            VideoPlayer.Play();
        }

        private void PauseVideo_Click(object sender, RoutedEventArgs e)
        {
            VideoPlayer.Pause();
        }

        private void StopVideo_Click(object sender, RoutedEventArgs e)
        {
            VideoPlayer.Stop();
        }

        private void VideoPositionSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (VideoPlayer.NaturalDuration.HasTimeSpan)
            {
                var duration = VideoPlayer.NaturalDuration.TimeSpan.TotalSeconds;
                var newPosition = (VideoPositionSlider.Value / 100) * duration;
                VideoPlayer.Position = TimeSpan.FromSeconds(newPosition);
            }
        }

        private void VideoPlayer_MediaEnded(object sender, RoutedEventArgs e)
        {
            VideoPlayer.Position = TimeSpan.Zero;
        }

        #endregion

        #region Utility Functions

        private void BrowseCivitAI_Click(object sender, RoutedEventArgs e)
        {
            var browserWindow = new Views.ModelBrowserWindow();
            browserWindow.ShowDialog();
        }

        private async void CheckVram_Click(object sender, RoutedEventArgs e)
        {
            SetStatus("Checking VRAM...");

            try
            {
                var response = await _backendService.GetVramStatsAsync();

                if (response.Success && response.Vram != null)
                {
                    MessageBox.Show(
                        response.Vram.GetSummary(),
                        "VRAM Statistics",
                        MessageBoxButton.OK,
                        MessageBoxImage.Information);
                }
                else
                {
                    MessageBox.Show(
                        "Failed to get VRAM statistics.\n\n" +
                        "Make sure CUDA is available.",
                        "Error",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to check VRAM: {ex.Message}", "Error",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }

            SetStatus("Ready");
        }

        private void OpenOutput_Click(object sender, RoutedEventArgs e)
        {
            string outputDir = @"D:\VideoGenerator\output";

            if (Directory.Exists(outputDir))
            {
                System.Diagnostics.Process.Start("explorer.exe", outputDir);
            }
            else
            {
                MessageBox.Show($"Output directory not found: {outputDir}", "Error",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void Slider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (!IsLoaded) return;

            // Update slider value displays
            if (sender == NumFramesSlider)
                NumFramesValue.Text = ((int)NumFramesSlider.Value).ToString();
            else if (sender == FpsSlider)
                FpsValue.Text = ((int)FpsSlider.Value).ToString();
            else if (sender == MotionBucketSlider)
                MotionBucketValue.Text = ((int)MotionBucketSlider.Value).ToString();
            else if (sender == GuidanceScaleSlider)
                GuidanceScaleValue.Text = GuidanceScaleSlider.Value.ToString("F1");
            else if (sender == InferenceStepsSlider)
                InferenceStepsValue.Text = ((int)InferenceStepsSlider.Value).ToString();
        }

        private void SetStatus(string message)
        {
            StatusText.Text = message;
        }

        #endregion
    }
}
