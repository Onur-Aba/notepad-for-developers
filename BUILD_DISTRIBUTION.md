# DevNest zero-setup Windows build

This release bundles only the public/client production identifiers required by
GitHub and Supabase, so end users do **not** need PowerShell environment
variables to launch `DevNest.exe`.

Bundled client-visible values:

- GitHub App Client ID
- GitHub App slug
- Supabase project URL
- Supabase publishable key

Never add any of the following to the desktop application:

- GitHub Client Secret / private key
- Supabase `service_role` key
- Supabase `sb_secret_...` key
- database password
- JWT signing secret

Supabase authorization is enforced by the project's RLS/RPC policies in
`supabase/devnest_schema.sql`. The publishable key is not an authorization
bypass.

## Build a single EXE

From PowerShell in the project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\build.ps1 -OneFile
```

If the virtual environment/dependencies already exist, only run:

```powershell
.\.venv\Scripts\Activate.ps1
.\build.ps1 -OneFile
```

The distributable file is:

```text
dist\DevNest.exe
```

The recipient can double-click this EXE without setting any `DEVNEST_*`
environment variables.

## Optional developer overrides

Developers can still temporarily point a local build to another GitHub App or
Supabase project by setting the existing `DEVNEST_*` environment variables
before launching DevNest. These overrides are not required for production use.
