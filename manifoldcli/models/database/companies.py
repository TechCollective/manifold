from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db_base import DBBase

class Companies(DBBase):
    __tablename__ = 'companies'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String)
    number = Column(String)

