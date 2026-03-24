# These configs are specifically for the open id server run from backend.
# This should only be used for development and demonstration. SHOULD NOT BE USED IN PROD.

import os


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
    """Initialize keys from environment or generate them."""
    private_key = os.getenv("OPENID_PRIVATE_KEY")
    public_key = os.getenv("OPENID_PUBLIC_KEY")

    if not private_key or not public_key:
        # Generate keys if not provided via environment
        private_key, public_key = _generate_keys()

    return private_key, public_key


class OpenIdConfigsForDevOnly:
    # Initialize keys at module load time
    private_key, public_key = _initialize_keys()
