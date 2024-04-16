from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase
from ...models.database import *

class Autotask_Devices(DBBase):
    __tablename__ = 'autotask_devices'
#    __table_args__ = (UniqueConstraint('autotask_device_id', 'autotask_company_key', name='_unique_autotask_device_id_autotask_company_key'),)
    primary_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    autotask_device_id = Column(String, nullable=False)
    autotask_company_key: Mapped[int] = mapped_column(ForeignKey("autotask_companies.primary_key"))

    device_key: Mapped[int] = mapped_column(ForeignKey("devices.primary_key"))
    parent = relationship("Devices", foreign_keys=[device_key])

