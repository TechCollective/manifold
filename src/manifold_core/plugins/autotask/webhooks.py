from typing import List
from manifold_core.models.base import SessionLocal
from manifold_core.plugins.autotask.models import AutotaskIntegrationDB
from manifold_core.plugins.autotask.api import AutotaskAPI
import logging

logger = logging.getLogger(__name__)

class AutotaskWebhook:
    def __init__(self, id, entity, event, url, is_active):
        self.id = id
        self.entity = entity
        self.event = event
        self.url = url
        self.is_active = is_active

    def __repr__(self):
        return f"<AutotaskWebhook id={self.id} entity={self.entity} event={self.event} active={self.is_active}>"

def list_webhooks(integration_id: int) -> List[AutotaskWebhook]:
    """
    List all webhooks for the given Autotask integration.
    """
    session = SessionLocal()
    integration = session.query(AutotaskIntegrationDB).filter_by(id=integration_id).first()
    session.close()

    if not integration:
        raise ValueError(f"Autotask integration with ID {integration_id} not found.")

    api = AutotaskAPI(integration)
    client = api._build_client()

    try:
        results = client._api_get("Webhooks")
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve webhooks: {e}")

    if not results:
        return []

    return [
        AutotaskWebhook(
            id=item.get("id"),
            entity=item.get("entity"),
            event=item.get("event"),
            url=item.get("url"),
            is_active=item.get("isActive", False)
        )
        for item in results
    ]
