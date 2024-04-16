
from cement import Controller, ex, Interface
from cement.utils.version import get_version_banner
from ..core.version import get_version
from ..core import *
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
        # arguments=[
        #     (['--name'], {
        #         'help': "Your name for the controller to add",
        #         'required': True,
        #         'dest': 'controller_name'
                
        #     })
        # ]
    )
    def full_run(self):
        """Run everything."""
        for res in self.app.hook.run('full_run', self.app):
            pass



    # Hooks
    # company_update
    # site_update
    # device_update
    # alert_update
        
  
