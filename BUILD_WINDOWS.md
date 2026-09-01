# DevNest Windows EXE Build

## 1. GitHub App configuration (one-time on this Windows account)

If you already ran DevNest from PowerShell with these values, the updated app stores the **public** Client ID and app slug in QSettings automatically:

```powershell
$env:DEVNEST_GITHUB_CLIENT_ID="Iv1.YOUR_PUBLIC_CLIENT_ID"
$env:DEVNEST_GITHUB_APP_SLUG="your-devnest-app-slug"
python main.py
```

The access/refresh tokens are never stored in QSettings or SQLite. They stay in Windows Credential Manager.

## 2. Build the recommended folder package

Open PowerShell in the project directory with the virtual environment active:

```powershell
.\build.ps1
```

Output:

```text
dist\DevNest\DevNest.exe
```

Distribute/copy the whole `dist\DevNest` folder.

## 3. Build a single EXE

```powershell
.\build.ps1 -OneFile
```

Output:

```text
dist\DevNest.exe
```

The one-file build is convenient, but the normal onedir package is generally easier to troubleshoot.

## GitHub connection persistence

DevNest stores GitHub user and refresh tokens in **Windows Credential Manager** under `DevNest.GitHub`, not in the executable and not in SQLite. Closing/reopening the app therefore does not intentionally disconnect GitHub. If the normal user access token expires, DevNest uses the stored refresh token automatically when GitHub issued one.
