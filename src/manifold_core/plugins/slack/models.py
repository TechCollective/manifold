from sqlalchemy import Integer, Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from manifold_core.models.base import Base

class SlackIntegrationDB(Base):
    __tablename__ = "slack_integrations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    workspace = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())