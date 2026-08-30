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

$Architecture = python -c "import platform; print(platform.architecture()[0])"
if ($Architecture.Trim() -ne "64bit") {
    Write-Host "WARNING: You are not building with 64-bit Python. For normal Windows 10/11 distribution, 64-bit Python is recommended." -ForegroundColor Yellow
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
if ($LASTEXITCODE -ne 0) { Fail "Tests failed. Build stopped to avoid packaging a broken release." }
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue

foreach ($Folder in @("build", "dist")) {
    if (Test-Path $Folder) {
        Write-Host "Removing old $Folder folder..."
        Remove-Item -Recurse -Force $Folder
    }
}

if ($OneFile) {
    Write-Host "Building single-file DevNest.exe with PyInstaller..."
    python -m PyInstaller --noconfirm --clean DevNest.spec -- --onefile
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller one-file build failed. Review the output above." }
    $Exe = Join-Path $ProjectRoot "dist\DevNest.exe"
} else {
    Write-Host "Building DevNest onedir package with PyInstaller..."
    python -m PyInstaller --noconfirm --clean DevNest.spec
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller onedir build failed. Review the output above." }
    $Exe = Join-Path $ProjectRoot "dist\DevNest\DevNest.exe"
}

if (-not (Test-Path $Exe)) {
    Fail "Build completed without the expected executable: $Exe"
}

Write-Host ""
Write-Host "Build successful." -ForegroundColor Green
Write-Host "Executable: $Exe"
if ($OneFile) {
    Write-Host "You can distribute dist\DevNest.exe as a single file."
} else {
    Write-Host "For maximum reliability, distribute the ENTIRE dist\DevNest folder."
}
Write-Host "User notes remain in Windows AppData, not beside the executable."
