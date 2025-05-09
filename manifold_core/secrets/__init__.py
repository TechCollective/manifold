import os
from importlib import import_module
from importlib.util import find_spec
from manifold_core.secrets.base import SecretBackend

BACKEND = os.getenv("MANIFOLD_SECRETS_BACKEND", "dotenv")
BACKEND_PATH = f"manifold_core.secrets.{BACKEND}"

def get_secret(key: str) -> str:
    if not find_spec(BACKEND_PATH):
        raise ImportError(
            f"[manifold_core] Secret backend '{BACKEND}' not found.\n"
            f"→ Set MANIFOLD_SECRETS_BACKEND=dotenv or bitwarden (or implement '{BACKEND_PATH}.py')"
        )

    module = import_module(BACKEND_PATH)

    if not hasattr(module, "Backend"):
        raise AttributeError(f"[manifold_core] '{BACKEND}' must define a class 'Backend'")

    backend_instance = module.Backend()

    if not isinstance(backend_instance, SecretBackend):
        raise TypeError(f"[manifold_core] '{BACKEND}.Backend' must inherit from SecretBackend")

    return backend_instance.get_secret(key)
