from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase
from ...models.database import *

class Autotask_Contracts(DBBase):
    __tablename__ = 'autotask_contracts'
    primary_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    autotask_id = Column(Integer, nullable=False)
    autotask_company_key: Mapped[int] = mapped_column(ForeignKey("autotask_companies.primary_key"))
    contract_category_value: Mapped[int] = mapped_column(ForeignKey("_autotask_contract_category.value"))
    autotask_name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)

