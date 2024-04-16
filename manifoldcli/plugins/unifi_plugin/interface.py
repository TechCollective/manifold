from abc import abstractmethod
from cement import Interface

class UniFiControllerInterface(Interface):
    class Meta:
        interface = 'unifi_controller'

    @abstractmethod
    def list(self):
        """
        Setup a new controller
        """
        pass

    @abstractmethod
    def add(self, name, url, port):
        """
        Setup a new controller
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete a controller from database
        """
        pass

    @abstractmethod
    def disable(self):
        """
        disable a controller
        """
        pass

    @abstractmethod
    def enable(self):
        """
        enable a disabled controller
        """
        pass

    @abstractmethod
    def auth(self, controller, user, password):
        """
        Setup Authinication for a Controller
        
        Args:
            controller (controller_obj): all information for the controller.
        """
        pass

class UniFiSiteInterface(Interface):
    class Meta:
        interface = 'unifi_site_interface'
    
    @abstractmethod
    def sync_all(self, controller):
        """
        2 steps
            * Loop through all sites on a Unifi controller, creates a site object, then sends them to get.
            * Loops through all sites for this controller in the database, creates a site object, then sends them to post.
        
        Args:
            controller (controller_obj): all information for the controller.
        """
        pass
    
    @abstractmethod
    def update_db(self, site, controller):
        """
        Verify a site is in the DB and is up to date.

        Args:
            site (site_obj): all information for the site.
            controller (controller_obj): all information for the controller.
        """
        pass
    
    @abstractmethod
    def post(self, site, controller):
        """
        Verify site is up to date on the controller side.

        Args:
            site (site_obj): all information for the site.
            controller (controller_obj): all information for the controller.
        """
        pass
    
    @abstractmethod
    def hooks(self, site, controller, source):
        pass

class UniFiDeviceInterface(Interface):
    class Meta:
        interface = 'unifi_device_interface'

    @abstractmethod
    def sync_site(self, controller):
        """
        Syns all deivces for a site
        
        Args:
            site (site_obj): all information for the site.
            controller (controller_obj): all information for the controller.
        """
        pass

    @abstractmethod
    def update_db(self, device, site, controller):
        """
        Verify a device is in the DB and is up to date.

        Args:
            device (device_obj): all information for the deivce.
            site (site_obj): all information for the site.
            controller (controller_obj): all information for the controller.
        """
        pass
        
    @abstractmethod
    def post(self, device, site, controller):
        """
        Verify device is up to date on the controller side.

        Args:
            device (device_obj): all information for the device.
            site (site_obj): all information for the site.
            controller (controller_obj): all information for the controller.
        """
        pass

class UniFiAlertsInterface(Interface):
    class Meta:
        interface = 'unifi_alerts_interface'    

    @abstractmethod
    def device_alerts(self, device_unifi):
        """
        Looks for alerts within the device from UniFi

        Args:
            device_unifi (device_obj): all information for the device.
        """
        pass

    def sync_controller(self, controller_name):
        pass


    # @abstractmethod
    # def get_all(self, controller):
    #     """
    #     Loops through all sites, sends site to get_site
        
    #     Args:
    #         controller (controller_obj): all information for the controller.
    #     """
    #     pass
    
    # @abstractmethod
    # def get_site(self, site, controller):
    #     """
    #     Loops through all alerts for a site, creates an alert object and sends it over to alert_update_db
        
    #     Args:
    #         site (site_obj): all information for the site.
    #         controller (controller_obj): all information for the controller.
    #     """
    #     pass
    
    
    # @abstractmethod
    # def get(self, alert, site, controller):
    #     """
    #     Verify an alert is in the DB and is up to date.

    #     Args:
    #         alert (alert_object): all information about an alert
    #         site (site_obj): all information for the site.
    #         controller (controller_obj): all information for the controller.
    #     """
    #     pass

class UniFiClientsInterface(Interface):
   class Meta:
        interface = 'unifi_clients'

class UniFiInterface(Interface):
    class Meta:
        interface = 'unifi_interface'

    # def __init__(self, *args, **kwargs):
    #     """
    #     You should create an __init__ that addes the controller, site and device handlers
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         self.controller = self.app.handler.get('controller', 'unifi_controller')
    #         self.site = self.app.handler.get('controller', 'unifi_site')
    #         self.device = self.app.handler.get('device', 'unifi_device')
    #     """
    #     pass