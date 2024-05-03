from cement import Handler
from .db_interface import *
from ..models.database.alerts import *
import sys
import datetime
from dateutil import parser
from sqlalchemy.exc import SQLAlchemyError

class DBAlertsTypeHandler(DBInterface, Handler):
    class Meta:
        label = 'db_alert_type'

    def add(self, name):
        exist = self.app.session.query( AlertTypes ).filter_by(name=name).first()
        
        if not exist:
            db = AlertTypes(
                name=name
                )
            self.app.session.add(db)
            self.app.session.commit()
            return db

    def delete(self, obj):
        pass

    def update(self, obj, db, source):
        pass

    # TODO put this in a hook when the app closes
    #def close_session(self):
    #   self.app.session.close()
    def run_hook(self, obj, source):
        for res in self.app.hook.run('alert_update'):
            res(obj, source)

class DBAlertsHandler(DBInterface, Handler):
    class Meta:
        label = 'db_alerts'

    def add(self, alert_obj, source):
        # TODO Look up the device in Autotask and and see if this alert is in the UDF: "UniFi Alerts Ignore List"
        self.app.log.debug("[Core] Alert: " + str(alert_obj.alert_type.name))
        # TODO: Check alerts being added. More alerts are being added that are connecting to tickets. Need to check what is happening.
        exist_alert = self.app.session.query( Alerts ).filter_by( alert_type_key=alert_obj.alert_type.primary_key, company_key=alert_obj.company_db.primary_key).first()
        changed_alert = False
        new_alert = False
        if exist_alert:
            self.app.log.debug("[Core] Alert exist")
            if exist_alert.devices and alert_obj.devices:
                if exist_alert.devices[0] == alert_obj.devices[0]:
                    if exist_alert.last_timestamp == alert_obj.last_timestamp:
                        self.app.log.debug("[Core] Same alert")
                    else:
                        if alert_obj.last_timestamp is not None:
                            self.app.log.debug("[Core] Different last_timestampt. updating alert")
                            db = exist_alert
                            if db.last_timestamp:
                                last_timestamp_og = parser.parse(db.last_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                                last_timestamp_new = parser.parse(alert_obj.last_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                                if last_timestamp_og < last_timestamp_new:
                                    db.last_timestamp = alert_obj.last_timestamp
                                else:
                                    self.app.log.debug("[Core] Timestamp suggest it's an earilyer alert. Ignoring")
                            else: 
                                db.last_timestamp = alert_obj.last_timestamp
                            self.app.session.commit()
                            changed_alert = True

                else:
                    new_alert = True
        else:
            new_alert = True

        if new_alert:
            self.app.log.debug("[Core] Adding Alert Object to the DB")

            try:
                db = Alerts(
                    alert_type = alert_obj.alert_type,
                    source = alert_obj.source_db,
                    start_timestamp = alert_obj.last_timestamp,
                    last_timestamp = alert_obj.last_timestamp, # since it's the first one
                    devices = alert_obj.devices,
                    company = alert_obj.company_db,
                    title_append = alert_obj.title_append,
                    useful_information = alert_obj.useful_information
                )
                self.app.session.add(db)
                self.app.session.commit()
            except (AttributeError, TypeError) as e:
                self.app.log.error(f"[Core] An SQLAlchemy error occurred: {e}")
                self.app.log.error("[Core] Object: " + alert_obj.to_str())
                sys.exit()

        if new_alert or changed_alert:
            self.app.last_alert = db
            self.run_hook(db, source)
            return db

    def delete(self, obj):
        pass

    def update(self, obj, db, source):
        pass

    # TODO put this in a hook when the app closes
    #def close_session(self):
    #   self.app.session.close()
    def run_hook(self, obj, source):
        for res in self.app.hook.run('alert_update', self.app):
            pass
