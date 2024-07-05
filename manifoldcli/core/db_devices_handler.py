from cement import Handler
from .db_interface import *
from ..models.database.devices import *
from ..models.database.sources import *
from ..models.devices import *
import sys

class DBDevicesHandler(DBInterface, Handler):
    class Meta:
        label = 'db_devices'

    def add(self, device_obj, source):
        device_db = Devices(name=device_obj.name)
        if device_obj.serial:
            device_db.serial = device_obj.serial
        if device_obj.manufacturer:
            device_db.manufacturer = device_obj.manufacturer
        if device_obj.model:
            device_db.model = device_obj.model
        if device_obj.install_date:
            device_db.install_date = device_obj.install_date
        if device_obj.company:
            device_db.company_key = device_obj.company
        else:
            self.app.log.error("device is not assoicated with a company!")
            self.app.log.error(device_obj)
            sys.exit()
        if device_obj.source:
            device_db.source = device_obj.source
        else:
            self.app.log.error("device is not assoicated with a source!")
            self.app.log.error(device_obj)
            sys.exit()

        self.app.session.add(device_db)
        self.app.session.commit()
        self.run_hook(device_db, source)
        return device_db

    def delete(self, device_obj, source):
        # TODO check with other sources to see if it's still being used
        pass

    def update(self, device_obj, device_db, source):
        if device_db is None:
            self.app.log.error("device_db is None!")
            sys.exit()
        changed = False
        if device_db.name != device_obj.name:
            device_db.name = device_obj.name
            changed = True
        # TODO Record IP if static, if not, put DHCP

        if device_db.manufacturer != device_obj.manufacturer:
            device_db.manufacturer = device_obj.manufacturer
            changed = True
        if device_db.model != device_obj.model:
            device_db.model = device_obj.model
            changed = True

        def is_newer_than(a, b):
            if a is None:
                return False 
            if b is None:
                return True
            return a < b   

        #if device_db.install_date is None or device_obj.install_date < device_db.install_date:
        if device_db.install_date is None or is_newer_than(device_obj.install_date, device_db.install_date):

            device_db.install_date = device_obj.install_date
            changed = True
        if device_db.company_key != device_obj.company:
            device_db.company_key = device_obj.company
            changed = True
        source_db = self.app.session.query(Sources).filter_by(primary_key=device_obj.source).first()

        if device_db.source != device_obj.source:
            # TODO This should not be hard coded. Need a way to say what source is primay
            if source_db.plugin_name == "UniFi":
                device_db.source = device_obj.source
                changed = True

        if changed:
            self.app.log.debug("[Core] Updating Device: " + device_obj.name + " Source: " + source )
            self.app.session.commit()
            self.run_hook(device_db, source)

    def create_object(self, device_db):
        if device_db is None:
            self.app.log.error("device_db is None!")
            sys.exit()
        device_obj = DeviceObject(
            name = device_db.name,
            manufacturer = device_db.manufacturer,
            model = device_db.model,
            install_date = device_db.install_date,
            company = device_db.company_key,
            serial = device_db.serial,
            source = device_db.source
        )

        return device_obj

    # TODO put this in a hook when the app closes
    #def close_session(self):
    #   self.app.session.close()

    def run_hook(self, obj, source):
        for res in self.app.hook.run('device_update'):
            res(obj, source)