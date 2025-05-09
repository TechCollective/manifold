from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, ForeignKey, Text
from datetime import datetime
from sqlalchemy.orm import relationship
from manifold_core.models.base import Base

class UnifiServer(Base):
    __tablename__ = "unifi_servers"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, default=443, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sites = relationship("UnifiSite", back_populates="server", cascade="all, delete-orphan")

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

    server = relationship("UnifiServer", back_populates="sites")

    __table_args__ = (
        UniqueConstraint("id", "server_id", name="uq_site_per_server"),
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