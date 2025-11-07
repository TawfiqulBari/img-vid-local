using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using VideoGenerator.Models;

namespace VideoGenerator.Views
{
    /// <summary>
    /// Interaction logic for ModelBrowserWindow.xaml
    /// </summary>
    public partial class ModelBrowserWindow : Window
    {
        private ModelsCatalog? _catalog;
        private List<CivitAIModel> _displayedModels = new();
        private CivitAIModel? _selectedModel;
        private readonly string _catalogPath;
        private readonly string _modelsDir = @"D:\VideoGenerator\models";
        private readonly HttpClient _httpClient = new();
        private CancellationTokenSource? _downloadCancellation;

        public ModelBrowserWindow()
        {
            InitializeComponent();

            // Path to catalog
            _catalogPath = Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory,
                "..", "..", "..", "..", "backend", "models_catalog.json"
            );

            Loaded += ModelBrowserWindow_Loaded;
        }

        private async void ModelBrowserWindow_Loaded(object sender, RoutedEventArgs e)
        {
            await LoadCatalogAsync();
        }

        #region Catalog Loading

        private async Task LoadCatalogAsync()
        {
            try
            {
                StatusText.Text = "Loading models catalog...";

                if (!File.Exists(_catalogPath))
                {
                    MessageBox.Show(
                        $"Models catalog not found at:\n{_catalogPath}\n\n" +
                        "Please ensure backend files are accessible.",
                        "Catalog Not Found",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                    return;
                }

                string json = await File.ReadAllTextAsync(_catalogPath);
                _catalog = JsonSerializer.Deserialize<ModelsCatalog>(json);

                if (_catalog == null || _catalog.Models.Count == 0)
                {
                    MessageBox.Show(
                        "Failed to load models catalog or catalog is empty.",
                        "Error",
                        MessageBoxButton.OK,
                        MessageBoxImage.Error);
                    return;
                }

                // Display all models initially
                _displayedModels = _catalog.Models;
                ModelsListBox.ItemsSource = _displayedModels;

                StatusText.Text = $"Loaded {_catalog.Models.Count} models from catalog";
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Failed to load catalog:\n\n{ex.Message}",
                    "Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }

        #endregion

        #region Filtering

        private void FilterRadio_Checked(object sender, RoutedEventArgs e)
        {
            if (_catalog == null) return;

            if (sender == AllModelsRadio)
            {
                _displayedModels = _catalog.Models;
            }
            else if (sender == RealisticRadio)
            {
                _displayedModels = _catalog.Models.Where(m => m.Type == "realistic").ToList();
            }
            else if (sender == AnimeRadio)
            {
                _displayedModels = _catalog.Models.Where(m => m.Type == "anime").ToList();
            }

            ModelsListBox.ItemsSource = null;
            ModelsListBox.ItemsSource = _displayedModels;
            StatusText.Text = $"Showing {_displayedModels.Count} models";
        }

        private void FilterBestOverall_Click(object sender, RoutedEventArgs e)
        {
            if (_catalog == null) return;

            if (_catalog.Recommendations.TryGetValue("best_overall", out int modelId))
            {
                var model = _catalog.Models.FirstOrDefault(m => m.Id == modelId);
                if (model != null)
                {
                    _displayedModels = new List<CivitAIModel> { model };
                    ModelsListBox.ItemsSource = _displayedModels;
                    ModelsListBox.SelectedIndex = 0;
                    StatusText.Text = "Showing best overall model";
                }
            }
        }

        private void FilterBestNSFW_Click(object sender, RoutedEventArgs e)
        {
            if (_catalog == null) return;

            if (_catalog.Recommendations.TryGetValue("best_nsfw_realistic", out int modelId))
            {
                var model = _catalog.Models.FirstOrDefault(m => m.Id == modelId);
                if (model != null)
                {
                    _displayedModels = new List<CivitAIModel> { model };
                    ModelsListBox.ItemsSource = _displayedModels;
                    ModelsListBox.SelectedIndex = 0;
                    StatusText.Text = "Showing best NSFW model";
                }
            }
        }

        private void FilterBestAnime_Click(object sender, RoutedEventArgs e)
        {
            if (_catalog == null) return;

            if (_catalog.Recommendations.TryGetValue("best_anime", out int modelId))
            {
                var model = _catalog.Models.FirstOrDefault(m => m.Id == modelId);
                if (model != null)
                {
                    _displayedModels = new List<CivitAIModel> { model };
                    ModelsListBox.ItemsSource = _displayedModels;
                    ModelsListBox.SelectedIndex = 0;
                    StatusText.Text = "Showing best anime model";
                }
            }
        }

        #endregion

        #region Model Selection

        private void ModelsListBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (ModelsListBox.SelectedItem is CivitAIModel model)
            {
                _selectedModel = model;
                ShowModelDetails(model);
            }
        }

        private void ShowModelDetails(CivitAIModel model)
        {
            DetailsPanel.Visibility = Visibility.Visible;

            SelectedModelName.Text = model.DisplayName;
            ProsList.ItemsSource = model.Pros;
            ConsList.ItemsSource = model.Cons;
            DownloadSizeText.Text = $"~{model.FileSizeDisplay}";

            if (model.Settings != null)
            {
                RecommendedSettings.Text =
                    $"Sampler: {model.Settings.Sampler} | " +
                    $"Steps: {model.Settings.Steps} | " +
                    $"CFG: {model.Settings.CfgScale} | " +
                    $"CLIP Skip: {model.Settings.ClipSkip}";
            }
            else
            {
                RecommendedSettings.Text = "No recommended settings provided";
            }

            // Check if model is already downloaded
            string modelFileName = GetModelFileName(model);
            string modelPath = Path.Combine(_modelsDir, "custom", modelFileName);

            if (File.Exists(modelPath))
            {
                DownloadButton.Content = "✓ Already Downloaded";
                DownloadButton.Background = System.Windows.Media.Brushes.Gray;
                DownloadButton.IsEnabled = false;
            }
            else
            {
                DownloadButton.Content = "📥 Download Model";
                DownloadButton.Background = System.Windows.Media.Brushes.Green;
                DownloadButton.IsEnabled = true;
            }
        }

        private string GetModelFileName(CivitAIModel model)
        {
            // Generate safe filename from model name
            string safeName = string.Join("_", model.Name.Split(Path.GetInvalidFileNameChars()));
            return $"{safeName}_{model.VersionId}.safetensors";
        }

        #endregion

        #region Download

        private async void DownloadButton_Click(object sender, RoutedEventArgs e)
        {
            if (_selectedModel == null) return;

            var result = MessageBox.Show(
                $"Download {_selectedModel.DisplayName}?\n\n" +
                $"Size: ~{_selectedModel.FileSizeDisplay}\n" +
                $"NSFW Level: {_selectedModel.NsfwLevelDescription}\n\n" +
                "This may take 10-30 minutes depending on your internet speed.",
                "Confirm Download",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes) return;

            await DownloadModelAsync(_selectedModel);
        }

        private async Task DownloadModelAsync(CivitAIModel model)
        {
            try
            {
                // Ensure directory exists
                string customDir = Path.Combine(_modelsDir, "custom");
                Directory.CreateDirectory(customDir);

                string modelFileName = GetModelFileName(model);
                string outputPath = Path.Combine(customDir, modelFileName);

                // UI: downloading state
                DownloadButton.IsEnabled = false;
                DownloadProgress.Visibility = Visibility.Visible;
                DownloadProgressText.Visibility = Visibility.Visible;
                StatusText.Text = $"Downloading {model.Name}...";

                _downloadCancellation = new CancellationTokenSource();

                // Download with progress
                using var response = await _httpClient.GetAsync(
                    model.DownloadUrl,
                    HttpCompletionOption.ResponseHeadersRead,
                    _downloadCancellation.Token);

                response.EnsureSuccessStatusCode();

                long? totalBytes = response.Content.Headers.ContentLength;

                using var contentStream = await response.Content.ReadAsStreamAsync();
                using var fileStream = new FileStream(outputPath, FileMode.Create, FileAccess.Write, FileShare.None, 8192, true);

                byte[] buffer = new byte[8192];
                long totalRead = 0;
                int bytesRead;

                while ((bytesRead = await contentStream.ReadAsync(buffer, 0, buffer.Length, _downloadCancellation.Token)) > 0)
                {
                    await fileStream.WriteAsync(buffer, 0, bytesRead, _downloadCancellation.Token);
                    totalRead += bytesRead;

                    if (totalBytes.HasValue)
                    {
                        double percent = (totalRead / (double)totalBytes.Value) * 100;
                        DownloadProgress.Value = percent;
                        DownloadProgressText.Text = $"{totalRead / (1024 * 1024):F1} MB / {totalBytes.Value / (1024 * 1024):F1} MB ({percent:F1}%)";
                    }
                }

                // Success!
                DownloadButton.Content = "✓ Download Complete!";
                DownloadButton.Background = System.Windows.Media.Brushes.Green;
                StatusText.Text = $"Downloaded {model.Name} successfully!";

                MessageBox.Show(
                    $"{model.DisplayName} has been downloaded!\n\n" +
                    $"Location: {outputPath}\n\n" +
                    "The model will be available in the model selector after restarting the application.",
                    "Download Complete",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);
            }
            catch (OperationCanceledException)
            {
                StatusText.Text = "Download cancelled";
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Download failed:\n\n{ex.Message}",
                    "Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);

                StatusText.Text = "Download failed";
            }
            finally
            {
                DownloadProgress.Visibility = Visibility.Collapsed;
                DownloadProgressText.Visibility = Visibility.Collapsed;
                _downloadCancellation?.Dispose();
                _downloadCancellation = null;
            }
        }

        #endregion

        #region Buttons

        private void RefreshInstalled_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(
                "To see newly downloaded models, please restart the application.\n\n" +
                "The main window will automatically discover all .safetensors files in D:\\VideoGenerator\\models\\",
                "Restart Required",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        #endregion
    }
}
