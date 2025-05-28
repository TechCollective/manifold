import os
from importlib import import_module
from importlib.util import find_spec
from dotenv import load_dotenv

load_dotenv()

# Determine which backend to use
BACKEND = os.getenv("MANIFOLD_SECRETS_BACKEND", "dotenv")
BACKEND_PATH = f"manifold_core.secrets.{BACKEND}"

def _load_provider():
    """Safely load the configured secrets backend module."""
    if not find_spec(BACKEND_PATH):
        raise ImportError(
            f"[manifold_core] Secret backend '{BACKEND}' not found.\n"
            f"→ Set MANIFOLD_SECRETS_BACKEND=dotenv or bitwarden (or implement '{BACKEND_PATH}.py')"
        )

    provider = import_module(BACKEND_PATH)

    required_methods = ["get_secret"]
    for method in required_methods:
        if not hasattr(provider, method):
            raise AttributeError(
                f"[manifold_core] Secret backend '{BACKEND}' is missing required method: '{method}'"
            )

    return provider

def get_secret(key: str) -> str:
    """Retrieve a secret from the configured backend."""
    return _load_provider().get_secret(key)

def set_secret(key: str, value: str):
    """Store a secret in the configured backend (if supported)."""
    provider = _load_provider()
    if not hasattr(provider, "set_secret"):
        raise NotImplementedError(
            f"[manifold_core] 'set_secret' is not implemented in backend '{BACKEND}'"
        )
    return provider.set_secret(key, value)

def delete_secret(key: str):
    """Delete a secret from the configured backend (if supported)."""
    provider = _load_provider()
    if not hasattr(provider, "delete_secret"):
        raise NotImplementedError(
            f"[manifold_core] 'delete_secret' is not implemented in backend '{BACKEND}'"
        )
    return provider.delete_secret(key)
