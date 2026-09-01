from __future__ import annotations

from app.services.credential_store import InMemoryCredentialStore, StoredCredentials


def test_in_memory_credentials_support_full_lifecycle() -> None:
    store = InMemoryCredentialStore()
    assert store.get_github_access_token() is None
    store.set(StoredCredentials("ghu_secret", "ghr_secret", "2099-01-01T00:00:00+00:00", None))
    assert store.get().refresh_token == "ghr_secret"
    store.delete()
    assert store.get().access_token is None


def test_windows_credential_blob_decoder_accepts_keyring_utf16() -> None:
    from app.services.credential_store import WindowsCredentialStore

    raw = '{"access_token":"ghu_saved"}'.encode("utf-16-le")
    assert WindowsCredentialStore._decode_blob(raw) == '{"access_token":"ghu_saved"}'
