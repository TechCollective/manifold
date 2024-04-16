from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db_base import *
from .sources import Sources
from .companies import Companies

class AlertTypes(DBBase):
    __tablename__ = 'alert_types'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String)

class Alerts(DBBase):
    __tablename__ = 'alerts'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    alert_type_key = Column(Integer, ForeignKey('alert_types.primary_key'), nullable=False)
    alert_type = relationship("AlertTypes", uselist=False)
    title_append = Column(String)
    useful_information = Column(String)
    source_key = Column(Integer, ForeignKey('sources.primary_key'), nullable=False)
    source = relationship("Sources", uselist=False)
    start_timestamp = Column(DateTime(timezone=True))
    last_timestamp = Column(DateTime(timezone=True))
    devices = relationship("Devices", secondary=device_alert_association, back_populates="alerts")
    company_key = Column(Integer, ForeignKey('companies.primary_key'), nullable=False)
    company = relationship("Companies", uselist=False)



