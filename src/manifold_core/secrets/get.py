# manifold_core/secrets/get.py
import os
from manifold_core.secrets.dotenv.backend import Backend as DotenvBackend
from manifold_core.secrets.bitwarden.backend import Backend as BitwardenBackend

def get_secret_backend():
    backend = os.getenv("MANIFOLD_SECRETS_BACKEND", "dotenv").lower()
    if backend == "bitwarden":
        return BitwardenBackend()
    return DotenvBackend()
