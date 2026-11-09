import hashlib
import multiprocessing
import os
import time
from pathlib import Path

import pytest

from spiffworkflow_backend.config.openid import rsa_keys


def _load_keys_in_parallel(cache_dir: str, barrier, results) -> None:
    os.environ["SPIFFWORKFLOW_BACKEND_OPEN_ID_CACHE_DIR"] = cache_dir
    original_generate = rsa_keys.OpenIdConfigsForDevOnly._generate_keys

    def slow_generate(cls):
        time.sleep(0.5)
        return original_generate()

    rsa_keys.OpenIdConfigsForDevOnly._generate_keys = classmethod(slow_generate)
    barrier.wait(timeout=20)
    _, public_key = rsa_keys.OpenIdConfigsForDevOnly._load_or_create_file_backed_keys()
    results.put(hashlib.sha256(public_key.encode()).hexdigest())


def test_parallel_workers_reuse_same_generated_keys(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_CACHE_DIR", str(tmp_path / "bootstrap"))
    monkeypatch.delenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("SPIFFWORKFLOW_BACKEND_SERVER_WORKER_COUNT", raising=False)
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    results = context.Queue()
    processes = [
        context.Process(target=_load_keys_in_parallel, args=(str(tmp_path / "shared"), barrier, results)) for _ in range(2)
    ]

    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)
        if process.is_alive():
            process.terminate()
            process.join()

    assert [process.exitcode for process in processes] == [0, 0]
    fingerprints = [results.get(timeout=5) for _ in processes]
    assert fingerprints[0] == fingerprints[1]


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
