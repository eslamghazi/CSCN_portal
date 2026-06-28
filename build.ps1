# Build the 64-bit CSCN web portal using the 64-bit Python venv. Output:
# dist\CSCN\CSCN.exe (a --onedir folder).
#
# This is a WEB app: the exe runs a local FastAPI/uvicorn server and opens the
# browser. The React SPA is pre-built (npm) into frontend\dist and bundled as data.
$ErrorActionPreference = "Continue"

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

Write-Host "Cleaning up old builds..."
Remove-Item -Recurse -Force dist\CSCN -ErrorAction SilentlyContinue
Get-Process -Name "CSCN" -ErrorAction SilentlyContinue | Stop-Process -Force

$envArgs = @()
if (Test-Path ".env") { $envArgs = @("--add-data", ".env;.") }

# --windowed: no console window; the app shows a small Tkinter status window
# instead (see launcher.py). Tkinter/Tcl-Tk are bundled automatically.
& .\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --noupx --windowed --name CSCN `
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
    --hidden-import uvicorn.loops.asyncio `
    --hidden-import uvicorn.protocols.http.h11_impl `
    --hidden-import uvicorn.protocols.websockets.auto `
    --hidden-import uvicorn.lifespan.on `
    --hidden-import multipart `
    --hidden-import sqlalchemy.dialects.sqlite `
    web_main.py

$piExit = $LASTEXITCODE
if ($piExit -eq 0 -and (Test-Path "dist\CSCN\CSCN.exe")) {
    Write-Host "64-bit web build complete! Folder: dist\CSCN\ (run CSCN.exe)"
} else {
    Write-Error "Build FAILED (PyInstaller exit $piExit); dist\CSCN\CSCN.exe was not produced."
    exit 1
}
