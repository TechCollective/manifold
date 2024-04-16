
from cement import App, TestApp, init_defaults
from cement.core.exc import CaughtSignal
from .core.exc import ManifoldError
from .core.db_interface import DBInterface
from .core.db_devices_handler import DBDevicesHandler
from .core.db_companies_handler import DBCompaniesHandler
from .core.db_sources_handler import DBSourcesHandler
from .core.db_alerts_handler import DBAlertsHandler, DBAlertsTypeHandler
from .controllers.base import Base
from .ext.ext_sqlite import db_extension
from .ext.ext_initial_data import add_initial_data
from cement.core.plugin import PluginInterface


# configuration defaults
# CONFIG = init_defaults('manifoldcli','log.colorlog','plugin.unifi_plugin', 'unifi')
CONFIG = init_defaults('manifoldcli','log.colorlog','unifi','autotask')
# TODO Change this to a better location
CONFIG['manifoldcli']['db_file'] = './db.sqlite3'
CONFIG['manifoldcli']['foo'] = 'bar'
#temp
CONFIG['log.colorlog']['file'] = './manifold.log'
#CONFIG['plugin.unifi_plugin']['enabled'] = 'true'
# TODO need to figure out how to move this to the unifi plugin
CONFIG['unifi']['sites2companies'] = 'autotask-udf'
# TODO need to figure out how to move this to the autotask plugin
CONFIG['unifi']['default_unifi_product'] = 'Unifi Generic Product'

class Manifold(App):
    """Manifold CLI primary application."""

    class Meta:
        label = 'manifoldcli'

        # configuration defaults
        config_defaults = CONFIG

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'json',
            'yaml',
            'colorlog',
            'jinja2',
            'daemon',
            'manifoldcli.ext.ext_pyfiglet',
            'manifoldcli.ext.ext_sqlite',
            'manifoldcli.ext.ext_initial_data'
        ]

        # configuration handler
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'
        template_handler = 'jinja2'

        interfaces = [
            DBInterface,
        ]
        # register handlers
        handlers = [
            Base,
            DBDevicesHandler,
            DBCompaniesHandler,
            DBSourcesHandler,
            DBAlertsHandler, 
            DBAlertsTypeHandler
        ]
        define_hooks = [
            'full_run',
            'device_update',
            'company_update',
            'alert_update'
        ]
        hooks = [
            ('post_setup', db_extension),
            ('post_setup', add_initial_data),
        ]
        plugin_dirs = ['./plugins']
        # TODO Move this to conf file
        plugins = [
            'unifi_plugin',
            'autotask_plugin'
        ]
    

class ManifoldTest(TestApp,Manifold):
    """A sub-class of Manifold that is better suited for testing."""

    class Meta:
        label = 'manifoldcli'


def main():
    with Manifold() as app:
        try:
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except ManifoldError as e:
            print('ManifoldError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
