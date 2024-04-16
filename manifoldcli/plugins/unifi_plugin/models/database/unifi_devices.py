from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase
from ...models.database import *

class UniFi_Devices(DBBase):
    __tablename__ = 'unifi_devices'
    __table_args__ = (UniqueConstraint('unifi_device_id', 'unifi_sites_key', name='_unique_unifi_device_id_unifi_sites_key'),)
    primary_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    unifi_device_id = Column(String, nullable=False)

    device_key: Mapped[int] = mapped_column(ForeignKey("devices.primary_key"))
    unifi_sites_key: Mapped[int] = mapped_column(ForeignKey("unifi_sites.primary_key"))

    parent = relationship("Devices", foreign_keys=[device_key])

