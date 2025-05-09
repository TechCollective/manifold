import os
from importlib import import_module
from importlib.util import find_spec

# Environment-configurable secret backend
BACKEND = os.getenv("MANIFOLD_SECRETS_BACKEND", "dotenv")
BACKEND_PATH = f"manifold_core.secrets.{BACKEND}"

def get_secret(key: str) -> str:
    if not find_spec(BACKEND_PATH):
        raise ImportError(
            f"[manifold_core] Secret backend '{BACKEND}' not found.\n"
            f"→ Set MANIFOLD_SECRETS_BACKEND=dotenv or bitwarden (or implement '{BACKEND_PATH}.py')"
        )

    provider = import_module(BACKEND_PATH)

    if not hasattr(provider, "get_secret"):
        raise AttributeError(
            f"[manifold_core] Secret backend '{BACKEND}' is missing a 'get_secret()' function."
        )

    return provider.get_secret(key)
