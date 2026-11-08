from pathlib import Path

import pytest
from flask import Flask

from spiffworkflow_backend.config.openid import rsa_keys


def test_worker_count_uses_environment_before_app_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_SERVER_WORKER_COUNT", "2")

    assert rsa_keys.OpenIdConfigsForDevOnly._expected_worker_count() == 2


def test_worker_count_uses_app_config_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_SERVER_WORKER_COUNT", "2")
    app = Flask(__name__)
    app.config["SPIFFWORKFLOW_BACKEND_SERVER_WORKER_COUNT"] = 3

    with app.app_context():
        assert rsa_keys.OpenIdConfigsForDevOnly._expected_worker_count() == 3


def test_read_key_pair_from_files_returns_none_for_truncated_pems(tmp_path: Path) -> None:
    private_key_path = tmp_path / "openid-private.pem"
    public_key_path = tmp_path / "openid-public.pem"

    private_key, public_key = rsa_keys.OpenIdConfigsForDevOnly._generate_keys()
    private_key_path.write_text(private_key[:40])
    public_key_path.write_text(public_key[:40])

    assert rsa_keys.OpenIdConfigsForDevOnly._read_key_pair_from_files(private_key_path, public_key_path) is None


def test_write_validated_pem_atomically_rejects_invalid_pem(tmp_path: Path) -> None:
    private_key_path = tmp_path / "openid-private.pem"

    with pytest.raises(ValueError):
        rsa_keys.OpenIdConfigsForDevOnly._write_validated_pem_atomically(
            private_key_path,
            "not-a-valid-private-key",
            0o600,
            rsa_keys.OpenIdConfigsForDevOnly._validate_private_key_pem,
        )

    assert not private_key_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_initialize_keys_raises_on_invalid_env_key_pair(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY", "truncated-private-key")
    monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY", "truncated-public-key")

    with pytest.raises(RuntimeError, match="invalid key data"):
        rsa_keys.OpenIdConfigsForDevOnly._initialize_keys()


def test_initialize_keys_raises_when_public_key_env_var_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, _public_key = rsa_keys.OpenIdConfigsForDevOnly._generate_keys()

    monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY", private_key)
    monkeypatch.delenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY"):
        rsa_keys.OpenIdConfigsForDevOnly._initialize_keys()


def test_initialize_keys_raises_when_private_key_env_var_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _private_key, public_key = rsa_keys.OpenIdConfigsForDevOnly._generate_keys()

    monkeypatch.delenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY", public_key)

    with pytest.raises(RuntimeError, match="SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY"):
        rsa_keys.OpenIdConfigsForDevOnly._initialize_keys()
