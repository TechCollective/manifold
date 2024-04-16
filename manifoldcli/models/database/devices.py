from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db_base import *
from .companies import Companies

class Devices_Macs(DBBase):
    __tablename__ = 'devices_macs'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    mac_addresses = Column(String, nullable=False)
    device_key: Mapped[int] = mapped_column(ForeignKey("devices.primary_key"))
    device: Mapped["Devices"] = relationship(back_populates="macs")

class Devices_IP(DBBase):
    __tablename__ = 'devices_ip_addresses'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    ip_addresses = Column(String, nullable=False)
    device_key: Mapped[int] = mapped_column(ForeignKey("devices.primary_key"))
    device: Mapped["Devices"] = relationship(back_populates="ip_addresses")

class Devices(DBBase):
    __tablename__ = 'devices'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String)
    description = Column(String)
    serial = Column(String)
    manufacturer = Column(String)
    model = Column(String)
    install_date = Column(DateTime)
    ip_addresses: Mapped[List["Devices_IP"]] = relationship(back_populates="device")
    macs: Mapped[List["Devices_Macs"]] = relationship(back_populates="device")
    company_key = Column(Integer, ForeignKey('companies.primary_key'), nullable=False)
    company = relationship("Companies", uselist=False)
    alerts = relationship("Alerts", secondary=device_alert_association, back_populates="devices")

    def __repr__(self):
        return f"Devices(id={self.primary_key}, name='{self.name}', serial='{self.serial}', ip_addresses='{self.ip_addresses}', manufacturer='{self.manufacturer}', model='{self.model}')"