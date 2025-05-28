import os
from manifold_core.secrets.bitwarden.backend import Backend

class SlackAPI:
    def __init__(self, name: str):
        self.name = name
        self.secrets = Backend()

    def get_token(self) -> str:
        return self.secrets.get_secret(f"slack:{self.name}:token")

    def save_token(self, token: str):
        self.secrets.set_secret(f"slack:{self.name}:token", token)

    def delete_token(self):
        raise NotImplementedError("Token deletion is not implemented yet.")
