from __future__ import annotations

import os
import shutil
import subprocess
import webbrowser
from pathlib import Path


class BrowserLauncher:
    def _chrome_candidates(self) -> list[Path]:
        candidates: list[Path] = []
        for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env_name)
            if base:
                candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
        located = shutil.which("chrome") or shutil.which("chrome.exe")
        if located:
            candidates.insert(0, Path(located))
        return candidates

    def open(self, url: str) -> bool:
        if os.name == "nt":
            for candidate in self._chrome_candidates():
                if candidate.exists():
                    try:
                        subprocess.Popen([str(candidate), url], shell=False)
                        return True
                    except OSError:
                        continue
        try:
            return bool(webbrowser.open(url, new=2, autoraise=True))
        except Exception:
            return False
