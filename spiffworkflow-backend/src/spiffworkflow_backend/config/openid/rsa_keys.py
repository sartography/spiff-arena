# These configs are specifically for the open id server run from backend.
# This should only be used for development and demonstration. SHOULD NOT BE USED IN PROD.

import os
import tempfile
from pathlib import Path


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
        return (private_key_path.read_text(), public_key_path.read_text())
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
        private_key_path.write_text(private_key)
        public_key_path.write_text(public_key)
        os.chmod(private_key_path, 0o600)
        os.chmod(public_key_path, 0o644)
        return (private_key, public_key)


def _load_or_create_file_backed_keys_without_lock() -> tuple[str, str]:
    private_key_path, public_key_path, _lock_path = _key_paths()
    private_key_path.parent.mkdir(parents=True, exist_ok=True)

    existing_keys = _read_key_pair_from_files(private_key_path, public_key_path)
    if existing_keys is not None:
        return existing_keys

    private_key, public_key = _generate_keys()
    private_key_path.write_text(private_key)
    public_key_path.write_text(public_key)
    os.chmod(private_key_path, 0o600)
    os.chmod(public_key_path, 0o644)
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

    if private_key and public_key:
        return (private_key, public_key)

    return _load_or_create_file_backed_keys()


class OpenIdConfigsForDevOnly:
    # Initialize keys at module load time
    private_key, public_key = _initialize_keys()
