# Build the 32-bit CSCN web portal (runs on 32-bit Windows and Windows 7+) using
# the 32-bit Python venv (venv32). Output: dist\CSCN_x86\CSCN_x86.exe.
#
# This is now a WEB app: the exe runs a local FastAPI/uvicorn server and opens the
# default browser. The React SPA is pre-built (npm) into frontend\dist and bundled
# as data. --onedir (a folder, not --onefile) gives fast startup with no per-launch
# extraction; the installer ships the whole folder.
$ErrorActionPreference = "Continue"

if (-not (Test-Path ".\venv32\Scripts\python.exe")) {
    Write-Error "venv32 not found. Create the 32-bit env first."
    exit 1
}

# 1. Build the React SPA (Node is needed only here, at build time).
Write-Host "Building the React frontend (vite)..."
Push-Location frontend
if (-not (Test-Path "node_modules")) { npm install }
npm run build
$npmExit = $LASTEXITCODE
Pop-Location
if ($npmExit -ne 0 -or -not (Test-Path "frontend\dist\index.html")) {
    Write-Error "Frontend build FAILED; frontend\dist\index.html not produced."
    exit 1
}

Write-Host "Cleaning old 32-bit build..."
Remove-Item -Recurse -Force dist\CSCN_x86 -ErrorAction SilentlyContinue
Get-Process -Name "CSCN_x86" -ErrorAction SilentlyContinue | Stop-Process -Force

$envArgs = @()
if (Test-Path ".env") { $envArgs = @("--add-data", ".env;.") }

# Web build: entry is web_main.py; no Qt. Bundle the built SPA + the Arabic PDF
# font. uvicorn submodules must be hidden-imported (dynamic imports).
# --windowed: no console window; the app shows a system-tray icon instead
# (see launcher.py). pystray's win32 backend is imported dynamically.
& .\venv32\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --noupx --windowed --name CSCN_x86 `
    --icon ui\resources\icons\app.ico `
    @envArgs `
    --add-data "frontend\dist;frontend\dist" `
    --add-data "ui\resources\fonts;ui\resources\fonts" `
    --add-data "ui\resources\icons;ui\resources\icons" `
    --collect-submodules api `
    --collect-submodules application `
    --collect-submodules infrastructure `
    --collect-submodules domain `
    --collect-submodules config `
    --collect-submodules database `
    --collect-submodules uvicorn `
    --collect-submodules pystray `
    --hidden-import uvicorn.loops.asyncio `
    --hidden-import uvicorn.protocols.http.h11_impl `
    --hidden-import uvicorn.protocols.websockets.auto `
    --hidden-import uvicorn.lifespan.on `
    --hidden-import multipart `
    --hidden-import sqlalchemy.dialects.sqlite `
    --hidden-import pystray._win32 `
    --hidden-import PIL.ImageDraw `
    web_main.py

$piExit = $LASTEXITCODE
if ($piExit -eq 0 -and (Test-Path "dist\CSCN_x86\CSCN_x86.exe")) {
    Write-Host "32-bit web build complete! Folder: dist\CSCN_x86\ (run CSCN_x86.exe)"
} else {
    Write-Error "32-bit build FAILED (PyInstaller exit $piExit); dist\CSCN_x86\CSCN_x86.exe not produced."
    exit 1
}
