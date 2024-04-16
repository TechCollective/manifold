from cement import Handler
from .db_interface import *
from ..models.database.sources import *
import sys

class DBSourcesHandler(DBInterface, Handler):
    class Meta:
        label = 'db_sources'

    def add(self, plugin_name, tenant_key):
        exist = self.app.session.query( Sources ).filter_by(plugin_name=plugin_name, tenant_key=tenant_key).first()
        
        if not exist:
            db = Sources(
                plugin_name=plugin_name,
                tenant_key=tenant_key
                )
            self.app.session.add(db)
            self.app.session.commit()
            return db

    def delete(self, device_obj, source):
        # TODO check with other sources to see if it's still being used
        pass

    def update(self, device_obj, device_db, source):
        pass

    # TODO put this in a hook when the app closes
    #def close_session(self):
    #   self.app.session.close()

    def run_hook(self, obj, source):
        for res in self.app.hook.run('source_update'):
            res(obj, source)