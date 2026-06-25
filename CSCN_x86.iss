; Inno Setup script for the 32-bit CSCN Portal — Arabic wizard, per-user install.
; Packages dist\CSCN_x86.exe (the 32-bit build) into CSCN_Setup_x86.exe. Unlike
; the 64-bit installer this places NO architecture restriction, so it installs
; on 32-bit Windows (and Windows 7+). Per-user install (no admin / no UAC).
; The app's data lives in C:\CSCN, so uninstalling keeps the database/uploads/logs.

#define MyAppName "بوابة CSCN"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Eslam Gamal Ghazi"
#define MyAppExeName "CSCN_x86.exe"

[Setup]
; Same AppId as the 64-bit installer: a machine uses whichever build fits it.
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
OutputBaseFilename=CSCN_Setup_x86
SetupIconFile=ui\resources\icons\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; No architecture restriction — runs on 32-bit and 64-bit Windows.
; Per-user install (no admin / no UAC); installs under %LocalAppData%\Programs.
PrivilegesRequired=lowest
CloseApplications=force

[Languages]
Name: "ar"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; One-dir build: ship the whole folder (exe + the _internal runtime) for fast
; startup (no per-launch unpacking).
Source: "dist\CSCN_x86\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\إزالة {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Best-effort: open the web + peer ports so other PCs can reach the portal over
; the LAN. Succeeds when the installer runs elevated; otherwise the app requests
; it once on first launch. runascurrentuser keeps it from failing the install.
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""CSCN Portal"" dir=in action=allow protocol=TCP localport=8765,50525"; Flags: runhidden runascurrentuser skipifdoesntexist; StatusMsg: "إعداد جدار الحماية للوصول عبر الشبكة..."
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
