import os
from dotenv import load_dotenv
from manifold_core.secrets.base import SecretBackend

load_dotenv()

class Backend(SecretBackend):
    def get_secret(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise KeyError(f"Missing required secret: {key}")
        return value
    
    def has_secret(self, key: str) -> bool:
        """Check if an environment variable exists and has a value"""
        value = os.getenv(key)
        return value is not None and value.strip() != ""
