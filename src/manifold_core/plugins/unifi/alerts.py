from sqlalchemy.orm import Session
from manifold_core.models.base import SessionLocal
from manifold_core.secrets.get import get_secret_backend
from manifold_core.plugins.unifi.models import (
    UnifiAlert,
    UnifiAlertKey,
    UnifiDevice,
    UnifiDeviceMac,
    UnifiSite,
    UnifiServer
)
from pyunifi.controller import Controller
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.sql import func


def extract_mac_from_key(alert_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract MAC address from alert data by checking various key fields.
    Returns the first MAC address found.
    """
    # Known key prefixes that contain MAC addresses
    mac_keys = ['sw', 'ap', 'gw', 'xg', 'bb', 'dev']
    
    for key in mac_keys:
        if key in alert_data and alert_data[key]:
            mac = alert_data[key]
            # Validate it looks like a MAC address
            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
                return mac
    
    return None


def find_device_by_mac(mac: str, session: Session) -> Optional[UnifiDevice]:
    """Find a device by MAC address."""
    if not mac:
        return None
    
    # Normalize the search MAC (remove colons, dashes, etc.)
    normalized_mac = re.sub(r'[^a-fA-F0-9]', '', mac).lower()
    
    # Get all device MACs and normalize them for comparison
    all_macs = session.query(UnifiDeviceMac).all()
    
    for mac_entry in all_macs:
        # Normalize the stored MAC
        stored_normalized = re.sub(r'[^a-fA-F0-9]', '', mac_entry.mac_address).lower()
        
        if stored_normalized == normalized_mac:
            return session.query(UnifiDevice).filter_by(id=mac_entry.device_id).first()
    
    return None


def get_or_create_alert_key(key: str, session: Session) -> UnifiAlertKey:
    """Get existing alert key or create a new one."""
    alert_key = session.query(UnifiAlertKey).filter_by(key=key).first()
    if not alert_key:
        alert_key = UnifiAlertKey(key=key)
        session.add(alert_key)
        session.flush()  # Get the ID
    return alert_key


def sync_unifi_alerts():
    """Sync alerts from all UniFi controllers."""
    session: Session = SessionLocal()
    servers = session.query(UnifiServer).all()
    secrets = get_secret_backend()
    
    total_alerts = 0
    
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
            
            # Get active sites from DB that belong to this server
            sites = session.query(UnifiSite).filter_by(server_id=server.id, active="true").all()
            
            for site in sites:
                try:
                    controller.site_id = site.id
                    
                    # Get all existing alerts for this site
                    existing_alerts = session.query(UnifiAlert).filter_by(site_id=site.id).all()
                    existing_alert_ids = {alert.id for alert in existing_alerts}
                    
                    # Track alerts found in this sync
                    found_alert_ids = set()
                    
                    # Get alerts from UniFi API using pyunifi's built-in function
                    alerts_data = controller.get_alerts_unarchived()
                    
                    if not alerts_data:
                        print(f"No alerts data for site {site.name}")
                        continue
                    print(f"Found {len(alerts_data)} alerts for site {site.name}")
                    
                    for alert_data in alerts_data:
                        alert_id = alert_data.get('_id')
                        if not alert_id:
                            continue
                        
                        found_alert_ids.add(alert_id)
                        
                        # Check if alert already exists
                        existing_alert = session.query(UnifiAlert).filter_by(id=alert_id).first()
                        if existing_alert:
                            existing_alert.active = "true"  # Mark as active since it exists
                            continue  # Skip if already exists
                        
                        # Extract MAC address from alert
                        mac_address = extract_mac_from_key(alert_data)
                        device = None
                        if mac_address:
                            device = find_device_by_mac(mac_address, session)
                        
                        # Get or create alert key
                        alert_key = get_or_create_alert_key(alert_data.get('key', ''), session)
                        
                        # Create new alert
                        alert = UnifiAlert(
                            id=alert_id,
                            site_id=site.id,
                            key_id=alert_key.id if alert_key else None,
                            device_id=device.id if device else None,
                            msg=alert_data.get('msg', ''),
                            archived=str(alert_data.get('archived', False)).lower(),
                            time=alert_data.get('time', 0),
                            datetime=alert_data.get('datetime', ''),
                            is_negative=str(alert_data.get('is_negative', False)).lower(),
                            key=alert_data.get('key', ''),
                            active="true"
                        )
                        
                        session.add(alert)
                        total_alerts += 1
                    
                    # Mark alerts that weren't found as inactive
                    for alert_id in existing_alert_ids - found_alert_ids:
                        alert = session.query(UnifiAlert).filter_by(id=alert_id).first()
                        if alert:
                            alert.active = "false"
                            print(f"Marked alert {alert_id} as inactive (not found in UniFi)")
                    
                    session.commit()
                    
                except Exception as e:
                    session.rollback()
                    print(f"Error syncing alerts for site {site.name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error connecting to server {server.name}: {e}")
            continue
    
    session.close()
    return total_alerts


def get_all_unifi_alerts():
    """Get all active alerts from all servers with site and device information."""
    session: Session = SessionLocal()
    
    alerts = session.query(UnifiAlert, UnifiSite, UnifiDevice, UnifiAlertKey).outerjoin(
        UnifiSite, UnifiAlert.site_id == UnifiSite.id
    ).outerjoin(
        UnifiDevice, UnifiAlert.device_id == UnifiDevice.id
    ).outerjoin(
        UnifiAlertKey, UnifiAlert.key_id == UnifiAlertKey.id
    ).filter(UnifiAlert.active == "true").order_by(UnifiAlert.time.desc()).all()
    
    result = []
    for alert, site, device, alert_key in alerts:
        result.append({
            "id": alert.id,
            "msg": alert.msg,
            "datetime": alert.datetime,
            "archived": alert.archived == "true",
            "is_negative": alert.is_negative == "true",
            "key": alert.key,
            "key_description": alert_key.description if alert_key else None,
            "site_name": site.name if site else "Unknown",
            "site_desc": site.desc if site else "Unknown",
            "device_name": device.name if device else None,
            "device_model": device.model if device else None
        })
    
    session.close()
    return result


def get_alert_keys():
    """Get all alert keys with their descriptions."""
    session: Session = SessionLocal()
    
    keys = session.query(UnifiAlertKey).order_by(UnifiAlertKey.key).all()
    result = []
    
    for key in keys:
        result.append({
            "id": key.id,
            "key": key.key,
            "description": key.description
        })
    
    session.close()
    return result


def update_alert_key_description(key_id: int, description: str):
    """Update the description for an alert key."""
    session: Session = SessionLocal()
    
    alert_key = session.query(UnifiAlertKey).filter_by(id=key_id).first()
    if alert_key:
        alert_key.description = description
        session.commit()
        session.close()
        return True
    
    session.close()
    return False 