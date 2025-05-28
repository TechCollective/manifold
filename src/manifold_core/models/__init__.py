from .base import Base, engine, SessionLocal

# Import models to ensure they get registered
from manifold_core.plugins.unifi.models import UnifiServer, UnifiSite, UnifiDevice
from manifold_core.plugins.slack.models import SlackIntegrationDB
from manifold_core.plugins.autotask.models import AutotaskIntegrationDB