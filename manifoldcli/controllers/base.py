
from cement import Controller, ex, Interface
from cement.utils.version import get_version_banner
from ..core.version import get_version
from ..core import *
from ..models.database import *
from cement.core.plugin import PluginInterface
import sys


VERSION_BANNER = """
Manifold Connects IT %s
%s
""" % (get_version(), get_version_banner())


class Base(Controller):
    class Meta:
        label = 'base'

        # text displayed at the top of --help output
        description = 'Manifold connects IT'

        # text displayed at the bottom of --help output
        #epilog = 'Usage: manifoldcli command1 --foo bar'

        # controller level arguments. ex: 'manifoldcli --version'
        arguments = [
            ### add a version banner
            ( [ '-v', '--version' ],
              { 'action'  : 'version',
                'version' : VERSION_BANNER } ),
        ]
        # extentions = ['manifoldcli.ext.ext_pyfiglet',
        #     'manifoldcli.ext.ext_sqlite'
        # ]

    def _default(self):
        """Default action if no sub-command is passed."""

        #self.app.render(self.app.Meta.label.capitalize())
        self.app.args.print_help()

    @ex(
        help='Will do a full run of all plugins.',
    )
    def full_run(self):
        """Run everything."""
        for res in self.app.hook.run('full_run', self.app):
            pass

    @ex(
        help='Will do a full run of all plugins.',
    )
    def cleanup_alerts(self):
        alerts_db = self.app.session.query( Alerts ).all()
        for alert_db in alerts_db:
            if alert_db:
                self.app.alert_db = alert_db
                for res in self.app.hook.run('hook_check_alert', self.app):
                    if not res:
                        associated_devices = self.app.session.query(device_alert_association).filter_by(alert_key=alert_db.primary_key).delete(synchronize_session='fetch')
                        self.app.session.delete(alert_db)
                        self.app.session.commit()
                delattr(self.app, "alert_db")
    
    
    # Hooks
    # company_update
    # site_update
    # device_update
    # alert_update
        
  
