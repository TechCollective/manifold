# manifold_core/secrets/bitwarden.py

import os
import subprocess
from manifold_core.secrets.base import SecretBackend

class Backend(SecretBackend):
    def get_secret(self, key: str) -> str:
        project_id = os.getenv("BW_PROJECT_ID")
        if not project_id:
            raise RuntimeError("BW_PROJECT_ID not set")

        try:
            return subprocess.check_output(
                ["bwsm", "secrets", "get", "--project-id", project_id, "--name", key],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            raise KeyError(f"Secret '{key}' not found in Bitwarden Secrets Manager")
