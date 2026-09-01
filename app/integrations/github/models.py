from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


@dataclass(slots=True)
class TokenBundle:
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    refresh_token_expires_in: int | None = None
