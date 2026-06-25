; Inno Setup script for the CSCN Portal — Arabic wizard, per-user install.
; Packages the single-file dist\CSCN.exe into an installer (CSCN_Setup.exe) with
; Start Menu + optional desktop shortcuts, an Add/Remove Programs entry, and an
; uninstaller. Installs per-user under %LocalAppData%\Programs (no admin / no UAC).
; The app's data lives in C:\CSCN (separate from the install dir), so
; uninstalling does NOT remove the database, uploads, or logs.

#define MyAppName "بوابة CSCN"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Eslam Gamal Ghazi"
#define MyAppExeName "CSCN.exe"

[Setup]
; A stable AppId so upgrades/uninstall are tracked correctly across versions.
AppId={{8F4B2C1A-6E5D-4A3B-9C2E-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright=© 2026 Eslam Gamal Ghazi
LicenseFile=LICENSE
DefaultDirName={autopf}\CSCN
DefaultGroupName=CSCN
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=CSCN_Setup
SetupIconFile=ui\resources\icons\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; 64-bit app: only install on 64-bit Windows (matches the build).
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Per-user install (no admin / no UAC); installs under %LocalAppData%\Programs.
PrivilegesRequired=lowest
; Replace the exe even if it is currently running.
CloseApplications=force

[Languages]
Name: "ar"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; One-dir build: ship the whole folder (exe + the _internal runtime) for fast
; startup (no per-launch unpacking).
Source: "dist\CSCN\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\إزالة {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
