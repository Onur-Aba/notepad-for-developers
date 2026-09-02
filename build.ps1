param(
    [switch]$SkipInstall,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

try {
    $VersionText = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
} catch {
    Fail "Python was not found. Install 64-bit Python 3.12 or newer and reopen PowerShell."
}

$Parts = $VersionText.Trim().Split('.')
if ([int]$Parts[0] -lt 3 -or ([int]$Parts[0] -eq 3 -and [int]$Parts[1] -lt 12)) {
    Fail "Python 3.12+ is required. Found $VersionText."
}

if (-not $SkipInstall) {
    Write-Host "Installing/updating project dependencies..."
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed." }
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Fail "Dependency installation failed." }
}

python -c "import PySide6, PyInstaller; print('PySide6', PySide6.__version__, '| PyInstaller', PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) { Fail "PySide6 or PyInstaller is unavailable in the active Python environment." }

Write-Host "Running tests..."
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    Fail "Tests failed. Build stopped to avoid packaging a broken release."
}
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue

foreach ($Folder in @("build", "dist")) {
    if (Test-Path $Folder) {
        Write-Host "Removing old $Folder folder..."
        Remove-Item -Recurse -Force $Folder
    }
}

$env:DEVNEST_BUILD_ONEFILE = if ($OneFile) { "1" } else { "0" }
try {
    if ($OneFile) {
        Write-Host "Building single-file DevNest.exe with PyInstaller..."
    } else {
        Write-Host "Building DevNest onedir package with PyInstaller..."
    }
    python -m PyInstaller --noconfirm --clean DevNest.spec
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller build failed. Review the output above." }
} finally {
    Remove-Item Env:DEVNEST_BUILD_ONEFILE -ErrorAction SilentlyContinue
}

if ($OneFile) {
    $Exe = Join-Path $ProjectRoot "dist\DevNest.exe"
} else {
    $Exe = Join-Path $ProjectRoot "dist\DevNest\DevNest.exe"
}

if (-not (Test-Path $Exe)) {
    Fail "Build completed without the expected executable: $Exe"
}

Write-Host ""
Write-Host "Build successful." -ForegroundColor Green
Write-Host "Executable: $Exe"
if ($OneFile) {
    Write-Host "Distribute dist\DevNest.exe."
} else {
    Write-Host "For maximum reliability, distribute the ENTIRE dist\DevNest folder."
}
Write-Host "GitHub tokens remain in Windows Credential Manager and are NOT embedded in the EXE."
Write-Host "Public GitHub Client ID/App Slug and Supabase URL/Publishable Key are bundled for zero-setup distribution."
Write-Host "No service-role key, Supabase secret key, GitHub client secret, or private key is bundled."
Write-Host "DEVNEST_* environment variables are optional developer overrides only."
