# Build the Windows installer (dist\CSCN_Setup.exe) from dist\CSCN.exe using
# Inno Setup. Run .\build.ps1 first to produce a fresh dist\CSCN.exe.
$ErrorActionPreference = "Continue"

if (-not (Test-Path "dist\CSCN.exe")) {
    Write-Error "dist\CSCN.exe not found. Run .\build.ps1 first."
    exit 1
}

# Locate the Inno Setup command-line compiler (ISCC.exe).
$iscc = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}
if (-not $iscc) {
    Write-Error "Inno Setup not found. Install it with: winget install -e --id JRSoftware.InnoSetup"
    exit 1
}

Write-Host "Compiling installer with $iscc ..."
& $iscc "CSCN.iss"

if ($LASTEXITCODE -eq 0 -and (Test-Path "dist\CSCN_Setup.exe")) {
    Write-Host "Installer built: dist\CSCN_Setup.exe"
} else {
    Write-Error "Installer build FAILED (ISCC exit $LASTEXITCODE)."
    exit 1
}
