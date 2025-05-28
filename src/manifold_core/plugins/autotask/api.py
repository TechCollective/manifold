from manifold_core.plugins.autotask.models import AutotaskIntegration
from manifold_core.secrets.get import get_secret_backend


class AutotaskAPI:
    def __init__(self, integration: AutotaskIntegration):
        self.integration = integration
        self.secrets = get_secret_backend()

    def _get_credentials(self):
        username = self.secrets.get_secret(f"autotask:{self.integration.name}:username")
        secret = self.secrets.get_secret(f"autotask:{self.integration.name}:secret")
        return username, secret

    def save_credentials(self, username: str, secret: str):
        self.secrets.set_secret(f"autotask:{self.integration.name}:username", username)
        self.secrets.set_secret(f"autotask:{self.integration.name}:secret", secret)

    def delete_credentials(self):
        self.secrets.delete_secret(f"autotask:{self.integration.name}:username")
        self.secrets.delete_secret(f"autotask:{self.integration.name}:secret")

    def has_credentials(self) -> bool:
        return (
            self.secrets.has_secret(f"autotask:{self.integration.name}:username") and
            self.secrets.has_secret(f"autotask:{self.integration.name}:secret")
        )

    # Placeholder for future API validation
    def test_connection(self) -> bool:
        try:
            username, secret = self._get_credentials()
            # Add connection test logic here later
            return bool(username and secret)
        except Exception:
            return False
