from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db_base import DBBase

class Sources(DBBase):
    __tablename__ = 'sources'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    plugin_name = Column(String, nullable=False)
    tenant_key = Column(Integer, nullable=False)
