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

        # Get all existing sites for this server
        existing_sites = db.query(UnifiSite).filter_by(server_id=server.id).all()
        existing_site_ids = {site.id for site in existing_sites}
        
        # Track sites found in this sync
        found_site_ids = set()

        for site in sites:
            site_id = site["name"]
            found_site_ids.add(site_id)
            
            existing = db.query(UnifiSite).filter_by(id=site_id, server_id=server.id).first()
            if existing:
                existing.desc = site.get("desc", "")
                existing.role = site.get("role", "")
                existing.active = "true"  # Mark as active since it exists
            else:
                new_site = UnifiSite(
                    id=site_id,
                    name=site_id,
                    desc=site.get("desc", ""),
                    role=site.get("role", ""),
                    server_id=server.id,
                    active="true"
                )
                db.add(new_site)
            count += 1

        # Mark sites that weren't found as inactive
        for site_id in existing_site_ids - found_site_ids:
            site = db.query(UnifiSite).filter_by(id=site_id, server_id=server.id).first()
            if site:
                site.active = "false"

    db.commit()
    db.close()
    return count


def get_all_unifi_sites():
    """Get all active sites from all servers."""
    session = SessionLocal()
    sites = session.query(UnifiSite).join(UnifiServer).filter(UnifiSite.active == "true").all()
    result = []
    for site in sites:
        result.append({
            "name": site.name,
            "desc": site.desc,
            "role": site.role,
            "server": site.server.name
        })
    session.close()
    return result