import os
from .controllers.autotask import Autotask
from .interface import *
from .handler import *
from dotenv import dotenv_values

def add_template_dir(app):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    app.add_template_dir(path)

def post_setup_hook(app):
    db_sources = app.handler.get('db_interface', 'db_sources', setup=True)
    tenants = app.session.query( Autotask_Tenants ).all()
    for tenant in tenants:
        db_sources.add('Autotask', tenant.primary_key)

def load(app):
    app.interface.define(AutotaskInterface)
    app.interface.define(AutotaskTenantInterface)
    app.interface.define(AutotaskCompanyInterface)
    app.interface.define(AutotaskDeviceInterface)
    app.interface.define(AutotaskTicketInterface)
    app.interface.define(AutotaskContractInterface)

    app.handler.register(Autotask)
    app.handler.register(AutotaskAPI)
    app.handler.register(AutotaskTenantHandler)
    app.handler.register(AutotaskCompanyHandler)
    app.handler.register(AutotaskDeviceHandler)
    app.handler.register(AutotaskTicketHandler)
    app.handler.register(AutotaskContractHandler)
    
    app.hook.register('post_setup', post_setup_hook)
    app.hook.register('alert_update', alert_update_hook)
    app.hook.register('alert_cleared', alert_cleared_hook)
    app.hook.register('alert_device_cleared', alert_device_cleared_hook)
    app.hook.register('full_run', full_run, weight=0)
    app.hook.register('hook_check_alert', hook_check_alert)
    
    app.log.debug('Autotask plugin loaded')
    
    env = ".env/autotask"
    if os.path.isfile(env):
        config = dotenv_values(env)
        for key, value in config.items():
            host = key.split('.')[0]
            section = "autotask." + host
            if not app.config.has_section(section):
                app.config.add_section(section)
            app.config.set(section, key.split('.')[1], value)