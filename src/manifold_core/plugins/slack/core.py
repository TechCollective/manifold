from typing import List
from manifold_core.models.base import SessionLocal
from manifold_core.plugins.slack.models import SlackIntegrationDB
from manifold_core.secrets.get import get_secret_backend
import logging

logger = logging.getLogger(__name__)

class SlackIntegrationInfo:
    def __init__(self, record: SlackIntegrationDB, has_token: bool):
        self.id = record.id
        self.name = record.name
        self.workspace = record.workspace
        self.has_token = has_token


def list_slack_integrations() -> List[SlackIntegrationInfo]:
    session = SessionLocal()
    records = session.query(SlackIntegrationDB).all()
    
    secrets = get_secret_backend()
    result = []

    for record in records:
        key = f"slack:{record.name}:token"
        token_exists = secrets.has_secret(key)
        result.append(SlackIntegrationInfo(record, token_exists))

    session.close()
    return result


def add_slack_integration(name: str, workspace: str) -> SlackIntegrationDB:
    session = SessionLocal()

    existing = session.query(SlackIntegrationDB).filter_by(name=name).first()
    if existing:
        session.close()
        raise ValueError("Slack integration with this name already exists")

    integration = SlackIntegrationDB(name=name, workspace=workspace)
    session.add(integration)
    session.commit()
    session.refresh(integration)
    session.close()
    return integration


def edit_slack_integration(slack_id: str, data: dict) -> None:
    session = SessionLocal()
    record = session.query(SlackIntegrationDB).filter_by(id=slack_id).first()
    if not record:
        session.close()
        raise ValueError("Integration not found")

    if "name" in data:
        record.name = data["name"]
    if "workspace" in data:
        record.workspace = data["workspace"]

    session.commit()
    session.close()


def delete_slack_integration(slack_id: str) -> None:
    session = SessionLocal()
    record = session.query(SlackIntegrationDB).filter_by(id=slack_id).first()
    if not record:
        session.close()
        raise ValueError("Integration not found")

    # Delete associated token
    secrets = get_secret_backend()
    secrets.delete_secret(f"slack:{record.name}:token")

    session.delete(record)
    session.commit()
    session.close()


def set_slack_token(slack_id: str, token: str) -> None:
    session = SessionLocal()
    record = session.query(SlackIntegrationDB).filter_by(id=slack_id).first()
    session.close()

    if not record:
        raise ValueError("Integration not found")

    secrets = get_secret_backend()
    secrets.set_secret(f"slack:{record.name}:token", token)

def get_slack_name() -> str:
    session = SessionLocal()
    records = session.query(SlackIntegrationDB).all()
    session.close()

    if len(records) == 0:
        raise ValueError("No Slack integrations are configured")
    if len(records) > 1:
        raise ValueError("Multiple Slack integrations found; cannot determine default")

    return records[0].name
