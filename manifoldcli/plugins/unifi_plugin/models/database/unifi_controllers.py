from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase

class UniFi_Controllers(DBBase):
    __tablename__ = 'unifi_controllers'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String, unique=True)
    host = Column(String, unique=True) #fqhn
    port = Column(Integer)
    is_active = Column(Boolean, default=True)
    last_full_sync = Column(DateTime)
    sites: Mapped[List["UniFi_Sites"]] = relationship(back_populates="controller")