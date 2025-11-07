; Image-to-Video Generator - Inno Setup Installer Script
; ======================================================
;
; This script creates a Windows installer for the Image-to-Video Generator.
;
; Requirements:
;   - Inno Setup 6.0 or later (https://jrsoftware.org/isinfo.php)
;   - Release build completed (run .\scripts\build_release.ps1 first)
;
; Usage:
;   1. Install Inno Setup
;   2. Open this file in Inno Setup Compiler
;   3. Click Build > Compile
;   OR
;   Run from command line: iscc installer\setup.iss
;
; Output:
;   installer\Output\ImageToVideoGenerator-Setup-v1.0.0.exe

#define MyAppName "Image-to-Video Generator"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tawfiq"
#define MyAppURL "https://github.com/YOUR_USERNAME/image-video-generator"
#define MyAppExeName "VideoGenerator.exe"

[Setup]
; Application Information
AppId={{A5B8C9D0-E1F2-4A5B-8C9D-0E1F2A5B8C9D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
InfoBeforeFile=..\installer\INSTALL_INFO.txt
OutputDir=.\Output
OutputBaseFilename=ImageToVideoGenerator-Setup-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; System Requirements
MinVersion=10.0.17763
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Visual Style
SetupIconFile=..\VideoGenerator\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardImageFile=..\installer\wizard_large.bmp
WizardSmallImageFile=..\installer\wizard_small.bmp

; Directories
DisableDirPage=no
DisableProgramGroupPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Application files
Source: "..\release\bin\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation
Source: "..\release\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
; Setup scripts
Source: "..\release\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs
; Version info
Source: "..\release\VERSION.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release\FILES.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Quick Start Guide"; Filename: "{app}\docs\QUICKSTART.md"
Name: "{group}\Troubleshooting Guide"; Filename: "{app}\docs\TROUBLESHOOTING.md"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Open Quick Start Guide after installation
Filename: "{app}\docs\QUICKSTART.md"; Description: "View Quick Start Guide"; Flags: postinstall shellexec skipifsilent unchecked
; Launch application
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\output"

[Code]
var
  DotNetPage: TOutputMsgMemoWizardPage;
  WSLPage: TOutputMsgMemoWizardPage;
  RequirementsOK: Boolean;

// Check if .NET 6.0 Runtime is installed
function IsDotNet60Installed: Boolean;
var
  Version: String;
  ResultCode: Integer;
begin
  Result := False;

  // Check using dotnet --list-runtimes
  if Exec('cmd.exe', '/c dotnet --list-runtimes | findstr "Microsoft.WindowsDesktop.App 6.0"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Result := (ResultCode = 0);
  end;
end;

// Check if WSL is installed
function IsWSLInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c wsl --status', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// Check if NVIDIA GPU is present
function IsNvidiaGPUPresent: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c wmic path win32_VideoController get name | findstr /i "NVIDIA"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  if Result then
    Result := (ResultCode = 0);
end;

// Initialize setup wizard
procedure InitializeWizard;
begin
  RequirementsOK := True;

  // Create .NET requirements page
  DotNetPage := CreateOutputMsgMemoPage(wpWelcome,
    'System Requirements Check',
    'Checking for required software...',
    'The installer will now check if your system meets the requirements.',
    '');

  // Create WSL requirements page
  WSLPage := CreateOutputMsgMemoPage(DotNetPage.ID,
    'Additional Requirements',
    'Python backend requirements',
    'The following components are required for the Python backend.',
    '');
end;

// Check system requirements
function NextButtonClick(CurPageID: Integer): Boolean;
var
  HasDotNet, HasWSL, HasNvidia: Boolean;
  ErrorMsg: String;
begin
  Result := True;

  if CurPageID = wpWelcome then
  begin
    // Check .NET 6.0
    HasDotNet := IsDotNet60Installed;
    if HasDotNet then
    begin
      DotNetPage.RichEditViewer.Lines.Add('✓ .NET 6.0 Desktop Runtime: INSTALLED');
    end
    else
    begin
      DotNetPage.RichEditViewer.Lines.Add('✗ .NET 6.0 Desktop Runtime: NOT FOUND');
      DotNetPage.RichEditViewer.Lines.Add('');
      DotNetPage.RichEditViewer.Lines.Add('The application requires .NET 6.0 Desktop Runtime.');
      DotNetPage.RichEditViewer.Lines.Add('Download from:');
      DotNetPage.RichEditViewer.Lines.Add('https://dotnet.microsoft.com/download/dotnet/6.0');
      RequirementsOK := False;
    end;

    DotNetPage.RichEditViewer.Lines.Add('');

    // Check WSL
    HasWSL := IsWSLInstalled;
    if HasWSL then
    begin
      DotNetPage.RichEditViewer.Lines.Add('✓ WSL (Windows Subsystem for Linux): INSTALLED');
    end
    else
    begin
      DotNetPage.RichEditViewer.Lines.Add('✗ WSL: NOT FOUND');
      DotNetPage.RichEditViewer.Lines.Add('');
      DotNetPage.RichEditViewer.Lines.Add('WSL 2 is required for the Python backend.');
      DotNetPage.RichEditViewer.Lines.Add('Install with: wsl --install -d Ubuntu-22.04');
      RequirementsOK := False;
    end;

    DotNetPage.RichEditViewer.Lines.Add('');

    // Check NVIDIA GPU
    HasNvidia := IsNvidiaGPUPresent;
    if HasNvidia then
    begin
      DotNetPage.RichEditViewer.Lines.Add('✓ NVIDIA GPU: DETECTED');
    end
    else
    begin
      DotNetPage.RichEditViewer.Lines.Add('⚠ NVIDIA GPU: NOT DETECTED');
      DotNetPage.RichEditViewer.Lines.Add('');
      DotNetPage.RichEditViewer.Lines.Add('An NVIDIA GPU with 12GB+ VRAM is strongly recommended.');
      DotNetPage.RichEditViewer.Lines.Add('The application may not work without a compatible GPU.');
    end;

    if not RequirementsOK then
    begin
      DotNetPage.RichEditViewer.Lines.Add('');
      DotNetPage.RichEditViewer.Lines.Add('========================================');
      DotNetPage.RichEditViewer.Lines.Add('WARNING: Required components are missing!');
      DotNetPage.RichEditViewer.Lines.Add('Install them before running the application.');
      DotNetPage.RichEditViewer.Lines.Add('========================================');

      ErrorMsg := 'Some required components are missing. ' +
                  'You can continue installation, but the application will not work ' +
                  'until you install the missing components.' + #13#10#13#10 +
                  'Continue anyway?';

      Result := MsgBox(ErrorMsg, mbConfirmation, MB_YESNO) = IDYES;
    end;
  end;

  if CurPageID = DotNetPage.ID then
  begin
    WSLPage.RichEditViewer.Lines.Add('Python Backend Setup');
    WSLPage.RichEditViewer.Lines.Add('====================');
    WSLPage.RichEditViewer.Lines.Add('');
    WSLPage.RichEditViewer.Lines.Add('After installation, you need to set up the Python backend:');
    WSLPage.RichEditViewer.Lines.Add('');
    WSLPage.RichEditViewer.Lines.Add('1. Open Ubuntu (WSL) terminal');
    WSLPage.RichEditViewer.Lines.Add('2. Navigate to installation directory');
    WSLPage.RichEditViewer.Lines.Add('3. Run: bash scripts/setup_wsl.sh');
    WSLPage.RichEditViewer.Lines.Add('4. Download AI models (~15GB, 20-40 minutes)');
    WSLPage.RichEditViewer.Lines.Add('');
    WSLPage.RichEditViewer.Lines.Add('See QUICKSTART.md in the installation folder for detailed instructions.');
    WSLPage.RichEditViewer.Lines.Add('');
    WSLPage.RichEditViewer.Lines.Add('Disk Space Requirements:');
    WSLPage.RichEditViewer.Lines.Add('  - Application: ~200 MB');
    WSLPage.RichEditViewer.Lines.Add('  - AI Models: ~15 GB');
    WSLPage.RichEditViewer.Lines.Add('  - Total recommended: 30+ GB free');
  end;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nThis application generates AI videos from static images using Stable Video Diffusion or AnimateDiff.%n%n⚠️ IMPORTANT: Requires NVIDIA RTX GPU with 12GB+ VRAM%n⚠️ AGE RESTRICTION: 18+ (NSFW model support)%n%nIt is recommended that you close all other applications before continuing.
