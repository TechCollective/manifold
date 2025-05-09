from typing import List, Dict, Any

from manifold_core.models.base import SessionLocal
from manifold_core.plugins.unifi.models import UnifiServer
from manifold_core.secrets.get import get_secret_backend


class ServerInfo:
    def __init__(self, server: UnifiServer, has_credentials: bool):
        self.id = server.id
        self.name = server.name
        self.host = server.host
        self.port = server.port
        self.has_credentials = has_credentials


def list_unifi_servers() -> List[ServerInfo]:
    session = SessionLocal()
    servers = session.query(UnifiServer).all()
    secrets = get_secret_backend()
    result = []

    for s in servers:
        has_username = secrets.has_secret(f"unifi:{s.name}:username")
        has_password = secrets.has_secret(f"unifi:{s.name}:password")
        result.append(ServerInfo(s, has_username and has_password))

    session.close()
    return result


def add_unifi_server(name: str, host: str, port: int) -> UnifiServer:
    session = SessionLocal()

    # Prevent duplicate name or host:port combinations
    existing = session.query(UnifiServer).filter(
        (UnifiServer.name == name)
        | ((UnifiServer.host == host) & (UnifiServer.port == port))
    ).first()
    if existing:
        session.close()
        raise ValueError("Server with this name or host:port already exists")

    server = UnifiServer(name=name, host=host, port=port)
    session.add(server)
    session.commit()
    session.refresh(server)
    session.close()
    return server


def edit_unifi_server(server_id: int, data: Dict[str, Any]) -> None:
    session = SessionLocal()
    server = session.query(UnifiServer).filter(UnifiServer.id == server_id).first()
    if not server:
        session.close()
        raise ValueError("Server not found")

    if "name" in data:
        server.name = data["name"]
    if "host" in data:
        server.host = data["host"]
    if "port" in data:
        server.port = data["port"]

    session.commit()
    session.close()


def delete_unifi_server(server_id: int) -> None:
    session = SessionLocal()
    server = session.query(UnifiServer).filter(UnifiServer.id == server_id).first()
    if not server:
        session.close()
        raise ValueError("Server not found")

    session.delete(server)
    session.commit()
    session.close()


def set_unifi_credentials(server_id: int, username: str, password: str) -> None:
    session = SessionLocal()
    server = session.query(UnifiServer).filter(UnifiServer.id == server_id).first()
    session.close()

    if not server:
        raise ValueError("Server not found")

    secrets = get_secret_backend()
    secrets.set_secret(f"unifi:{server.name}:username", username)
    secrets.set_secret(f"unifi:{server.name}:password", password)
