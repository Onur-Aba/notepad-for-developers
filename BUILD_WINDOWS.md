# DevNest — Windows EXE build

## Requirements

- Windows 10/11 64-bit
- 64-bit Python 3.12 or newer (3.12 or 3.13 recommended)
- Internet access the first time dependencies are installed

When installing Python from python.org, enable **Add python.exe to PATH**.

## Recommended clean build

Open PowerShell in the extracted DevNest project folder and run:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
.\build.ps1 -SkipInstall
```

The recommended folder build is created at:

```text
dist\DevNest\DevNest.exe
```

Keep the entire `dist\DevNest` folder together when copying it to another PC.

## Single-file EXE

After activating the same virtual environment:

```powershell
.\build.ps1 -SkipInstall -OneFile
```

Output:

```text
dist\DevNest.exe
```

The single-file build is convenient, but startup can be a little slower because PyInstaller has to unpack runtime files. For the fastest and easiest-to-debug package, prefer the normal folder build.

## If PowerShell blocks Activate.ps1 or build.ps1

Run this only for the current PowerShell window:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then run the activation/build command again.

## GitHub App configuration (optional)

If you use the GitHub integration, public Client ID/App Slug values can be supplied as developer overrides:

```powershell
$env:DEVNEST_GITHUB_CLIENT_ID="Iv1.YOUR_PUBLIC_CLIENT_ID"
$env:DEVNEST_GITHUB_APP_SLUG="your-devnest-app-slug"
```

GitHub access/refresh tokens are not embedded in the EXE. On Windows they are stored in Windows Credential Manager.
