import os
import sys
from .controllers.unifi import UniFi
from .models.database import *
from ...models.database import *
from .interface import *
from .handler import *
from dotenv import dotenv_values

def add_template_dir(app):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    app.add_template_dir(path)

def unifi_post_setup_hook(app):
    db_sources = app.handler.get('db_interface', 'db_sources', setup=True)
    tenants = app.session.query( UniFi_Controllers ).all()
    for tenant in tenants:
        db_sources.add('UniFi', tenant.primary_key)

def load(app):
    app.interface.define(UniFiControllerInterface)
    app.interface.define(UniFiSiteInterface)
    app.interface.define(UniFiDeviceInterface)
    app.interface.define(UniFiAlertsInterface)
    app.interface.define(UniFiInterface)
    app.handler.register(UniFi)
    app.handler.register(UniFiControllerHandler)
    app.handler.register(UniFiSiteHandler)
    app.handler.register(UniFiDeviceHandler)
    app.handler.register(UniFiAlertsHandler)
    app.handler.register(UniFiHandler)
    app.handler.register(UniFiAPI)
    app.log.debug('UniFi plugin loaded')
    #app.hook.register('post_setup', add_template_dir)
    app.hook.register('post_setup', unifi_post_setup_hook)
    app.hook.register('full_run', full_run, 100)



    unifi_env = ".env/unifi"
    if os.path.isfile(unifi_env):
        unifi_config = dotenv_values(unifi_env)
        for key, value in unifi_config.items():
            host = key.split('.')[0]
            section = "unifi." + host
            if not app.config.has_section(section):
                app.config.add_section(section)
            app.config.set(section, key.split('.')[1], value)


