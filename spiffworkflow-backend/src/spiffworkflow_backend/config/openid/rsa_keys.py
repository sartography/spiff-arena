# These configs are specifically for the open id server run from backend.
# This should only be used for development and demonstration. SHOULD NOT BE USED IN PROD.
import os
import tempfile
from collections.abc import Callable
from pathlib import Path

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import current_app

try:
    # fcntl is not available on Windows. With multiple workers, file locking is required
    # to prevent race conditions when generating keys. For single worker, locking is unnecessary.
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


class OpenIdConfigsForDevOnly:
    private_key: str
    public_key: str

    @classmethod
    def _validate_private_key_pem(cls, private_key: str) -> None:
        serialization.load_pem_private_key(private_key.encode(), password=None)

    @classmethod
    def _validate_public_key_pem(cls, public_key: str) -> None:
        serialization.load_pem_public_key(public_key.encode())

    @classmethod
    def _validate_key_pair(cls, private_key: str, public_key: str) -> tuple[str, str] | None:
        try:
            cls._validate_private_key_pem(private_key)
            cls._validate_public_key_pem(public_key)
        except (TypeError, ValueError, UnsupportedAlgorithm):
            return None
        return (private_key, public_key)

    @classmethod
    def _write_validated_pem_atomically(cls, path: Path, pem_contents: str, mode: int, validator: Callable[[str], None]) -> None:
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

    @classmethod
    def _expected_worker_count(cls) -> int:
        configured_count = current_app.config.get("SPIFFWORKFLOW_BACKEND_SERVER_WORKER_COUNT", 1)
        try:
            return int(configured_count)
        except ValueError:
            return 1

    @classmethod
    def _key_cache_dir(cls) -> Path:
        configured_dir = os.getenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_CACHE_DIR")
        if configured_dir:
            return Path(configured_dir)
        return Path(tempfile.gettempdir()) / "spiffworkflow-dev-openid-keys"

    @classmethod
    def _key_paths(cls) -> tuple[Path, Path, Path]:
        key_dir = cls._key_cache_dir()
        return (
            key_dir / "openid-private.pem",
            key_dir / "openid-public.pem",
            key_dir / ".lock",
        )

    @classmethod
    def _read_key_pair_from_files(cls, private_key_path: Path, public_key_path: Path) -> tuple[str, str] | None:
        if private_key_path.exists() and public_key_path.exists():
            return cls._validate_key_pair(private_key_path.read_text(), public_key_path.read_text())
        return None

    @classmethod
    def _load_or_create_file_backed_keys_with_lock(cls) -> tuple[str, str]:
        private_key_path, public_key_path, lock_path = cls._key_paths()
        private_key_path.parent.mkdir(parents=True, exist_ok=True)

        with lock_path.open("w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

            existing_keys = cls._read_key_pair_from_files(private_key_path, public_key_path)
            if existing_keys is not None:
                return existing_keys

            private_key, public_key = cls._generate_keys()
            cls._write_validated_pem_atomically(private_key_path, private_key, 0o600, cls._validate_private_key_pem)
            cls._write_validated_pem_atomically(public_key_path, public_key, 0o644, cls._validate_public_key_pem)
            return (private_key, public_key)

    @classmethod
    def _load_or_create_file_backed_keys_without_lock(cls) -> tuple[str, str]:
        private_key_path, public_key_path, _lock_path = cls._key_paths()
        private_key_path.parent.mkdir(parents=True, exist_ok=True)

        existing_keys = cls._read_key_pair_from_files(private_key_path, public_key_path)
        if existing_keys is not None:
            return existing_keys

        private_key, public_key = cls._generate_keys()
        cls._write_validated_pem_atomically(private_key_path, private_key, 0o600, cls._validate_private_key_pem)
        cls._write_validated_pem_atomically(public_key_path, public_key, 0o644, cls._validate_public_key_pem)
        return (private_key, public_key)

    @classmethod
    def _load_or_create_file_backed_keys(cls) -> tuple[str, str]:
        if not HAS_FCNTL:
            if cls._expected_worker_count() > 1:
                raise RuntimeError(
                    "Built-in OpenID dev keys require SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY "
                    "and SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY when running with multiple workers "
                    "on platforms without fcntl-based file locking."
                )
            return cls._load_or_create_file_backed_keys_without_lock()

        return cls._load_or_create_file_backed_keys_with_lock()

    @classmethod
    def _generate_keys(cls) -> tuple[str, str]:
        """Generate ephemeral RSA key pair for development."""
        try:
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

    @classmethod
    def _initialize_keys(cls) -> tuple[str, str]:
        """Initialize keys from environment or load a shared cached keypair."""
        private_key = os.getenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY")
        public_key = os.getenv("SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY")

        if private_key and not public_key:
            raise RuntimeError(
                "SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY is set but SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY is missing."
            )

        if public_key and not private_key:
            raise RuntimeError(
                "SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY is set but SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY is missing."
            )

        if private_key and public_key:
            validated_key_pair = cls._validate_key_pair(private_key, public_key)
            if validated_key_pair is not None:
                return validated_key_pair
            raise RuntimeError(
                "SPIFFWORKFLOW_BACKEND_OPEN_ID_PRIVATE_KEY and SPIFFWORKFLOW_BACKEND_OPEN_ID_PUBLIC_KEY "
                "are set but contain invalid key data. Provide valid PEM-encoded RSA keys or unset "
                "these variables to use generated keys."
            )

        return cls._load_or_create_file_backed_keys()


# Initialize keys at module load time
OpenIdConfigsForDevOnly.private_key, OpenIdConfigsForDevOnly.public_key = OpenIdConfigsForDevOnly._initialize_keys()
