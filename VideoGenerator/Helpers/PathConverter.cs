using System.Linq;

namespace VideoGenerator.Helpers
{
    /// <summary>
    /// Converts paths between Windows and WSL formats
    ///
    /// Windows: D:\VideoGenerator\models
    /// WSL:     /mnt/d/VideoGenerator/models
    /// </summary>
    public static class PathConverter
    {
        /// <summary>
        /// Convert Windows path to WSL path
        /// Example: D:\VideoGenerator\models -> /mnt/d/VideoGenerator/models
        /// </summary>
        /// <param name="windowsPath">Windows-style path</param>
        /// <returns>WSL-style path</returns>
        public static string WindowsToWsl(string windowsPath)
        {
            if (string.IsNullOrWhiteSpace(windowsPath))
                return windowsPath;

            // Normalize backslashes to forward slashes
            string path = windowsPath.Replace('\\', '/');

            // Remove trailing slashes
            path = path.TrimEnd('/');

            // Check if it's a drive letter path (e.g., D:/ or D:\)
            if (path.Length >= 2 && path[1] == ':')
            {
                char drive = char.ToLower(path[0]);
                string rest = path.Length > 2 ? path.Substring(2) : string.Empty;

                // Remove leading slash if present
                if (rest.StartsWith("/"))
                    rest = rest.Substring(1);

                return string.IsNullOrEmpty(rest)
                    ? $"/mnt/{drive}"
                    : $"/mnt/{drive}/{rest}";
            }

            // Already a WSL path or relative path
            return path;
        }

        /// <summary>
        /// Convert WSL path to Windows path
        /// Example: /mnt/d/VideoGenerator/models -> D:\VideoGenerator\models
        /// </summary>
        /// <param name="wslPath">WSL-style path</param>
        /// <returns>Windows-style path</returns>
        public static string WslToWindows(string wslPath)
        {
            if (string.IsNullOrWhiteSpace(wslPath))
                return wslPath;

            // Check if it's a /mnt/ path
            if (wslPath.StartsWith("/mnt/"))
            {
                // Split: /mnt/d/path/to/file -> ['', 'mnt', 'd', 'path', 'to', 'file']
                string[] parts = wslPath.Split('/');

                if (parts.Length >= 3)
                {
                    char drive = char.ToUpper(parts[2][0]);
                    string rest = parts.Length > 3
                        ? string.Join('\\', parts.Skip(3))
                        : string.Empty;

                    return string.IsNullOrEmpty(rest)
                        ? $"{drive}:\\"
                        : $"{drive}:\\{rest}";
                }
            }

            // Already a Windows path or relative path
            return wslPath.Replace('/', '\\');
        }

        /// <summary>
        /// Check if path is in WSL format
        /// </summary>
        public static bool IsWslPath(string path)
        {
            return !string.IsNullOrWhiteSpace(path) && path.StartsWith("/mnt/");
        }

        /// <summary>
        /// Check if path is in Windows format
        /// </summary>
        public static bool IsWindowsPath(string path)
        {
            return !string.IsNullOrWhiteSpace(path) &&
                   path.Length >= 2 &&
                   path[1] == ':';
        }

        /// <summary>
        /// Normalize path for current system (Windows)
        /// </summary>
        public static string Normalize(string path)
        {
            if (IsWslPath(path))
                return WslToWindows(path);

            return path.Replace('/', '\\');
        }
    }
}
