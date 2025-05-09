from manifold_core.secrets.get import get_secret_backend
from manifold_core.plugins.unifi.models import UnifiServer, UnifiSite
from manifold_core.models.base import SessionLocal
from pyunifi.controller import Controller

def get_unifi_sites(server_id: int):
    db = SessionLocal()
    server = db.query(UnifiServer).filter_by(id=server_id).first()
    db.close()

    if not server:
        raise ValueError(f"Server ID {server_id} not found.")

    secrets = get_secret_backend()
    username = secrets.get_secret(f"unifi:{server.name}:username")
    password = secrets.get_secret(f"unifi:{server.name}:password")

    controller = Controller(
        host=server.host,
        username=username,
        password=password,
        port=server.port,
        ssl_verify=True  # defaults to True; only change if debugging
    )

    # pyunifi auto-detects UniFi OS and normalizes site structure
    return controller.get_sites()

def sync_unifi_sites(server_id=None):
    db = SessionLocal()

    if server_id:
        servers = db.query(UnifiServer).filter_by(id=server_id).all()
    else:
        servers = db.query(UnifiServer).all()

    secrets = get_secret_backend()
    count = 0

    for server in servers:
        username = secrets.get_secret(f"unifi:{server.name}:username")
        password = secrets.get_secret(f"unifi:{server.name}:password")
        controller = Controller(server.host, username, password, port=server.port, ssl_verify=True)
        sites = controller.get_sites()

        for site in sites:
            existing = db.query(UnifiSite).filter_by(id=site["name"], server_id=server.id).first()
            if existing:
                existing.desc = site.get("desc", "")
                existing.role = site.get("role", "")
            else:
                new_site = UnifiSite(
                    id=site["name"],
                    name=site["name"],
                    desc=site.get("desc", ""),
                    role=site.get("role", ""),
                    server_id=server.id
                )
                db.add(new_site)
            count += 1

    db.commit()
    db.close()
    return count