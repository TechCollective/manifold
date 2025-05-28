from pyautotask import atsite
from manifold_core.plugins.autotask.models import AutotaskIntegrationDB
from manifold_core.secrets.get import get_secret_backend


class AutotaskAPI:
    def __init__(self, integration: AutotaskIntegrationDB):
        self.integration = integration
        self.secrets = get_secret_backend()

    def _get_credentials(self):
        username = self.secrets.get_secret(f"autotask:{self.integration.name}:username")
        integration_code = self.secrets.get_secret(f"autotask:{self.integration.name}:integration_code")
        secret = self.secrets.get_secret(f"autotask:{self.integration.name}:secret")
        return username, integration_code, secret

    def _build_client(self) -> atsite.atSite:
        username, integration_code, secret = self._get_credentials()
        return atsite.atSite(
            api_url=self.integration.api_url,
            username=username,
            integration_code=integration_code,
            secret=secret,
        )

    def save_credentials(self, username: str, integration_code: str, secret: str):
        self.secrets.set_secret(f"autotask:{self.integration.name}:username", username)
        self.secrets.set_secret(f"autotask:{self.integration.name}:integration_code", integration_code)
        self.secrets.set_secret(f"autotask:{self.integration.name}:secret", secret)

    def delete_credentials(self):
        for key in ["username", "integration_code", "secret"]:
            try:
                self.secrets.delete_secret(f"autotask:{self.integration.name}:{key}")
            except ValueError:
                pass  # Allow graceful deletion even if some secrets don't exist

    def has_credentials(self) -> bool:
        return all(
            self.secrets.has_secret(f"autotask:{self.integration.name}:{key}")
            for key in ["username", "integration_code", "secret"]
        )

    def test_connection(self) -> bool:
        try:
            client = self._build_client()
            # Implement a simple API call to test the connection, e.g., fetching a known resource
            # For example:
            # response = client.get("Tickets", 1)
            # return response is not None
            return True  # Placeholder
        except Exception:
            return False

    def get_ticket(self, ticket_id: int) -> dict:
        client = self._build_client()
        return client.get("Tickets", ticket_id)
