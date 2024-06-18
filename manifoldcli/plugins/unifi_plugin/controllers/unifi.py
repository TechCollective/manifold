
from cement import Controller, ex
from ..interface import *
from ..handler import *
from ....core.db_interface import *
from ....core.db_devices_handler import *
import sys
import os
from prompt_toolkit import prompt

# TODO, when checking devices, record uplinks, alet when it changes
# TODO Log switch state/port changes


class UniFi(Controller):
    class Meta:
        label = 'unifi'
        stacked_on = 'base'
        stacked_type = 'nested'
        connection = True
        interfaces = [UniFiInterface, UniFiControllerInterface, UniFiSiteInterface, UniFiAlertsInterface, DBInterface]
        handlers = [UniFiAPI, UniFiControllerHandler, UniFiSiteHandler, UniFiAlertsHandler, DBDevicesHandler]
        extentions = 'json'
        output_handler = 'json'

    def _default(self):
        self._parser.print_help()

    @ex(
        help='Setup a new UniFi controller',
        arguments=[
            (['--name'], {
                'help': "Your name for the controller to add",
                'required': True,
                'dest': 'controller_name'
                
            }),
            (['--url'],{
                'help': 'URL for the controller',
                'required': True,
                'dest': 'controller_url'
            }),
            (['--port'],{
                'help': 'Port for the controller',
                'required': True,
                'dest': 'controller_port'
            }),
        ]
    )
    def add_controller(self):
        """Setup Unifi controller."""
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.controller.add(name=self.app.pargs.controller_name, url=self.app.pargs.controller_url, port=self.app.pargs.controller_port)
        # FIXME output better!
        print("Create an API user in your controller, then add the following to your unifi enviroment file, replace wiht the correct values.\n" + self.app.pargs.controller_name + ".user=USERNAME\n" + self.app.pargs.controller_name + ".password=PASSWORD")

    @ex(
        help='List all UniFi Controllers'
    )
    def list_controllers(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        
        controllers = unifi.controller.list()
        # FIXME fix output
        print("Controllers:")
        for controller in controllers:
            print(" - " + controller.name + " " + controller.host + ":" + str(controller.port))
            #print(self.app.template.render('Foo => {{ foo }}', data))
            #self.app.render(data)

    # @ex(
    #     help='Setup Authentication',
    #     arguments=[
    #         (['--controller-name'], {
    #             'help': "Name of the controller you want to setup Autjentication for.",
    #             'required': True,
    #             'dest': 'controller_name'
    #         }),
    #         (['--user'], {
    #             'help': "Name of API user.",
    #             'required': True,
    #             'dest': 'api_name'
    #         }),
    #     ]
    # )
    # def setup_auth(self):
    #     unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
    #     password = prompt('Enter password for ' + self.app.pargs.controller_name + ': ', is_password=True)
    #     unifi.controller.auth(controller=self.app.pargs.controller_name, user=self.app.pargs.api_name, password=password)

    @ex(
        help='Sync all sites',
    )
    def sync_all_sites(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        controllers = unifi.controller.list()
        for controller in controllers:
            unifi.site.sync_all(controller)

    @ex(
        help='Sync device for a site',
        arguments=[
            (['--site-id'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'site_id'
            }),
            (['--controller-name'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'controller_name'
            })]
    )
    def sync_site_devices(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.device.sync_site(self.app.pargs.controller_name, self.app.pargs.site_id)
    
    @ex(
        help='Sync all devices for all sites on a controller',
        arguments=[
            (['--controller-name'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'controller_name'
                
            })]
    )
    def sync_controller_devices(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.device.sync_controller(self.app.pargs.controller_name)
    
    @ex(
        help='Sync all devices for all sites on all controllers',
    )
    def sync_all_devices(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.device.sync_all()

    @ex(
        help='Sync alerts for a site',
        arguments=[
            (['--site-id'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'site_id'
            }),
            (['--controller-name'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'controller_name'
            })]
    )
    def sync_site_alerts(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.alert.sync_site_by_id(self.app.pargs.controller_name, self.app.pargs.site_id)
    
    @ex(
        help='Sync alerts for a controller',
        arguments=[
            (['--controller-name'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'controller_name'
                
            })]
    )
    def sync_controller_alerts(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.alert.sync_controller(self.app.pargs.controller_name)

    @ex(
        help='Sync all alerts for all sites on all controllers',
    )
    def sync_all_alerts(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.alert.sync_all()

    # TODO check on unifi tickets. Will grab all tickets and check if they are still relavant. 
    # If they are, update them with latest information. 
    # If the issue is resolved, add a note. 
    #   If the issue is resolved and there is no time, add a note, close the ticket, alert the primary resource


    # Stright API calls for dev help and troubleshootsing
    @ex(
        help='Get health info for a site',
        arguments=[
            (['--site-id'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'site_id'
            }),
            (['--controller-name'], {
                'help': "Controller you will to sync",
                'required': True,
                'dest': 'controller_name'
            })]
    )
    def site_health(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.site_health(self.app.pargs.controller_name, self.app.pargs.site_id)

    @ex(
        help='Get device json',
        arguments=[
            (['--mac'], {
                'help': "mac address of device",
                'required': True,
                'dest': 'mac'
            }),
            (['--site-id'], {
                'help': "Site ID you will to sync",
                'required': True,
                'dest': 'site_id'
            }),
            (['--controller-name'], {
                'help': "Controler name you will to sync",
                'required': True,
                'dest': 'controller_name'
            })]
    )
    def pull_device(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.pull_device_by_mac(self.app.pargs.mac, self.app.pargs.controller_name, self.app.pargs.site_id)

    @ex(
        help='Clear old alerts',
    )
    def clear_old_alerts(self):
        unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
        unifi.alert.verify_old_alerts()