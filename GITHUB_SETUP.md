# DevNest 2.0 — GitHub App setup

DevNest is local-first. GitHub is an optional, read-only integration used to list repositories, inspect commits / pull requests and compare revisions.

## GitHub App settings

Create a GitHub App under **GitHub → Settings → Developer settings → GitHub Apps → New GitHub App**.

Use:

- **Device Flow:** enabled
- **Webhook:** disabled
- **Expire user authorization tokens:** enabled is recommended; DevNest stores the refresh token securely and refreshes automatically
- **Repository permissions**
  - Metadata: Read
  - Contents: Read-only
  - Pull requests: Read-only
- Do not grant repository write permissions.

The desktop app needs the public **Client ID** (not App ID) and, for automatic installation navigation, the GitHub App **slug**. No client secret or private key belongs in DevNest.

## Configure DevNest once

From PowerShell in the project folder:

```powershell
$env:DEVNEST_GITHUB_CLIENT_ID="Iv1.YOUR_PUBLIC_CLIENT_ID"
$env:DEVNEST_GITHUB_APP_SLUG="your-app-slug"
python main.py
```

The updated build remembers these two **public** identifiers in Windows QSettings. After that, closing PowerShell or launching the packaged EXE by double-click does not require re-entering them on the same Windows account.

## What happens when you press Connect GitHub

1. DevNest starts GitHub Device Flow and opens GitHub.
2. You authorize the GitHub user access token.
3. If the GitHub App is not installed yet, DevNest automatically opens the App installation page.
4. On GitHub, choose **All repositories** or **Only select repositories** and finish installation.
5. DevNest polls for that installation in the background and automatically loads the allowed repositories. You do not need to restart the desktop app.
6. If you later use **Manage Access** and change repository selections, DevNest automatically retries refreshes after the browser opens.

Authorizing the user and installing the GitHub App are separate GitHub operations. A successful Device Flow login alone does not grant repository access until an installation exposes repositories to the app.

## Persistence and security

- GitHub access and refresh tokens are stored in **Windows Credential Manager** under `DevNest.GitHub`.
- Tokens are not stored in SQLite or QSettings.
- Closing/reopening DevNest keeps the connection as long as GitHub has not revoked it and the refresh token remains valid.
- DevNest validates/synchronizes a stored connection at startup when **Check repositories on startup** is enabled.
- Disconnect removes the secure GitHub credentials but preserves local projects, notes, decisions, diagrams, repository references and review baselines.

## Windows EXE

See `BUILD_WINDOWS.md`.

Recommended build:

```powershell
.\build.ps1
```

Single-file build:

```powershell
.\build.ps1 -OneFile
```
