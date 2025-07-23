from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, ForeignKey, Text
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from manifold_core.models.base import Base

class UnifiServer(Base):
    __tablename__ = "unifi_servers"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, default=443, nullable=False)
    sites = relationship("UnifiSite", back_populates="server", cascade="all, delete-orphan")
    admins = relationship("UnifiAdmin", back_populates="server", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('host', 'port', name='uq_unifi_host_port'),
    )

    def __repr__(self):
        return f"<UnifiServer name={self.name} host={self.host} port={self.port}>"

class UnifiSite(Base):
    __tablename__ = "unifi_sites"

    id = Column(String, primary_key=True) 
    name = Column(String, nullable=False)
    desc = Column(String, nullable=True)
    role = Column(String, nullable=True)
    server_id = Column(Integer, ForeignKey("unifi_servers.id"), nullable=False)
    active = Column(String, default="true", nullable=True)  # "true" or "false"

    server = relationship("UnifiServer", back_populates="sites")

    __table_args__ = (
        UniqueConstraint("id", "server_id", name="uq_site_per_server"),
    )
    
class UnifiAdmin(Base):
    __tablename__ = "unifi_admins"

    id = Column(String, primary_key=True)  # maps to _id in UniFi
    name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_super = Column(String, nullable=True)  # "true" or "false" from UniFi API
    server_id = Column(Integer, ForeignKey("unifi_servers.id"), nullable=False)
    active = Column(String, default="true", nullable=True)  # "true" or "false"

    server = relationship("UnifiServer", back_populates="admins")
    site_permissions = relationship("UnifiAdminSitePermission", back_populates="admin", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("id", "server_id", name="uq_admin_per_server"),
    )


class UnifiAdminSitePermission(Base):
    __tablename__ = "unifi_admin_site_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String, ForeignKey("unifi_admins.id"), nullable=False)
    site_id = Column(String, ForeignKey("unifi_sites.id"), nullable=False)
    site_name = Column(String, nullable=False)  # UniFi site name
    site_desc = Column(String, nullable=True)   # UniFi site description
    role = Column(String, nullable=True)        # Role within this site
    permissions = Column(Text, nullable=True)   # JSON string of permissions

    admin = relationship("UnifiAdmin", back_populates="site_permissions")
    site = relationship("UnifiSite")

    __table_args__ = (
        UniqueConstraint("admin_id", "site_id", name="uq_admin_site_permission"),
    )

class UnifiDevice(Base):
    __tablename__ = "unifi_devices"

    id = Column(String, primary_key=True)  # maps to _id in UniFi
    site_id = Column(String, ForeignKey("unifi_sites.id"), nullable=False)
    name = Column(String)
    type = Column(String)
    model = Column(String)
    serial = Column(String)
    last_seen = Column(Integer)  # Unix timestamp
    state = Column(Integer)
    uptime = Column(Integer)
    firmware_version = Column(String)
    uplink_json = Column(Text)  # serialized JSON string
    downlink_json = Column(Text)  # serialized JSON string
    active = Column(String, default="true", nullable=True)  # "true" or "false"


class UnifiDeviceMac(Base):
    __tablename__ = "unifi_device_macs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("unifi_devices.id"), nullable=False)
    mac_address = Column(String)


class UnifiDeviceIP(Base):
    __tablename__ = "unifi_device_ips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("unifi_devices.id"), nullable=False)
    ip_address = Column(String)


class UnifiAlertKey(Base):
    __tablename__ = "unifi_alert_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)  # e.g., "EVT_SW_Lost_Contact"
    description = Column(String, nullable=True)  # User-defined description


class UnifiAlert(Base):
    __tablename__ = "unifi_alerts"

    id = Column(String, primary_key=True)  # maps to _id in UniFi
    site_id = Column(String, ForeignKey("unifi_sites.id"), nullable=False)
    key_id = Column(Integer, ForeignKey("unifi_alert_keys.id"), nullable=True)
    device_id = Column(String, ForeignKey("unifi_devices.id"), nullable=True)  # Linked device if MAC found
    
    msg = Column(Text, nullable=False)  # Alert message
    archived = Column(String, nullable=False)  # "true" or "false" from UniFi
    time = Column(Integer, nullable=False)  # Unix timestamp
    datetime = Column(String, nullable=False)  # ISO datetime string
    is_negative = Column(String, nullable=False)  # "true" or "false" from UniFi
    key = Column(String, nullable=False)  # Alert key from UniFi
    active = Column(String, default="true", nullable=True)  # "true" or "false"

    site = relationship("UnifiSite")
    alert_key = relationship("UnifiAlertKey")
    device = relationship("UnifiDevice")

    __table_args__ = (
        UniqueConstraint("id", "site_id", name="uq_alert_per_site"),
    )