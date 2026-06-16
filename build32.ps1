# Build the 32-bit CSCN portal (runs on 32-bit Windows and Windows 7+) using the
# 32-bit Python venv (venv32 + PySide2). Output: dist\CSCN_x86\CSCN_x86.exe.
#
# Uses --onedir (a folder) NOT --onefile: a one-file exe re-extracts ~120 MB to a
# temp dir on EVERY launch (slow startup); a one-dir build runs in place, so it
# opens in ~1-2s instead of many seconds. The installer ships the whole folder.
$ErrorActionPreference = "Continue"

if (-not (Test-Path ".\venv32\Scripts\python.exe")) {
    Write-Error "venv32 not found. Create the 32-bit env first (see migration setup)."
    exit 1
}

Write-Host "Cleaning old 32-bit build..."
Remove-Item -Recurse -Force dist\CSCN_x86 -ErrorAction SilentlyContinue
Remove-Item -Force dist\CSCN_x86.exe -ErrorAction SilentlyContinue
Get-Process -Name "CSCN_x86" -ErrorAction SilentlyContinue | Stop-Process -Force

$envArgs = @()
if (Test-Path ".env") {
    Write-Host "Embedding .env into the build."
    $envArgs = @("--add-data", ".env;.")
} else {
    Write-Warning ".env not found; the exe will fall back to a random superadmin password."
}

# qtpy selects PySide2 automatically (the only Qt binding in venv32).
# --onedir + --noupx: fastest startup (no per-launch unpack, no UPX decompression).
& .\venv32\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --noupx --windowed --name CSCN_x86 `
    --icon ui\resources\icons\app.ico `
    @envArgs `
    --collect-submodules domain `
    --collect-submodules infrastructure `
    --collect-submodules application `
    --collect-submodules ui `
    --collect-submodules qtpy `
    --collect-submodules qtawesome `
    --collect-data qtawesome `
    main.py

$piExit = $LASTEXITCODE
if ($piExit -eq 0 -and (Test-Path "dist\CSCN_x86\CSCN_x86.exe")) {
    Write-Host "32-bit build complete! Folder: dist\CSCN_x86\ (run CSCN_x86.exe)"
} else {
    Write-Error "32-bit build FAILED (PyInstaller exit $piExit); dist\CSCN_x86\CSCN_x86.exe not produced."
    exit 1
}
