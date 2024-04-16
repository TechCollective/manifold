from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase

class UniFi_Sites(DBBase):
    __tablename__ = 'unifi_sites'
    primary_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    id = Column(String, nullable=False)
    desc = Column(String, nullable=False)
    controller_key: Mapped[int] = mapped_column(ForeignKey("unifi_controllers.primary_key"))
    controller: Mapped["UniFi_Controllers"] = relationship(back_populates="sites")
    parent_id: Mapped[int] = mapped_column(ForeignKey('companies.primary_key'))
    parent = relationship("Companies", foreign_keys=[parent_id])
    __table_args__ = (UniqueConstraint('name', 'controller_key', name='_unique_name_controller_key'),)