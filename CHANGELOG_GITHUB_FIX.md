# GitHub connection / persistence fix

This patch is based on the `DevNest-schema5-v6-fix` source.

Changes:

- Device Flow authorization now continues into GitHub App installation when no installation exists.
- The GitHub App installation page opens automatically after authorization (when app slug is configured).
- DevNest polls for the new installation and loads selected repositories without an app restart.
- `Manage Access` schedules automatic repository refreshes after GitHub opens.
- Repository-list failures are isolated per installation so one inaccessible installation does not hide all others.
- GitHub connection is synchronized automatically on app startup when repository startup checks are enabled.
- Access/refresh tokens use Windows Credential Manager directly on Windows, with compatibility for the previous `DevNest.GitHub` keyring credential target.
- Public GitHub App Client ID and app slug are remembered in QSettings after being supplied once through environment variables.
- PyInstaller one-file/onedir switching in `build.ps1` / `DevNest.spec` was corrected.
- Added `BUILD_WINDOWS.md` and updated `GITHUB_SETUP.md`.
