# Build a single-file, self-contained CSCN.exe that runs on any Windows PC
# without installing Python or any dependencies. Output: dist\CSCN.exe
# (Note: PyInstaller writes INFO to stderr; keep ErrorActionPreference=Continue
#  and do NOT pipe the native command through 2>&1, or PowerShell treats those
#  INFO lines as fatal errors.)
$ErrorActionPreference = "Continue"

Write-Host "Cleaning up old builds..."
Remove-Item -Recurse -Force dist\CSCN_portal -ErrorAction SilentlyContinue
Remove-Item -Force dist\CSCN_portal.exe -ErrorAction SilentlyContinue
Remove-Item -Force dist\CSCN.exe -ErrorAction SilentlyContinue

Write-Host "Killing any running instances..."
Get-Process -Name "CSCN", "CSCN_portal" -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Starting PyInstaller (single-file) build..."
# Embed the .env INTO the exe so the distributed file needs no external .env
# (config/settings._load_dotenv reads it from the bundle at runtime).
$envArgs = @()
if (Test-Path ".env") {
    Write-Host "Embedding .env into the build."
    $envArgs = @("--add-data", ".env;.")
} else {
    Write-Warning ".env not found; the exe will fall back to a random superadmin password."
}

# --onefile: one portable exe. qtawesome ships icon fonts that must be collected.
# The stylesheet is generated in Python, so no QSS data file is bundled.
# Invoke via `python -m PyInstaller` rather than the pyinstaller.exe console
# script: the .exe wrapper breaks if the venv is relocated, whereas the module
# form always works.
& .\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name CSCN `
    --icon ui\resources\icons\app.ico `
    @envArgs `
    --collect-submodules domain `
    --collect-submodules infrastructure `
    --collect-submodules application `
    --collect-submodules ui `
    --collect-submodules qtawesome `
    --collect-data qtawesome `
    main.py

# Verify the artifact instead of unconditionally reporting success: PyInstaller
# writes INFO to stderr, so don't trust output alone — check the exit code AND
# that the exe actually exists.
$piExit = $LASTEXITCODE
if ($piExit -eq 0 -and (Test-Path "dist\CSCN.exe")) {
    Write-Host "Build complete! Single file: dist\CSCN.exe"
} else {
    Write-Error "Build FAILED (PyInstaller exit $piExit); dist\CSCN.exe was not produced."
    exit 1
}
