from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from manifold_core.models.base import SessionLocal
from manifold_core.secrets.get import get_secret_backend
from pyunifi.controller import Controller
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from manifold_core.plugins.unifi.models import (
    UnifiDevice,
    UnifiDeviceMac,
    UnifiDeviceIP,
    UnifiSite,
    UnifiServer
)
import re


def sync_unifi_devices():
    session: Session = SessionLocal()
    servers = session.query(UnifiServer).all()
    secrets = get_secret_backend()

    total_devices = 0

    for server in servers:
        try:
            username = secrets.get_secret(f"unifi:{server.name}:username")
            password = secrets.get_secret(f"unifi:{server.name}:password")

            controller = Controller(
                host=server.host,
                username=username,
                password=password,
                port=server.port,
                ssl_verify=True
            )

            # Get sites from DB that belong to this server
            sites = session.query(UnifiSite).filter_by(server_id=server.id).all()

            for site in sites:
                controller.site_id=site.id
                devices = controller.get_aps()

                for device in devices:
                    total_devices += 1
                    # Update or create UnifiDevice
                    db_device = session.query(UnifiDevice).filter_by(id=device["_id"]).first()
                    if not db_device:
                        db_device = UnifiDevice(id=device["_id"], site_id=site.id)
                        session.add(db_device)

                    db_device.name = device.get("name")
                    db_device.type = device.get("type")
                    db_device.model = device.get("model")
                    db_device.serial = device.get("serial")
                    db_device.last_seen = device.get("last_seen")
                    db_device.state = device.get("state")
                    db_device.uptime = device.get("uptime")
                    db_device.firmware_version = device.get("version")
                    db_device.uplink_json = json.dumps(device.get("uplink_table", []))
                    db_device.downlink_json = json.dumps(device.get("downlink_table", []))

                    # Clear old MACs and IPs
                    session.query(UnifiDeviceMac).filter_by(device_id=db_device.id).delete()
                    session.query(UnifiDeviceIP).filter_by(device_id=db_device.id).delete()

                    # Add MACs
                    macs = device.get("mac_table") or [device.get("mac")]
                    for mac in macs:
                        if mac:
                            session.add(UnifiDeviceMac(device_id=db_device.id, mac_address=mac))

                    # Add IPs
                    ips = device.get("ip_table") or [device.get("ip")]
                    for ip in ips:
                        if ip:
                            session.add(UnifiDeviceIP(device_id=db_device.id, ip_address=ip))

            session.commit()

        except Exception as e:
            session.rollback()
            print(f"[sync_unifi_devices] Failed for server {server.name}: {e}")

    session.close()
    return total_devices

def normalize_mac(identifier: str) -> str:
    """Strip non-hex characters and lowercase."""
    return re.sub(r'[^a-fA-F0-9]', '', identifier).lower()

def sync_unifi_devices():
    session: Session = SessionLocal()
    servers = session.query(UnifiServer).all()
    secrets = get_secret_backend()

    total_devices = 0

    for server in servers:
        try:
            username = secrets.get_secret(f"unifi:{server.name}:username")
            password = secrets.get_secret(f"unifi:{server.name}:password")

            controller = Controller(
                host=server.host,
                username=username,
                password=password,
                port=server.port,
                ssl_verify=True
            )

            # Get sites from DB that belong to this server
            sites = session.query(UnifiSite).filter_by(server_id=server.id).all()

            for site in sites:
                controller.site_id = site.id
                devices = controller.get_aps()

                for device in devices:
                    total_devices += 1
                    # Update or create UnifiDevice
                    db_device = session.query(UnifiDevice).filter_by(id=device["_id"]).first()
                    if not db_device:
                        db_device = UnifiDevice(id=device["_id"], site_id=site.id)
                        session.add(db_device)

                    db_device.name = device.get("name")
                    db_device.type = device.get("type")
                    db_device.model = device.get("model")
                    db_device.serial = device.get("serial")
                    db_device.last_seen = device.get("last_seen")
                    db_device.state = device.get("state")
                    db_device.uptime = device.get("uptime")
                    db_device.firmware_version = device.get("version")
                    db_device.uplink_json = json.dumps(device.get("uplink_table", []))
                    db_device.downlink_json = json.dumps(device.get("downlink_table", []))

                    # Clear old MACs and IPs
                    session.query(UnifiDeviceMac).filter_by(device_id=db_device.id).delete()
                    session.query(UnifiDeviceIP).filter_by(device_id=db_device.id).delete()

                    # Add MACs
                    macs = device.get("mac_table") or [device.get("mac")]
                    for mac in macs:
                        if mac:
                            session.add(UnifiDeviceMac(device_id=db_device.id, mac_address=mac))

                    # Add IPs
                    ips = device.get("ip_table") or [device.get("ip")]
                    for ip in ips:
                        if ip:
                            session.add(UnifiDeviceIP(device_id=db_device.id, ip_address=ip))

            session.commit()

        except Exception as e:
            session.rollback()
            print(f"[sync_unifi_devices] Failed for server {server.name}: {e}")

    session.close()
    return total_devices

def format_seconds(seconds: Optional[int]) -> str:
    if not seconds:
        return "N/A"
    return str(timedelta(seconds=seconds))

def format_timestamp(timestamp: Optional[int]) -> str:
    if not timestamp:
        return "N/A"
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')

def lookup_unifi_device(identifier: str) -> Optional[Dict[str, Any]]:
    session: Session = SessionLocal()
    normalized = normalize_mac(identifier)
    device = None
    
    # Try MAC match first
    mac_entries = session.query(UnifiDeviceMac).all()
    for mac in mac_entries:
        if normalize_mac(mac.mac_address) == normalized:
            device = session.query(UnifiDevice).filter_by(id=mac.device_id).first()
            break
    # If not found, try serial match
    if not device:
        device = session.query(UnifiDevice).filter_by(serial=identifier).first()
    if not device:
        session.close()
        return {"error": "Device not found."}

    site = session.query(UnifiSite).filter_by(id=device.site_id).first()
    server = session.query(UnifiServer).filter_by(id=site.server_id).first()

    macs = [m.mac_address for m in session.query(UnifiDeviceMac).filter_by(device_id=device.id)]
    ips = [i.ip_address for i in session.query(UnifiDeviceIP).filter_by(device_id=device.id)]

    session.close()

    return {
        "server": server.name,
        "site": site.name,
        "site_desc": site.desc,
        "name": device.name,
        "serial": device.serial,
        "macs": macs,
        "ips": ips,
        "model": device.model,
        "last_seen": format_timestamp(device.last_seen),
        "uptime": format_seconds(device.uptime),
        "state": device.state
    }
