from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase

class Autotask_Tenants(DBBase):
    __tablename__ = 'autotask_tenants'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String, unique=True)
    host = Column(String, unique=True) #fqhn
    is_active = Column(Boolean, default=True)
    last_full_sync = Column(DateTime, nullable=True)
