from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.orm import declarative_base

DBBase = declarative_base()

device_alert_association = Table('device_alert_association', DBBase.metadata,
    Column('device_key', Integer, ForeignKey('devices.primary_key')),
    Column('alert_key', Integer, ForeignKey('alerts.primary_key')),
    Column('cleared', Boolean, default=False))