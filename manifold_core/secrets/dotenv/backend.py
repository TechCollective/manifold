import os
from manifold_core.secrets.dotenv.backend import load_dotenv
from manifold_core.secrets.base import SecretBackend

load_dotenv()

class Backend(SecretBackend):
    def get_secret(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise KeyError(f"Missing required secret: {key}")
        return value
