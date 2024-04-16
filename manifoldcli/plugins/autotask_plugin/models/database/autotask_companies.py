from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase
from ...models.database import *

class Autotask_Companies(DBBase):
    __tablename__ = 'autotask_companies'
    __table_args__ = (UniqueConstraint('autotask_company_id', 'autotask_tenant_key', name='_unique_autotask_company_id_autotask_tenant_key'),)
    primary_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    autotask_company_id = Column(String, nullable=False)
    autotask_tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))

    company_key = Column(Integer, ForeignKey('companies.primary_key'))
    parent = relationship("Companies", foreign_keys=[company_key])

