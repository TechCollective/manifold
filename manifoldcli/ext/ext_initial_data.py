from ..models.database import *
from ..core.db_interface import *
from ..core.db_alerts_handler import *
from cement import minimal_logger

def add_initial_data(app):
    db = app.handler.get('db_interface', 'db_alert_type', setup=True)
    db.add("Site Down")
    db.add("Lost Contact")
    db.add("Secondary WAN Inactive")
    db.add("Stp Port Blocking")
    db.add("WAN Transition")
    db.add("Rogue AP")
    db.add("LTE Hard Limit Used")
    db.add("LTE Threshold")
    db.add("Radar Detected")
    db.add("IPS")
    db.add("No Contract")
