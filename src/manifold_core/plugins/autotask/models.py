from sqlalchemy import Integer, Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from manifold_core.models.base import Base

class AutotaskIntegrationDB(Base):
    __tablename__ = "autotask_integrations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    api_url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
