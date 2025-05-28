from typing import List
from manifold_core.models.base import SessionLocal
from manifold_core.plugins.autotask.models import AutotaskIntegrationDB
from manifold_core.secrets.get import get_secret_backend
from manifold_core.plugins.autotask.api import AutotaskAPI


class AutotaskIntegrationInfo:
    def __init__(self, record: AutotaskIntegrationDB, has_creds: bool):
        self.id = record.id
        self.name = record.name
        self.api_url = record.api_url
        self.has_credentials = has_creds

def list_autotask_integrations() -> List[AutotaskIntegrationInfo]:
    session = SessionLocal()
    integrations = session.query(AutotaskIntegrationDB).all()
    secrets = get_secret_backend()
    result = []

    for record in integrations:
        has_user = secrets.has_secret(f"autotask:{record.name}:username")
        has_secret = secrets.has_secret(f"autotask:{record.name}:secret")
        result.append(AutotaskIntegrationInfo(record, has_user and has_secret))

    session.close()
    return result

def add_autotask_integration(name: str, api_url: str) -> AutotaskIntegrationDB:
    session = SessionLocal()

    existing = session.query(AutotaskIntegrationDB).filter_by(name=name).first()
    if existing:
        session.close()
        raise ValueError("Autotask integration with this name already exists")

    integration = AutotaskIntegrationDB(name=name, api_url=api_url)
    session.add(integration)
    session.commit()
    session.refresh(integration)
    session.close()
    return integration

def edit_autotask_integration(integration_id: int, data: dict) -> None:
    session = SessionLocal()
    record = session.query(AutotaskIntegrationDB).filter_by(id=integration_id).first()
    if not record:
        session.close()
        raise ValueError("Integration not found")

    if "name" in data:
        record.name = data["name"]
    if "api_url" in data:
        record.api_url = data["api_url"]

    session.commit()
    session.close()

def delete_autotask_integration(autotask_id: int) -> None:
    session = SessionLocal()
    record = session.query(AutotaskIntegrationDB).filter_by(id=autotask_id).first()
    if not record:
        session.close()
        raise ValueError("Integration not found")

    secrets = get_secret_backend()

    # Try deleting username secret
    try:
        secrets.delete_secret(f"autotask:{record.name}:username")
    except ValueError:
        pass  # Secret may not exist — that's fine

    # Try deleting integration code secret
    try:
        secrets.delete_secret(f"autotask:{record.name}:integration_code")
    except ValueError:
        pass

    # Try deleting secret key
    try:
        secrets.delete_secret(f"autotask:{record.name}:secret")
    except ValueError:
        pass

    session.delete(record)
    session.commit()
    session.close()


def set_autotask_credentials(autotask_id: int, username: str, integration_code: str, secret: str) -> None:
    session = SessionLocal()
    record = session.query(AutotaskIntegrationDB).filter_by(id=autotask_id).first()
    session.close()

    if not record:
        raise ValueError("Autotask integration not found")

    secrets = get_secret_backend()
    secrets.set_secret(f"autotask:{record.name}:username", username)
    secrets.set_secret(f"autotask:{record.name}:integration_code", integration_code)
    secrets.set_secret(f"autotask:{record.name}:secret", secret)


def get_ticket(autotask_id: int, ticket_id: int) -> dict:
    session = SessionLocal()
    integration = session.query(AutotaskIntegrationDB).filter_by(id=autotask_id).first()
    session.close()

    if not integration:
        raise ValueError("Autotask integration not found")

    api = AutotaskAPI(integration)
    client = api._build_client()

    results = client.get_ticket_by_id(ticket_id)

    if not results:
        raise ValueError(f"Ticket with ID {ticket_id} not found")

    return results[0]

def extract_udf(ticket: dict, field_name: str) -> str | None:
    """Searches for a user-defined field by name and returns its value."""
    for udf in ticket.get("userDefinedFields", []):
        if udf.get("name") == field_name:
            return udf.get("value")
    return None

def update_ticket_udf(integration_id: int, ticket_id: int, field_name: str, value: str) -> None:
    session = SessionLocal()
    integration = session.query(AutotaskIntegrationDB).filter_by(id=integration_id).first()
    session.close()

    if not integration:
        raise ValueError("Autotask integration not found")

    client = AutotaskAPI(integration)._build_client()

    udf = []
    udf.append({'name': field_name, 'value': value})
    params_udf = {'userDefinedFields': udf}
    params = { "id": ticket_id}
    params.update(params_udf)


    try:
        result = client._api_update("Tickets", params)
        logger.debug(f"Autotask update result: {result}")
    except Exception as e:
        raise Exception(f"Autotask update failed: {e}")

    if not result or result.get("id") != ticket_id:
        raise Exception("Failed to update Autotask ticket UDF")