import os
from manifold_core.secrets.base import SecretBackend
from manifold_core.secrets.bitwarden.helper import BitwardenHelper


class Backend(SecretBackend):
    def __init__(self):
        self.project_id = os.getenv("BW_PROJECT_ID")

    def get_secret(self, name):
        return BitwardenHelper(self.project_id).get_secret(name)

    def set_secret(self, name, value):
        return BitwardenHelper(self.project_id).create_secret(name, value)

    def has_secret(self, key: str) -> bool:
        return BitwardenHelper(self.project_id).has_secret(key)

    def delete_secret(self, name: str):
        return BitwardenHelper(self.project_id).delete_secret(name)