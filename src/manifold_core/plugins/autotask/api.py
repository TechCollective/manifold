from pyautotask.atsite import ATSite
from manifold_core.plugins.autotask.models import AutotaskIntegrationDB
from manifold_core.secrets.get import get_secret_backend
import requests


class AutotaskAPI:
    def __init__(self, integration: AutotaskIntegrationDB):
        self.integration = integration
        self.secrets = get_secret_backend()

    def _get_credentials(self):
        username = self.secrets.get_secret(f"autotask:{self.integration.name}:username")
        integration_code = self.secrets.get_secret(f"autotask:{self.integration.name}:integration_code")
        secret = self.secrets.get_secret(f"autotask:{self.integration.name}:secret")
        return username, integration_code, secret

    def _build_client(self) -> ATSite:
        username, integration_code, secret = self._get_credentials()
        return ATSite(
            api_url=self.integration.api_url,
            username=username,
            integration_code=integration_code,
            secret=secret,
        )

    def _get_api(self):
        username, integration_code, secret = self._get_credentials()
        return PyAutotaskAPI(
            username=username,
            integration_code=integration_code,
            secret=secret,
            base_url=self.integration.api_url,
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


    # Placeholder for future API validation
    def test_connection(self) -> bool:
        try:
            username, secret = self._get_credentials()
            # Add connection test logic here later
            return bool(username and secret)
        except Exception:
            return False
    
    def get_ticket(self, ticket_id: int) -> dict:
        api = self._get_api()
        ticket = api.get("Tickets", ticket_id)
        return ticket