import os

def get_base_url():
    """Returns the base URL for the application, configurable via environment variable."""
    return os.getenv("E2E_URL", "http://localhost:7001")
