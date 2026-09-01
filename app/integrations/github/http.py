from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .errors import GitHubNetworkError


@dataclass(slots=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    data: Any


class HttpTransport:
    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def request(self, method: str, url: str, *, headers: dict[str, str] | None = None,
                query: dict[str, object] | None = None, form: dict[str, object] | None = None,
                json_body: dict[str, object] | None = None) -> HttpResponse:
        if query:
            encoded = urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
            url = f"{url}{'&' if '?' in url else '?'}{encoded}"
        request_headers = dict(headers or {})
        body: bytes | None = None
        if form is not None:
            body = urllib.parse.urlencode(form).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        request = urllib.request.Request(url, data=body, headers=request_headers, method=method.upper())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                return HttpResponse(
                    status=int(response.status),
                    headers={k.lower(): v for k, v in response.headers.items()},
                    data=self._decode(raw, response.headers.get("Content-Type", "")),
                )
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            return HttpResponse(
                status=int(exc.code),
                headers={k.lower(): v for k, v in exc.headers.items()},
                data=self._decode(raw, exc.headers.get("Content-Type", "")),
            )
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            raise GitHubNetworkError(f"Could not reach GitHub: {exc}") from exc

    @staticmethod
    def _decode(raw: bytes, content_type: str) -> Any:
        if not raw:
            return None
        text = raw.decode("utf-8", errors="replace")
        if "json" in content_type.lower() or text[:1] in "[{":
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"message": text[:1000]}
        return text
