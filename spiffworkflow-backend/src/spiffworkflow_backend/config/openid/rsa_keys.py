# These configs are specifically for the open id server run from backend.
# This should only be used for development and demonstration. SHOULD NOT BE USED IN PROD.

import os
import tempfile
from collections.abc import Callable
from pathlib import Path


def _validate_private_key_pem(private_key: str) -> None:
    from cryptography.hazmat.primitives import serialization

    serialization.load_pem_private_key(private_key.encode(), password=None)


def _validate_public_key_pem(public_key: str) -> None:
    from cryptography.hazmat.primitives import serialization

    serialization.load_pem_public_key(public_key.encode())


def _validate_key_pair(private_key: str, public_key: str) -> tuple[str, str] | None:
    from cryptography.exceptions import UnsupportedAlgorithm

    try:
        _validate_private_key_pem(private_key)
        _validate_public_key_pem(public_key)
    except (TypeError, ValueError, UnsupportedAlgorithm):
        return None
    return (private_key, public_key)


def _write_validated_pem_atomically(path: Path, pem_contents: str, mode: int, validator: Callable[[str], None]) -> None:
    validator(pem_contents)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, prefix=f"{path.name}.", suffix=".tmp", delete=False) as tmp_file:
        tmp_file.write(pem_contents)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = Path(tmp_file.name)

    try:
        os.chmod(tmp_path, mode)
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _expected_worker_count() -> int:
    configured_count = os.getenv("SERVER_WORKER_COUNT", "1")
    try:
        return int(configured_count)
    except ValueError:
        return 1


def _key_cache_dir() -> Path:
    configured_dir = os.getenv("OPENID_KEY_CACHE_DIR")
    if configured_dir:
        return Path(configured_dir)
    return Path(tempfile.gettempdir()) / "spiffworkflow-dev-openid-keys"


def _key_paths() -> tuple[Path, Path, Path]:
    key_dir = _key_cache_dir()
    return (
        key_dir / "openid-private.pem",
        key_dir / "openid-public.pem",
        key_dir / ".lock",
    )


def _read_key_pair_from_files(private_key_path: Path, public_key_path: Path) -> tuple[str, str] | None:
    if private_key_path.exists() and public_key_path.exists():
        return _validate_key_pair(private_key_path.read_text(), public_key_path.read_text())
    return None


def _load_or_create_file_backed_keys_with_lock() -> tuple[str, str]:
    private_key_path, public_key_path, lock_path = _key_paths()
    private_key_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open("w") as lock_file:
        import fcntl

        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

        existing_keys = _read_key_pair_from_files(private_key_path, public_key_path)
        if existing_keys is not None:
            return existing_keys

        private_key, public_key = _generate_keys()
        _write_validated_pem_atomically(private_key_path, private_key, 0o600, _validate_private_key_pem)
        _write_validated_pem_atomically(public_key_path, public_key, 0o644, _validate_public_key_pem)
        return (private_key, public_key)


def _load_or_create_file_backed_keys_without_lock() -> tuple[str, str]:
    private_key_path, public_key_path, _lock_path = _key_paths()
    private_key_path.parent.mkdir(parents=True, exist_ok=True)

    existing_keys = _read_key_pair_from_files(private_key_path, public_key_path)
    if existing_keys is not None:
        return existing_keys

    private_key, public_key = _generate_keys()
    _write_validated_pem_atomically(private_key_path, private_key, 0o600, _validate_private_key_pem)
    _write_validated_pem_atomically(public_key_path, public_key, 0o644, _validate_public_key_pem)
    return (private_key, public_key)


def _load_or_create_file_backed_keys() -> tuple[str, str]:
    try:
        import fcntl  # noqa: F401
    except ImportError as err:
        if _expected_worker_count() > 1:
            raise RuntimeError(
                "Built-in OpenID dev keys require OPENID_PRIVATE_KEY and OPENID_PUBLIC_KEY "
                "when running with multiple workers on platforms without fcntl-based file locking."
            ) from err
        return _load_or_create_file_backed_keys_without_lock()

    return _load_or_create_file_backed_keys_with_lock()


def _generate_keys() -> tuple[str, str]:
    """Generate ephemeral RSA key pair for development."""
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        return private_pem, public_pem
    except ImportError as err:
        raise RuntimeError(
            "cryptography package is required to generate RSA keys. Install it with: pip install cryptography"
        ) from err


def _initialize_keys() -> tuple[str, str]:
    """Initialize keys from environment or load a shared cached keypair."""
    private_key = os.getenv("OPENID_PRIVATE_KEY")
    public_key = os.getenv("OPENID_PUBLIC_KEY")

    if private_key and not public_key:
        raise RuntimeError("OPENID_PRIVATE_KEY is set but OPENID_PUBLIC_KEY is missing.")

    if public_key and not private_key:
        raise RuntimeError("OPENID_PUBLIC_KEY is set but OPENID_PRIVATE_KEY is missing.")

    if private_key and public_key:
        validated_key_pair = _validate_key_pair(private_key, public_key)
        if validated_key_pair is not None:
            return validated_key_pair

    return _load_or_create_file_backed_keys()


class OpenIdConfigsForDevOnly:
    # Initialize keys at module load time
    private_key, public_key = _initialize_keys()
