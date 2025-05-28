from manifold_core.plugins.autotask.models import AutotaskIntegrationDB
from manifold_core.secrets.get import get_secret_backend
import requests


class AutotaskAPI:
    def __init__(self, integration: AutotaskIntegrationDB):
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

    def get_ticket(self, ticket_id: str) -> dict:
        """Fetch ticket details from Autotask by ID."""
        username, secret = self._get_credentials()
        integration_code = self.secrets.get_secret(
            f"autotask:{self.integration.name}:integration_code"
        )

        url = f"{self.integration.api_url}/tickets/{ticket_id}"
        headers = {
            "Content-Type": "application/json",
            "ApiIntegrationcode": integration_code,
            "UserName": username,
            "Secret": secret
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Autotask API error: {response.status_code} - {response.text}")

        return response.json()