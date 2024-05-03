from cement import Handler
from .interface import *
from .models.database import *
from ...models.database import *
from ...models.devices import *
from ...models.alerts import *
from pyunifi import controller
import sys
import os
import json
import pytz
from datetime import datetime, timedelta
import dateutil.parser
import multiprocessing
import time
import re

class UniFiControllerHandler(UniFiControllerInterface, Handler):
    class Meta:
        label = 'unifi_controller'

    def list(self):
        return self.app.session.query( UniFi_Controllers).all()

    def add(self, name, url, port):
        # Check if entry exsits first
        self.app.log.debug("[UniFi plugin] Adding controller to database")
        controller = UniFi_Controllers(
            name = name,
            host = url,
            port = port,
            is_active = True
        )
        # TODO detect UNIQUE constraint and explain it to the user
        self.app.session.add(controller)
        self.app.session.commit()

    def delete(self):
        pass

    def disable(self):
        pass

    def enable(self):
        pass

    def auth(self, controller, user, password):
        pass

    def controller_api_object(self, controller_db_object, site_id=None):
        name = controller_db_object.name
        host = controller_db_object.host
        port = controller_db_object.port
        username = None
        password = None

        section = "unifi." + name
        if self.app.config.has_section(section):
            if self.app.config.get(section,'user') is not None:
                username = self.app.config.get(section,'user')
            else:
                self.app.log.error('[UniFi plugin] Controller variables "username" is missing! Please define controller varibles first.')
                sys.exit()

            if self.app.config.get(section,'password') is not None:
                password = self.app.config.get(section,'password')
            else:
                self.app.log.error('[UniFi plugin] Controller variables "password" is missing! Please define controller varibles first.')
                sys.exit()
            if site_id:
                return controller.Controller(host=host, username=username, password=password, port=port, version="v5", site_id=site_id)
            else:
                return controller.Controller(host=host, username=username, password=password, port=port, version="v5")
        else:
            self.app.log.error('[UniFi plugin] Controller variables are missing! Please define controller varibles first.')
            sys.exit()

class UniFiSiteHandler(UniFiSiteInterface, Handler):
    class Meta:
        label = 'unifi_site_handler'
    
    def sync_all(self, controller):
        """
        2 steps
            * Loop through all sites on a Unifi controller, creates a site object, then sends them to get.
            * Loops through all sites for this controller in the database, creates a site object, then sends them to post.
        
        Args:
            controller (controller_obj): all information for the controller.
        """
        session = self.app.session

        # Update database
        c = UniFiControllerHandler.controller_api_object(self, controller)
        sites = c.get_sites()
        for site in sites:
            self.update_db(site, controller)
        
        # Remove sites from database that are no longer in the controller
        sites_db = session.query(UniFi_Sites).filter_by(controller_key=controller.primary_key).all()
        for site_db in sites_db:
            on_controller = False
            
            for site in sites:
                if site_db.name == site['name']:
                    on_controller = True
            if on_controller == False:
                self.app.log.debug("[UniFi plugin] Deleting Site from DB: site not found in controller. [Site: " + site_db.desc + " Site ID: " + site_db.name + "]")
                session.delete(session.merge(site_db))
                session.commit()
        session.close()

    def update_db(self, site, controller):
        """
        Verify a site is in the DB and is up to date.

        Args:
            site (site_obj): all information for the site.
            controller (controller_obj): all information for the controller.
        """
        
        existing_entry = self.app.session.query(UniFi_Sites).filter_by(name=site['name'], controller_key=controller.primary_key).first()
        
        if existing_entry:
            self.app.log.debug("[UniFi plugin] Syncing Site: " + site['desc'] )
            changed = False
            if existing_entry.id != site['_id']:
                existing_entry.id = site['_id']
                changed = True
            if existing_entry.desc != site['desc']:
                existing_entry.desc = site['desc']
                changed = True
            if changed:
                self.app.log.debug("[UniFi plugin] Updating Site in DB:  [Site: " + site['desc'] + " Site ID: " + site['name'] + "]")
                self.app.session.commit()
                # FIXME Might trigger a hook
            if existing_entry.parent_id:
                unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
                unifi.alert.verify_contract(existing_entry)
        else:
            self.app.log.debug("[UniFi plugin] New Site: " + site['desc'] + " Site ID: " + site['name'] )
            site_db = UniFi_Sites(
                name = site['name'],
                id = site['_id'],
                desc = site['desc'],
                controller_key = controller.primary_key
            )
            self.app.log.debug("[UniFi plugin] Adding Site to DB:  [Site: " + site['desc'] + " Site ID: " + site['name'] + "]")
            self.app.session.add(site_db)
            self.app.session.commit()
            # FIXME Might trigger a hook
        self.app.session.close()
    
    def post(self, site_db, controller):
        """
        Verify site is up to date on the controller side.

        Args:
            site (site_obj): all information for the site.
            controller (controller_obj): all information for the controller.
        """
        pass

    def hooks(self, site, controller, source):
        pass

    def get_host_and_port_from_autotask_udf(self, site_id):
        controller_db = None
        site_id_componets = site_id.split('/')
        if ":" in site_id_componets[2]:
            unifi_host_componets = site_id_componets[2].split(':')
            controller_db = self.app.session.query(UniFi_Controllers).filter_by(host=unifi_host_componets[0], port=unifi_host_componets[1]).first()
        else:
            controller_db = self.app.session.query(UniFi_Controllers).filter_by(host=site_id_componets[2]).first()
        if site_id_componets[4] == 'site':
            return self.app.session.query(UniFi_Sites).filter_by(name=site_id_componets[5], controller_key=controller_db.primary_key).first()
        else:
            return self.app.session.query(UniFi_Sites).filter_by(name=site_id_componets[4], controller_key=controller_db.primary_key).first()
         
    def link_sites_to_company_from_autotask(self, site_ids, company_key):
        # TODO since this pulls input from Autotask and we cannot know that it is without error, we need to have a way to dealing with errors here
        # TODO manually add a subname to each entry in autotask for the Site ID. Detect that here. 
        # TODO If there is only 1 site ID, sync UniFi's "site Desc" to the company name
        # TODO If there are more than 1, change the "Site Desc" to "Company Name - Subname"
        # If they don't have an the "Base" SLA service, prepend "zz_"the "Site Desc"

        if site_ids.find('\n') != -1:
            for site_id in site_ids.split('\n'):
                # Detects if we are just dealing with Site IDs or the whole url
                if len(site_id) == 8:
                    # Only the 8 digit site id. We are assuming it's the first Controller
                    site_db = self.app.session.query(UniFi_Sites).filter_by(name=site_id, controller_key='1').first()
                    if site_db:
                        site_db.parent_id = company_key
                        self.app.session.commit()
                    else:
                        # TODO check last sync and sync unifi sites if it's after sync time.
                        self.app.log.warning("[UniFi plugin] Autotask has a listed Site ID: " + site_id + " But there is not a site in the database.")
                elif len(site_id) == 0:
                    pass
                else:
                    site_db = self.get_host_and_port_from_autotask_udf(site_id)
                    site_db.parent_id = company_key
                    self.app.session.commit()
        else:
            site_id = site_ids
            if len(site_id) == 8:
                # Only the 8 digit site id. We are assuming it's the first Controller
                site_db = self.app.session.query(UniFi_Sites).filter_by(name=site_id, controller_key='1').first()
                if site_db:
                    site_db.parent_id = company_key
                    self.app.session.commit()
                else:
                    # TODO check last sync and sync unifi sites if it's after sync time.
                    self.app.log.warning("[UniFi plugin] Autotask has a listed Site ID: " + site_id + " But there is not a site in the database.")
            else:
                site_db = self.get_host_and_port_from_autotask_udf(site_ids)
                site_db.parent_id = company_key
                self.app.session.commit()

class UniFiDeviceHandler(UniFiDeviceInterface, Handler):
    class Meta:
        label = 'unifi_device_handler'

    def sync_all(self):
        controllers = self.app.session.query(UniFi_Controllers).all()

        for controller in controllers:
            self.app.log.info("[UniFi plugin] Syncing for Controller: " + controller.name)
            self.sync_controller(controller.name)
   
    def sync_controller(self, controller_name):
        controller = self.app.session.query(UniFi_Controllers).filter_by(name=controller_name).first()
        
        c = UniFiControllerHandler.controller_api_object(self, controller)

        sites = c.get_sites()
        for site in sites:
            self.app.log.info("[UniFi plugin] Syncing Site: " + site['desc'] + "  ID: " + site['name'])
            self.sync_site(controller.name, site['name'])

    def sync_site(self, controller_name, site_id):
        controller = self.app.session.query(UniFi_Controllers).filter_by(name=controller_name).first()
        unifi_site_db = self.app.session.query( UniFi_Sites ).filter_by( name=site_id, controller_key=controller.primary_key  ).first()
        c = UniFiControllerHandler.controller_api_object(self, controller, site_id)

        if unifi_site_db.parent_id:
            devices = c.get_aps()
            for device in devices:
                if device.get('serial') is not None and device.get('adopted'):
                    self.update_db(device, site_id, controller)

                    unifi_api = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
                    device_db = self.app.session.query( Devices ).filter_by( serial=device['serial'] ).first()
                    company_db = self.app.session.query( Companies ).filter_by( primary_key=unifi_site_db.parent_id  ).first()

                    alert_obj = unifi_api.alert.UniFiAlertObject(
                        alert_unifi = None,
                        controller = controller, 
                        site_name = site_id,
                        connection = c,
                        device_unifi = device,
                        source_db = self.app.session.query( Sources ).filter_by(plugin_name="UniFi", tenant_key=controller.primary_key).first(), 
                        devices=[device_db], 
                        company_db=company_db
                    )
                    unifi_api.alert.device_alerts(alert_obj)

                elif device.get('serial') is None:
                    # TODO Figure out what to do with these
                    # Not sure what to do with these. I'm guessing that we should generate a ticket to have them removed.
                    # Might be able to use disconnection_reason': "MISSED_INFORM, last_seen '1692203911', considered_lost '1692203921', state: 5", 
                    # Also weird keys. 'anomalies': -1 and 'satisfaction': -1, 
                    # For now skipping
                    self.app.log.warning("[UniFi plugin] Device has no serial number. [Device: " + device['name'] + "]")
                    self.app.log.warning("[UniFi plugin] Device Json: " + str(device))
                elif device.get('adopted') == False:
                    # Not sure I want to do anything with devices not adapted. Just tagging this in case I do
                    pass
        else:
            self.app.log.warning("[UniFi plugin] Site: " + unifi_site_db.desc + "is not assoicated with a company. Skipping.")

    def _create_device_object(self,device):
        if device['name'] == None:
            print("no name")
            print(device)
            sys.exit()
        # TODO copy mac logic for ip_addresses
        mac_obj = MacAddressObject(
            mac_address=device['mac']
        )
        # TODO for loop through device['ethernet_table'] to get all macs
        mac_list_obj = MacAddressListObject(
            results=[mac_obj]
        )
        device_obj = DeviceObject(
            name=device['name'],
            manufacturer="Ubiquiti",
            model=device['model'],
            serial=device['serial'],
            mac_address=mac_list_obj
        )
        if device.get('provisioned_at') is not None:
            device_obj.install_date=datetime.fromtimestamp(device['provisioned_at'])
        return device_obj

    def update_db(self, device, site_id, controller):
        db_devices = self.app.handler.get('db_interface', 'db_devices', setup=True)
        device_obj = self._create_device_object(device)
        site_db = self.app.session.query( UniFi_Sites ).filter_by(name=site_id, controller=controller).first()

        if site_db == None:
            self.app.log.error("[UniFi plugin] TODO: Site is not in Database. Need to create a function that will add it!")
        elif site_db.parent_id == None:
            self.app.log.error("[UniFi plugin] Site " + site_id + "is not assoicated with a Company is not in Database. Need to create a function that will add it!")
        else:
            device_obj.company = site_db.parent_id
            # if site_db.parent_id:
            #     device_obj.company = site_db.parent_id

            existing_entry = self.app.session.query( UniFi_Devices ).filter_by(unifi_device_id=device['_id']).first()

            if existing_entry:
                db_devices.update(device_obj, existing_entry.parent, "unifi")
            else:
                # TODO Maybe we should verify it's a unifi device
                existing_device = self.app.session.query( Devices ).filter_by( serial=device['serial'], company_key=site_db.parent_id ).first()
                device_db = None
                
                if existing_device:
                    device_db = existing_device
                else:
                    device_db = db_devices.add(device_obj, "unifi")

                site_db = self.app.session.query( UniFi_Sites ).filter_by( name=site_id, controller_key=controller.primary_key ).first()

                unifi_device_db = UniFi_Devices(
                    unifi_device_id = device['_id'],
                    parent = device_db,
                    unifi_sites_key = site_db.primary_key,
                    device_key = device_db.primary_key
                )
                self.app.log.debug("[UniFi plugin] Linking device to unifi_device. [Device: " + device['name'] + " Site ID: " + site_id + "]")
                self.app.session.add(unifi_device_db)
                self.app.session.commit()

    def post(self, device, site, controller):
        pass

class UniFiAlertsHandler(UniFiAlertsInterface, Handler):
    class Meta:
        label = 'unifi_alerts_handler'

    # TODO create a function that looks up /api/s/l8s06sos/stat/health, which will tell us if both ISP are up. 

    class UniFiAlertObject(AlertObject):
        def __init__(self,
            alert_unifi = None,
            controller = None, # Controller that created the alert
            site_name = None, # Site name
            connection = None, # api connection, for easy reconnecting to get information
            device_unifi = None, # API return json of the device from the controller
            alert_type=None, source_db=None, start_timestamp=None, last_timestamp=None, devices=None, company_db=None, title_append=None, useful_information=None #From Main Class
        ):
            super().__init__(alert_type=alert_type, 
                             source_db=source_db, 
                             start_timestamp=start_timestamp, 
                             last_timestamp=last_timestamp, 
                             devices=devices, 
                             company_db=company_db, 
                             title_append=title_append,
                             useful_information=useful_information)
            self._alert_unifi = None

            if alert_unifi is not None:
                self.alert_unifi = alert_unifi
            if controller is not None:
                self.controller = controller
            if site_name is not None:
                self.site_name = site_name
            if connection is not None:
                self.connection = connection
            if device_unifi is not None:
                self.device_unifi = device_unifi

        @property
        def alert_unifi(self):
            return self._alert_unifi
        
        @alert_unifi.setter
        def alert_unifi(self, alert_unifi):
            self._alert_unifi = alert_unifi

    def _archive_alert(self, c, alert_id):
        params = {'_id': alert_id}
        return c._run_command('archive-alarm', params, mgr="evtmgr")

    def device_alert_state(self, alert_obj):
        # States I have some information about
        # State 0: Disconnected
        # State 1: Connected
        # State 2: Not adopted (I think) - ChatGPT: Pending
        # State 3: ChatGPT: Adopting
        # State 4: ChatGPT: Upgrading
        # State 5: ChatGPT: Failed
        # State 6: ChatGPT: Inactive
        # State 11: Isolated (I think)

        if alert_obj.device_unifi['state'] == 0:
            alert_obj.alert_type =  self.app.session.query( AlertTypes ).filter_by(name="Lost Contact").first()
            unifi_site_db = self.app.session.query( UniFi_Sites ).filter_by( name=alert_obj.site_name, controller_key=alert_obj.controller.primary_key  ).first()
            alert_obj.title_append = " (" + str(unifi_site_db.desc) + ")"
            alert_obj.useful_information = "UniFi Controller: https://" +  alert_obj.controller.host + ":" + str(alert_obj.controller.port) + "/manage/" + str(alert_obj.site_name) +"/"

            self.alert_lost_contact(alert_obj)

        elif alert_obj.device_unifi['state'] > 1:
            self.app.log.warning("[UniFi plugin] Device: " + alert_obj.device_unifi['name'] + " is state " + str(alert_obj.device_unifi['state']))

    def device_alerts(self, alert_obj):
        if alert_obj.device_unifi.get('state') is not None:
            if alert_obj.device_unifi['state'] != 1:
                self.device_alert_state(alert_obj)

        if alert_obj.device_unifi.get('unsupported') is not None:
            if alert_obj.device_unifi['unsupported']:
                self.app.log.warning("[UniFi plugin] Device: " + alert_obj.device_unifi['name'] + " is unsupported. Reason: " + str(alert_obj.device_unifi['unsupported_reason']))
        # if device_unifi.get('internet') is not None:
        #     self.app.log.warning("[UniFi plugin] No internet [Device: " + device_unifi['name'] + "]")
        # Verify device has the correct inform url
        if alert_obj.device_unifi.get('inform_url') is not None:
            # TODO, need to create the inform url from the controller.
            pass
        if alert_obj.device_unifi.get('sys_error_caps') is not None:
            if alert_obj.device_unifi['sys_error_caps'] > 0:
                self.app.log.error("[UniFi plugin] Device error: sys_error_caps - " + alert_obj.device_unifi['sys_error_caps'])
                self.app.log.error("[UniFi plugin] Device: " + str(alert_obj.device_unifi))
                sys.exit()
        if alert_obj.device_unifi.get('model_incompatible') is not None:
            if alert_obj.device_unifi['model_incompatible']:
                print('model_incompatible')
                print(alert_obj.device_unifi['model_incompatible'])
                self.app.log.error("[UniFi plugin] Device: " + str(alert_obj.device_unifi))
                sys.exit()
        if alert_obj.device_unifi.get('model_in_eol') is not None:
            if alert_obj.device_unifi['model_in_eol']:
                self.app.log.warning("[UniFi plugin] Device: " + alert_obj.device_unifi['name'] + " is EOL")
        if alert_obj.device_unifi.get('has_temperature') is not None:
            if alert_obj.device_unifi['has_temperature']:
                if alert_obj.device_unifi.get('overheating'):
                    self.app.log.warning("[UniFi plugin] Device: " + alert_obj.device_unifi['name'] + " is overheating. General_temperature: " + str(alert_obj.device_unifi['general_temperature']))
                    self.app.log.error("[UniFi plugin] Device: " + str(alert_obj.device_unifi))
                    sys.exit()
        if alert_obj.device_unifi.get('model_in_lts') is not None:
            if alert_obj.device_unifi['model_in_lts']:
                print('model_in_lts')
                print(alert_obj.device_unifi['model_in_lts'])
                self.app.log.error("[UniFi plugin] Device: " + str(alert_obj.device_unifi))
                sys.exit()
        if alert_obj.device_unifi.get('upgrade_state') is not None:
            if alert_obj.device_unifi['upgrade_state'] != 0:
                print('upgrade_state')
                print(alert_obj.device_unifi['upgrade_state'])
                self.app.log.error("[UniFi plugin] Device: " + str(alert_obj.device_unifi))
                sys.exit()
        if alert_obj.device_unifi.get('anomalies') is not None:
            if alert_obj.device_unifi['anomalies'] != -1:
                self.app.log.error("[UniFi plugin] Device 'anomalies'")
                self.app.log.error("[UniFi plugin] Device: " + str(alert_obj.device_unifi))
                self.app.log.error("[UniFi plugin] " + str(alert_obj.device_unifi['anomalies']))
                sys.exit()

    def check_get_device_stat(self, c, mac):
        url = c._api_url() + "stat/device/" + mac
        response = c.session.get(url, params=None, headers=c.headers)
        if response.headers.get("X-CSRF-Token"):
            c.headers = {"X-CSRF-Token": response.headers["X-CSRF-Token"]}

        obj = json.loads(response.text)
        if "meta" in obj:
            if obj["meta"]["rc"] != "ok":
                if obj['meta']['msg'] != "api.err.UnknownDevice":
    #				raise APIError(obj["meta"]["msg"])
                    #print("Unknown Device: " + obj['meta']['msg'])
                    self.app.log.error("Unknown Device: " + obj['meta']['msg'])
        if "data" in obj:
            result = obj["data"]
        else:
            result = obj
        return result

    def secondary_wan_inactive(self, alert, alert_obj):
        self.app.log.warning("[UniFi plugin] Seconadary WAN is down. Creating alert.")
        c = alert['connection']
        alert_obj.alert_type = self.app.session.query( AlertTypes ).filter_by(name="Secondary WAN Inactive").first()
        device = self.check_get_device_stat(c, alert['xg'])
        device_db = self.app.session.query( Devices ).filter_by( serial=device[0]['serial']).first()
        if device_db:
                    alert_obj.devices.append(device_db)
        else:
            self.app.log.error("[UniFi plugin] TODO: Need to add the device")
            self.app.log.error("[UniFi plugin] " + device[0])
            sys.exit()
        db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
        db_alerts.add(alert_obj, "UniFi")

    def get_unifi_device_from_alert(self, c, unifi_alert):
        device_mac = ""
        # unifi alert key is usally in the format of 'EVT_SW_Lost_Contact' This takes the key and splits in along the '_'
        event = unifi_alert['key'].split("_")

        if event[1] == "GW":
            device_mac = unifi_alert['gw']
        elif event[1] == "AP":
            device_mac = unifi_alert['ap']
        elif event[1] == "SW":
            device_mac = unifi_alert['sw']
        elif event[1] == "XG":
            device_mac = unifi_alert['xg']
        elif event[1] == "BB":
            device_mac = unifi_alert['bb']
        elif event[1] == "LTE":
            device_mac = unifi_alert['dev']
        elif event[1] == "IPS":
            gateway_unifi = self.find_gateway(c.get_aps())
            device_mac = gateway_unifi['mac']
        elif event[1] == "USP":
            self.app.log.info("[UniFi plugin] don't have anything for UPS.")
            self.app.log.info("[UniFi plugin] " + str(unifi_alert))
        else:
            self.app.log.error("[UniFi plugin] First time seeing this alert. Need to create a ticket to update this script")
            self.app.log.info("[UniFi plugin] " + str(unifi_alert))

        if device_mac:
            device_stat = self.check_get_device_stat(c, device_mac)
            if device_stat: 
                return device_stat[0]
            else:
                # TODO This happens when an alert comes in for a device, but the device is no longer in the system. I'm manually clearing this alert, but we need to be able to handle this situation
                self.app.log.error("[UniFi plugin] UniFi return nonthing for deivce. " + str(unifi_alert))
                self.app.log.error("[UniFi plugin] " + str(event[1]))
                self.app.log.error("[UniFi plugin] " + str(device_mac))
        else:
            self.app.log.error("[UniFi plugin] Didn't find mac from alert. " + str(unifi_alert))

    def get_alert_type_from_alert(self, unifi_alert):
        # unifi alert key is usally in the format of 'EVT_SW_Lost_Contact' This takes the key and splits in along the '_'
        
        alert_type_name = ""
        # Normally the above splits the key into 3 parts, with the last part being a a camel case of the actual event
        # only exception I know of is Lost Contact, with is in the formate of 'Lost_Contact'
        self.app.log.debug("[UniFi plugin] Alert Key " + unifi_alert['key'])
        if unifi_alert['key'] == "EVT_GW_WANTransition":
            alert_type_name = "WAN Transition"
        elif unifi_alert['key'] == "EVT_AP_DetectRogueAP":
            alert_type_name = "Rogue AP"
        elif unifi_alert['key'] == "EVT_AP_RadarDetected":
            alert_type_name ="Radar Detected"
        elif unifi_alert['key'] == "EVT_SW_StpPortBlocking":
            alert_type_name = "Stp Port Blocking"
        elif unifi_alert['key'] == 'EVT_SW_PoeOverload':
            alert_type_name = "Poe Overload"
        # elif unifi_alert['key'] == 'EVT_SW_RestartedUnknown':
        #     # TODO Check other tickets and add notes about this if they are. Do not create a ticket based on this alert alone.
        #     self.app.log.error("[UniFi plugin] Event is Restart Unknown")
        #     self.app.log.error("[UniFi plugin] TODO Check other tickets and add notes about this if they are. Do not create a ticket based on this alert alone.")
        # LTE Stuff
        elif unifi_alert['key'] == "EVT_LTE_HardLimitUsed":
            alert_type_name = "LTE Hard Limit Used"
        elif unifi_alert['key'] == "EVT_LTE_Threshold":
            alert_type_name = "LTE Threshold"
        elif unifi_alert['key'] == "EVT_IPS_IpsAlert":
            alert_type_name = "IPS"
        else:
            event = unifi_alert['key'].split("_")
            if event[2] == "Lost" and event[3] == "Contact":
                alert_type_name = "Lost Contact"
            else:
                # TODO Create a ticket for any unknown alerts with a note to assign it to jeff after any actionable steps have been taken.
                self.app.log.error("[UniFi plugin] - Unknown alert type " + str(event))
                alert_type_name = "Unknown"
        self.app.log.debug("[UniFi plugin] alert type: " + alert_type_name)
        alert_type_db =  self.app.session.query( AlertTypes ).filter_by(name=alert_type_name).first()
        
        if alert_type_db:
            return alert_type_db
        else:
            #add alert type to database
            pass

    def create_alert_unifi_object(self, unifi_alert, company_db, unifi_site_db):
        device_db = []

        controller = self.app.session.query(UniFi_Controllers).filter_by(primary_key=unifi_site_db.controller_key).first()
        c = UniFiControllerHandler.controller_api_object(self, controller, unifi_site_db.name)

        device_unifi = self.get_unifi_device_from_alert(c, unifi_alert)

        if device_unifi is not None and device_unifi:
            self.app.log.debug("[UniFi plugin] " + company_db.name + " - device pulled from Unifi.")
            device_db = self.app.session.query( Devices ).filter_by( serial=device_unifi['serial'] ).first()
            
            if not device_db:
                self.app.log.debug("[UniFi plugin] Add device to Database")
                api_devices = self.app.handler.get('unifi_device_interface', 'unifi_device_handler', setup=True)
                api_devices.update_db(device_unifi, unifi_site_db.name, controller)
                device_db = self.app.session.query( Devices ).filter_by( serial=device_unifi['serial'] ).first()

        # TODO The alert processing functions are not using last_timestamp, maybe fix them to use this instead of the orginal datetime from the event
        
        unif_alert_obj = self.UniFiAlertObject(
                # Orginal Object
                last_timestamp = datetime.strptime(unifi_alert['datetime'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC),
                source_db = self.app.session.query( Sources ).filter_by(plugin_name="UniFi", tenant_key=controller.primary_key).first(),
                devices = [device_db],
                company_db = company_db,

                title_append = " (" + str(unifi_site_db.desc) + ")",
                useful_information = "UniFi Controller: https://" +  controller.host + ":" + str(controller.port) + "/manage/" + str(unifi_site_db.name) +"/",

                # UniFi Alert Object add ons
                alert_unifi = unifi_alert,
                device_unifi = device_unifi,
                connection = c,
                controller = controller,
                site_name = unifi_site_db.name
            )

        alert_type_db = self.get_alert_type_from_alert(unifi_alert)
        if alert_type_db:
            unif_alert_obj.alert_type = alert_type_db
        else:
            self.app.log.error("[UniFi plugin] create_alert_unifi_object - No alert_type" )
            self.app.log.error("[UniFi plugin] " + unifi_alert['key'])
            sys.exit()

        return unif_alert_obj

    def alert_site_down(self, alert_obj):
        self.app.log.error("[UniFi plugin] Site Down")
        c = alert_obj.connection
        alert_obj.alert_type =  self.app.session.query( AlertTypes ).filter_by(name="Internet Outage").first()

        db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
        db_alerts.add(alert_obj, "UniFi")

        if alert_obj.alert_unifi is not None:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def find_gateway(self, devices_unifi):
        # devices_unifi output to c.get_aps()
        # TODO Maybe look it up in the database to reduce API calls
        for device_unifi in devices_unifi:
            if device_unifi['type'] == "ugw" or device_unifi['type'] == "uxg":
                return device_unifi

    def alert_lost_contact(self, alert_obj):
        # TODO check last complete device sync date, if alert if older, clear alert, since we would catch the same information that way
        # TODO: Add 'last seen' data to ticket if possible
        # TODO: Add what the device's uplink is and it's status
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection

        device = alert_obj.device_unifi
        if device:
            if device['state'] == 1:
                self.app.log.debug("[UniFi plugin] Device is online now, archiving alert")
                if alert_obj.alert_unifi is not None:
                    self._archive_alert(c, alert_obj.alert_unifi['_id'])
            elif device['state'] != 1:
                devices_unifi = c.get_aps()
                
                # add all down devices to the ticket
                anything_up = False
                for device_unifi in devices_unifi:
                    if device_unifi['state'] == 1:
                        anything_up = True
                    elif device_unifi['state'] != 1 and device_unifi.get('serial') is not None:
                        # Add device to alert
                        device_db = self.app.session.query( Devices ).filter_by( serial=device_unifi['serial'] ).first()        
                        if device_db is None:
                            device_handles = self.app.handler.get('unifi_device_interface', 'unifi_device_handler', setup=True)
                            device_handles.update_db(device_unifi, alert_obj.site_name, alert_obj.controller)
                            device_db = self.app.session.query( Devices ).filter_by( serial=device_unifi['serial'] ).first()
                            if device_db is None: 
                                self.app.log.error("[UniFi plugin] Cannot find device in database")
                                sys.exit(device_unifi)
                        alert_obj.devices.extend([device_db])
                gateway_unifi = None
                gateway_db = None
                gateway_down = False
                if device['type'] == "gw":
                    self.app.log.debug("[UniFi plugin] This device is the gateway")
                    gateway_unifi = device[0]
                    gateway_down = True
                else:
                    # Find Gateway
                    gateway_unifi = self.find_gateway(devices_unifi)
                    if gateway_unifi is not None:
                        if gateway_unifi['state'] == 0:
                            self.app.log.debug("[UniFi plugin] Gateway is also down")
                            # Move Gateway to the first device
                            device_db = self.app.session.query( Devices ).filter_by( serial=gateway_unifi['serial'] ).first()
                            if device_db is None:
                                device_handles = self.app.handler.get('unifi_device_interface', 'unifi_device_handler', setup=True)
                                device_handles.update_db(device, alert_obj.site_name, alert_obj.controller)
                                device_db = self.app.session.query( Devices ).filter_by( serial=gateway_unifi['serial'] ).first()

                            index_of_gateway = alert_obj.devices.index(device_db)
                            gateway_db = alert_obj.devices.pop(index_of_gateway)
                            alert_obj.devices.insert(0, gateway_db)
                            gateway_down = True
                

                # Check if this device is a Gateway
                if gateway_down:
                    self.alert_site_down(alert_obj)
                else:
                    if alert_obj.devices == None: sys.exit("No Devices")
                    self.app.log.debug("[UniFi plugin] Device is still off line. Creating ticket")
                    db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
                    db_alerts.add(alert_obj, "UniFi")
                    if alert_obj.alert_unifi is not None:
                        self._archive_alert(c, alert_obj.alert_unifi['_id'])

                    # TODO One possible fix is to power cycle the switch port if the devices is on a POE switch and powered by that switch.
                    # TODO Most of these are solved by sending a set inform. Need to work on that.
        else:
            self.app.log.debug("[UniFi plugin] the device is not in the controller, it's probably because the device has been removed")
            if alert_obj.alert_unifi is not None:
                self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_wan_transition(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        alert_date = dateutil.parser.isoparse(alert_obj.alert_unifi['datetime'])
        if alert_date.strftime("%Y-%m-%d") == datetime.today().strftime("%Y-%m-%d"):
            if alert_obj.device_unifi:
                if alert_obj.device_unifi['wan1']['ip'] != alert_obj.device_unifi['uplink']['ip']:
                    self.app.log.debug("[UniFi plugin] Primary WAN is down.. Creating ticket")
                    db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
                    db_alerts.add(alert_obj, "UniFi")
                else:
                    self._archive_alert(c, alert_obj.alert_unifi['_id'])
            else:
                self.app.log.error("EVT_GW_WANTransition - no device was returned")
                self.app.log.error(alert_obj.alert_unifi)
                sys.exit()
        else:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_stp_port_blocking(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        #alert_obj.alert_type = self.app.session.query( AlertTypes ).filter_by(name="STP Port Blocking").first()
        port = int(alert_obj.alert_unifi['port']) -1
        
        if alert_obj.device_unifi['port_table'][port]['stp_state'] != 'forwarding':
            self.app.log.debug("[UniFi plugin] STP Port Blocked. Creating ticket")
            db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
            db_alerts.add(alert_obj, "UniFi")
        elif alert_obj.device_unifi['port_table'][port]['stp_state'] != 'disabled':
            self._archive_alert(c, alert_obj.alert_unifi['_id'])
        else:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])   

    def alert_detect_rouge_ap(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        alert_date = dateutil.parser.isoparse(alert_obj.alert_unifi['datetime'])

        if alert_date.strftime("%Y-%m-%d") == datetime.today().strftime("%Y-%m-%d"):
            if alert_obj.devices:
                # TODO We should put this under "resolution" and it should probably be a link to docuemtnation
                alert_obj.useful_information += "\n\n"
                alert_obj.useful_information += "Note: Alert is assoicated with the device UniFi AP that detected the Rogue AP"
                alert_obj.useful_information += "\n"
                alert_obj.useful_information += "If this is a known Access Point and you wish to stop getting these alerts:\n"
                alert_obj.useful_information += " * Consult with a senior tech!\n"
                alert_obj.useful_information += " * Log into the UniFi Controller\n"
                alert_obj.useful_information += " * Make sure you are using 'Legacy Mode'\n"
                alert_obj.useful_information += " * Under 'Insight' on the left\n"
                alert_obj.useful_information += " * Pick 'Neighboring Access Point' in the upper left-hand drop-down list\n"
                alert_obj.useful_information += " * Look for an AP that has a red dot in the 'Rogue' Column\n"
                alert_obj.useful_information += " * On the far right of that row, when you hover over it, the words 'Mark as known' will appear. Pick it.\n"
                alert_obj.useful_information += " * Archive all Rogue AP alerts under 'Alerts'"

                db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
                db_alerts.add(alert_obj, "UniFi")
                self._archive_alert(c, alert_obj.alert_unifi['_id'])
            else:
                self.app.log.error("EVT_AP_DetectRogueAP - no device was returned")
                self.app.log.error(alert_obj.alert_unifi)
                sys.exit()
        else:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_radar_detected(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        self.app.log.warning( alert_obj.alert_type.name + " - Not processing these alerts")
        self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_lte_hard_limit_used(self, alert_obj):
	    # TODO Link this to the Threshold ticket, but change status to new and prioirty to Crital
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        alert_date = dateutil.parser.isoparse(alert_obj.alert_unifi['datetime'])
        if alert_date.month == datetime.now().month:
            if alert_obj.device_unifi:
                self.app.log.error("[UniFi plugin] TODO - Need to check if there is another LTE ticket and add to that one")
                self.app.log.debug("[UniFi plugin] LTE Hard Limit Used. Creating ticket")
                db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
                db_alerts.add(alert_obj, "UniFi")
            else:
                self.app.log.error( alert_obj.alert_type.name + " - no device was returned")
                sys.exit()
        else:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_lte_hard_limit_cutoff(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        alert_date = dateutil.parser.isoparse(alert_obj.alert_unifi['datetime'])
        if alert_date.month == datetime.now().month:
            if alert_obj.device_unifi:
                self.app.log.error("[UniFi plugin] TODO - Need to check if there is another LTE ticket and add to that one")
                self.app.log.debug("[UniFi plugin] LTE Hard Limit Cutoff. Creating ticket")
                db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
                db_alerts.add(alert_obj, "UniFi")
            else:
                self.app.log.error( alert_obj.alert_type.name + " - no device was returned")
                sys.exit()
        else:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_lte_threshold(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        alert_date = dateutil.parser.isoparse(alert_obj.alert_unifi['datetime'])
        if alert_date.month == datetime.now().month:
            if alert_obj.device_unifi:
                self.app.log.error("[UniFi plugin] TODO - Need to check if there is another LTE ticket and add to that one")
                self.app.log.debug("[UniFi plugin] LTE threshold. Creating ticket")
                db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
                db_alerts.add(alert_obj, "UniFi")
            else:
                self.app.log.error( alert_obj.alert_type.name + " - no device was returned")
                sys.exit()
        else:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_ips(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        #alert_date = dateutil.parser.isoparse(alert_obj.alert_unifi['datetime'])
        self.app.log.info("[UniFi plugin] We are ignoring these threats right now.")
        self.app.log.info("[UniFi plugin] " + alert_obj.alert_unifi['msg'])

    def alert_poe_overload(self,alert_obj):
        # TODO alert has the port that is overloaded. Might be useful to add that to the ticket.

        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        alert_date = dateutil.parser.isoparse(alert_obj.alert_unifi['datetime'])
        alert_obj.useful_information += "\n\n"
        alert_obj.useful_information += "Alert Message: " + str(alert_obj.alert_unifi('msg'))

        if alert_date.strftime("%Y-%m-%d") == datetime.today().strftime("%Y-%m-%d"):
            if alert_obj.devices:
                db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
                db_alerts.add(alert_obj, "UniFi")
                self._archive_alert(c, alert_obj.alert_unifi['_id'])
            else:
                self.app.log.error("EVT_SW_PoeOverload - no device was returned")
                self.app.log.error(alert_obj.alert_unifi)
                sys.exit()
        else:
            self._archive_alert(c, alert_obj.alert_unifi['_id'])

    def alert_unknown_alert(self, alert_obj):
        self.app.log.debug("[UniFi plugin] " + alert_obj.company_db.name + " - " + alert_obj.alert_type.name)
        c = alert_obj.connection
        if alert_obj.devices:
            # TODO Need to create a ticket that gets assigned to me so I can create a function to deal with this.
            alert_obj.useful_information += "\n\n"
            alert_obj.useful_information += "Note: This is an unknown alert to the system."
            alert_obj.useful_information += "Alert Key: " + alert_obj.alert_unifi['key']
            alert_obj.useful_information += "Alert Message: " + alert_obj.alert_unifi['msg']
            alert_obj.useful_information += "\n"
            alert_obj.useful_information += "After you are done with this ticket, please assign it to Jeff."
            alert_obj.useful_information += "\n"
            alert_obj.useful_information += "Alert json: " + str(alert_obj.alert_unifi)

            db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
            db_alerts.add(alert_obj, "UniFi")
            #self._archive_alert(c, alert_obj.alert_unifi['_id'])
        else:
            self.app.log.error("[UniFi plugin] " + str(alert_obj.alert_unifi['key']))
            self.app.log.error(alert_obj.alert_unifi)
            #sys.exit()

    def process_alert(self, alert_obj):
        if alert_obj.alert_type:
            # Generic
            if alert_obj.alert_type.name == "Lost Contact":
                self.alert_lost_contact(alert_obj)
            # Gateway
            elif alert_obj.alert_type.name == "WAN Transition":
                self.alert_wan_transition(alert_obj)
            # Switches
            elif alert_obj.alert_type.name == "Stp Port Blocking":
                self.alert_stp_port_blocking(alert_obj)
            elif alert_obj.alert_type.name == "Poe Overload":
                self.alert_poe_overload(alert_obj)
            # APs
            elif alert_obj.alert_type.name == "Rogue AP":
                self.alert_detect_rouge_ap(alert_obj)
            elif alert_obj.alert_type.name == "Radar Detected":
                self.alert_radar_detected(alert_obj)
            # LTE
            elif alert_obj.alert_type.name == "LTE Hard Limit Used":
                self.alert_lte_hard_limit_used(alert_obj)
            elif alert_obj.alert_type.name == "LTE Hard Limit Cutoff":
                self.alert_lte_hard_limit_cutoff(alert_obj)
            elif alert_obj.alert_type.name == "LTE Threshold":
                self.alert_lte_threshold(alert_obj)
            # IPS
            elif alert_obj.alert_type.name == "IPS":
                self.alert_ips(alert_obj)
            else:
                self.alert_unknown_alert(alert_obj)
        else:
            self.app.log.error("[UniFi plugin] No alert_type" )
            sys.exit()

    def verify_contract(self, site_db):
        # TODO Need to check parent for a contract
        # TODO We should create a contract database outside of autotask that just has basic information

        # TODO Can move to using Contract Category's Code below was written when there was a mapping issue with Contract Categories

        from  ..autotask_plugin.models.database import Autotask_Contracts, Autotask_Companies, Autotask_Contract_Category
        autotask_company_db = self.app.session.query( Autotask_Companies ).filter_by( company_key=site_db.parent_id  ).first()

        contracts_db = self.app.session.query( Autotask_Contracts ).filter_by( autotask_company_key=autotask_company_db.primary_key ).all()
        convered = False
        # Move to Contract_category values
        contracts_type_covered = [
            "Annual Unifi Controller",
            "C4 Legacy SLA",
            "Managed Service - Protect",
            "Managed Services - Base",
            "Managed Services - HelpDesk",
            "Managed Services - Protect",
            "Managed Services - Protect + HelpDesk"
        ]
        for contract in contracts_db:
            #contract_catagory_db = self.app.session.query( Autotask_Contract_Category ).filter_by( value=contract.contract_category_value, isActive=True).first()
            if contract.autotask_name in contracts_type_covered:
                convered = True
        if not convered:
            self.app.log.info("[UniFi plugin] " + site_db.desc +" has no contract!")
            # TODO Might be able to create some common functions with create_alert_unifi_object
            unifi_devices_db = self.app.session.query(UniFi_Devices).filter_by( unifi_sites_key=site_db.primary_key ).all()
            devices_db = []
            for unifi_device_db in unifi_devices_db:
                device_db = self.app.session.query(Devices).filter_by( primary_key=unifi_device_db.device_key ).first()
                devices_db.append(device_db)

            controller = self.app.session.query(UniFi_Controllers).filter_by(primary_key=site_db.controller_key).first()
            c = UniFiControllerHandler.controller_api_object(self, controller, site_db.name)
            company_db = self.app.session.query( Companies ).filter_by( primary_key=autotask_company_db.company_key  ).first()
            alert_type_db = self.app.session.query( AlertTypes ).filter_by( name="No Contract"  ).first()
            unif_alert_obj = self.UniFiAlertObject(
                    # Orginal Object
                    source_db = self.app.session.query( Sources ).filter_by(plugin_name="UniFi", tenant_key=controller.primary_key).first(),
                    devices = devices_db,
                    company_db = company_db,

                    title_append = " (" + str(site_db.desc) + ")",
                    useful_information = "UniFi Controller: https://" +  controller.host + ":" + str(controller.port) + "/manage/" + str(site_db.name) +"/",
                    alert_type = alert_type_db,

                    # UniFi Alert Object add ons
                    connection = c,
                    controller = controller,
                    site_name = site_db.name
            )
            db_alerts = self.app.handler.get('db_interface', 'db_alerts', setup=True)
            db_alerts.add(unif_alert_obj, "UniFi")

            # TODO Check if any of the device are active.
            # TODO Create ticket for the site
            # Need an ignore list

    def verify_old_alerts(self, unifi_site_db):
        company_db = self.app.session.query( Companies ).filter_by( primary_key=unifi_site_db.parent_id  ).first()
        self.app.log.info("[UniFi plugin] Verifing old alerts for " + company_db.name + " Site: " + unifi_site_db.desc + " ID: " + unifi_site_db.name)
        source_db = self.app.session.query( Sources ).filter_by( plugin_name="UniFi", tenant_key=unifi_site_db.controller_key ).first()
        if source_db is None:
            self.app.log.error("[UniFi plugin] Cannot fine source for alert!")
        alerts_db = self.app.session.query( Alerts ).filter_by( source_key=source_db.primary_key, company_key=unifi_site_db.parent_id ).all()
        devices_unifi = []
        for alert in alerts_db:
            if alert.alert_type.name == "Lost Contact" or alert.alert_type.name == "Internet Outage":
                devices_back_online = 0
                associated_devices = self.app.session.query(Devices).\
                    join(device_alert_association, device_alert_association.c.device_key == Devices.primary_key).\
                    join(Alerts, device_alert_association.c.alert_key == Alerts.primary_key).\
                    filter(Alerts.primary_key == alert.primary_key).all()
                
                for device in associated_devices:
                    controller_db = self.app.session.query(UniFi_Controllers).filter_by(primary_key=source_db.tenant_key).first()
                    c = UniFiControllerHandler.controller_api_object(self, controller_db, unifi_site_db.name)
                    device_unifi = self.check_get_device_stat(c, device.serial)[0]
                    devices_unifi.append(device_unifi)
                    if device_unifi['state'] != 0:
                        devices_back_online += 1
                if devices_back_online > 0:
                    if devices_back_online == len(devices_unifi):
                        alert.cleared = True
                        self.app.session.commit()
                        # TODO Create and call Hook for cleared alerts | Maybe add a Autotask check for cleared alerts that is part of full run
                        # TODO Delete alert and assoicated data




















                        self.app.log.error("[UniFi plugin] All devices are back online. Close ticket.")
                    else:
                        self.app.log.error("[UniFi plugin] At least one fo the devices are back online. Need to update ticket.")
                    sys.exit()
            else:
                sys.exit(alert.alert_type.name)

    def sync_site(self, controller, site_unifi):
        c = UniFiControllerHandler.controller_api_object(self, controller, site_unifi['name'])

        unifi_site_db = self.app.session.query( UniFi_Sites ).filter_by( name=site_unifi['name'], controller_key=controller.primary_key  ).first()
        if unifi_site_db: 
            company_db = self.app.session.query( Companies ).filter_by( primary_key=unifi_site_db.parent_id  ).first()
        else:
            self.app.log.debug("[UniFi plugin] Pushing Site to database: " + site_unifi['desc'])
            site_handler = self.app.handler.get('unifi_site_interface', 'unifi_site_handler', setup=True)
            site_handler.update_db(site_unifi, controller)
            unifi_site_db = self.app.session.query( UniFi_Sites ).filter_by( name=site_unifi['name'], controller_key=controller.primary_key  ).first()
            company_db = self.app.session.query( Companies ).filter_by( primary_key=unifi_site_db.parent_id  ).first()

        if company_db:
            # self.verify_old_alerts(unifi_site_db)

            self.app.log.info("[UniFi plugin] Syning alerts for " + company_db.name + " Site: " + site_unifi['desc'] + " ID: " + site_unifi['name'])

            first_wan_transition = True
            alerts = c.get_alerts_unarchived()
            for alert in alerts:
                if alert['key'] == 'EVT_GW_WANTransition' and first_wan_transition == False:
                    self._archive_alert(c, alert['_id'])
                else:
                    if alert['key'] != 'EVT_IPS_IpsAlert':
                        if unifi_site_db.parent_id:
                            alert_unifi_obj = self.create_alert_unifi_object(alert, company_db, unifi_site_db)
                            # Setting up a timeout
                            p = multiprocessing.Process(target=self.process_alert(alert_unifi_obj))
                            p.start()
                            p.join(timeout=30)
                            if p.is_alive():
                                 p.terminate()
                                 self.app.log.warn("[UniFi plugin] Function was taking too long. Terminating")
                            #self.process_alert(alert_unifi_obj)
                            if alert['key'] == 'EVT_GW_WANTransition':
                                first_wan_transition = False
        else:
            self.app.log.warning("[UniFi plugin] Site is not assoicated with a company. " + site_unifi['desc'] + " " + site_unifi['name'])
            self.app.log.warning("[UniFi plugin] Full Site path: https://" +  controller.host + ":" + str(controller.port) + "/manage/" + str(unifi_site_db.name) +"/")

    def sync_site_by_id(self, controller_name, site_id):
        controller = self.app.session.query(UniFi_Controllers).filter_by(name=controller_name).first()
        c = UniFiControllerHandler.controller_api_object(self, controller)
        for site in c.get_sites():
            if site['name'] == site_id:
                self.sync_site(controller, site)
                break

    def sync_controller(self, controller_name):
        # TODO Track companies not assoicated wiht a site, then create an alert with all companies and how to fix them. 
        # TODO Create a funtion that allows us to set a site to ignore (for test sites, etc)
        controller = self.app.session.query(UniFi_Controllers).filter_by(name=controller_name).first()
        
        c = UniFiControllerHandler.controller_api_object(self, controller)

        sites = c.get_sites()
        for site in sites:
            self.sync_site(controller, site)

    def sync_all(self):
        controllers = self.app.session.query(UniFi_Controllers).all()

        for controller in controllers:
            self.app.log.info("[UniFi plugin] Syncing for Controller: " + controller.name)
            self.sync_controller(controller.name)

class UniFiHandler(UniFiInterface, Handler):
    class Meta:
        label = 'unifi_handler'

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     pass
        #self.controller = None
        # print(self.app)
        # sys.exit()
        #self.controller = UniFiControllerHandler()
        #self.controller = self.app.handler.get('unifi_controller', 'unifi_controller', setup=True)
    #     self.controller = self.app.handler.get('controller', 'unifi_controller')
    #     #self.site = self.app.handler.get('controller', 'unifi_site')
    #     #self.device = self.app.handler.get('device', 'unifi_device')
        
    # def _post_setup(self, *args, **kwargs):
    #     super()._post_setup(*args, **kwargs)
    #     self.controller = self.app.handler.get('unifi_controller', 'unifi_controller', setup=True)

class UniFiAPI(UniFiHandler):
    class Meta:
        label = 'unifi_api'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def _setup(self, *args, **kwargs):
        super()._setup(*args, **kwargs)
        self.controller = self.app.handler.get('unifi_controller', 'unifi_controller', setup=True)
        self.site = self.app.handler.get('unifi_site_interface', 'unifi_site_handler', setup=True)
        self.device = self.app.handler.get('unifi_device_interface', 'unifi_device_handler', setup=True)
        self.alert = self.app.handler.get('unifi_alerts_interface', 'unifi_alerts_handler', setup=True)

    def site_health(self, controller_name, site_id):
        controller = self.app.session.query(UniFi_Controllers).filter_by(name=controller_name).first()
        c = UniFiControllerHandler.controller_api_object(self, controller)
        # TODO pull site from the database
        for site in c.get_sites():
            if site['name'] == site_id:
                health = c.get_healthinfo()
                self.app.log.info("[UniFi plugin] " + str(health))
                break

    def pull_device_by_mac(self, mac, controller_name, site_id):
        controller = self.app.session.query(UniFi_Controllers).filter_by(name=controller_name).first()
        c = UniFiControllerHandler.controller_api_object(self, controller)
        for site in c.get_sites():
            if site['name'] == site_id:
                c.site_id = site["name"]
                device = self.alert.check_get_device_stat(c, mac)
                self.app.log.info("[UniFi plugin] " + str(device))
                break

def full_run(app):
    unifi = app.handler.get('unifi_interface', 'unifi_api', setup=True)
    controllers = app.session.query(UniFi_Controllers).all()
    for controller in controllers:
        # TODO add a timeout feature when running these. Look into threading or Concurrent Futures

        # TODO Make the time configuratable        
        do_full_run = True
        if controller.last_full_sync != None:
            now = datetime.now()
            time_diff = now - controller.last_full_sync
            if time_diff <= timedelta(days=1):
                do_full_run = False
       
        if do_full_run:
            app.log.info("[UniFi plugin] Syncing sites")
            try:
                unifi.site.sync_all(controller)
            except Exception as e:
                app.log.error("[UniFi plugin] Site Sync All Error: " + str(e))

            app.log.info("[UniFi plugin] Syncing devices")
            try:
                unifi.device.sync_controller(controller.name)
            except Exception as e:
                app.log.error("[UniFi plugin] Device Sync Controller Error:" + str(e))

            app.log.info("[UniFi plugin] Syncing alerts")
            try:
                unifi.alert.sync_controller(controller.name)
            except Exception as e:
                app.log.error("[UniFi plugin] Alert Sync Controller Error:" + str(e))

            controller.last_full_sync = datetime.now()
            app.session.commit()
        else:
            app.log.info("[UniFi plugin] Controller: " + controller.name + " - Last run was done within 24 hours. Skipping site and device syncing")
            app.log.info("[UniFi plugin] Syncing alerts")
            try:
                unifi.alert.sync_controller(controller.name)
            except Exception as e:
                app.log.error("[UniFi plugin] Alert Sync Controller Error:" + str(e))