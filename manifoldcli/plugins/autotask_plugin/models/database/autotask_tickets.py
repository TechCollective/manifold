from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase
from ...models.database import *

class Autotask_Tickets(DBBase):
    __tablename__ = 'autotask_tickets'
    primary_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_number = Column(String, nullable=False)
    autotask_tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))
    alert_key: Mapped[int] = mapped_column(ForeignKey("alerts.primary_key"))

