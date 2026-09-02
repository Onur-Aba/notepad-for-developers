# Zero-setup public client configuration

- Bundled the production GitHub App Client ID and App Slug as public desktop-client defaults.
- Bundled the production Supabase URL and Publishable Key as public desktop-client defaults.
- Preserved all existing `DEVNEST_*` environment variables as optional developer overrides.
- Fresh OneFile builds now work when launched by double-click on another Windows PC without PowerShell setup.
- GitHub access/refresh tokens remain in Windows Credential Manager and are not bundled.
- No Supabase service-role/secret key, GitHub client secret, private key, DB password, or signing secret is bundled.
- Added regression tests for no-environment packaged configuration.
