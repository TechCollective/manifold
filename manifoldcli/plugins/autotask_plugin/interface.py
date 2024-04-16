from abc import abstractmethod
from cement import Interface

class AutotaskInterface(Interface):
    class Meta:
        interface = 'autotask_interface'

class AutotaskTenantInterface(Interface):
    class Meta:
        interface = 'autotask_tenant_interface'

    @abstractmethod
    def list(self):
        """
        Setup a new tenant
        """
        pass

    @abstractmethod
    def add(self, name, host):
        """
        Setup a new tenant
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Delete a tenant from database
        """
        pass

    @abstractmethod
    def disable(self):
        """
        disable a tenant
        """
        pass

    @abstractmethod
    def enable(self):
        """
        enable a disabled tenant
        """
        pass

class AutotaskCompanyInterface(Interface):
    class Meta:
        interface = 'autotask_company_interface'
    
    @abstractmethod
    def sync_all(self, tenant):
        """
        2 steps
            * Loop through all sites on a Unifi tenant, creates a site object, then sends them to get.
            * Loops through all sites for this tenant in the database, creates a site object, then sends them to post.
        
        Args:
            tenant (tenant_obj): all information for the tenant.
        """
        pass
    
    @abstractmethod
    def update_db(self, company, tenant):
        """
        Verify a company is in the DB and is up to date.

        Args:
            company (company_obj): all information for the company.
            tenant (tenant_obj): all information for the tenant.
        """
        pass
    
    @abstractmethod
    def post(self, site, tenant):
        """
        Verify site is up to date on the tenant side.

        Args:
            site (site_obj): all information for the site.
            tenant (tenant_obj): all information for the tenant.
        """
        pass

    @abstractmethod
    def hooks(self, site, tenant, source):
        pass

class AutotaskContractInterface(Interface):
    class Meta:
        interface = 'autotask_contract_interface'

    @abstractmethod
    def sync_company(self, tenant_name, company_id):
        """
            Syncs a company's contract with the database
        """
        pass

    @abstractmethod
    def sync_tenant(self, tenant):
        """
            Syncs all company's contract within a tenant with the database
        """
        pass

    @abstractmethod
    def sync_all(self):
        """
            Syncs all company's contract from all tenants with the database
        """
        pass
    # @abstractmethod
    # def hooks(self, site, tenant, source):
    #     pass

class AutotaskDeviceInterface(Interface):
    class Meta:
        interface = 'autotask_device_interface'

    @abstractmethod
    def sync_company(self, tenant):
        """
        Syns all deivces for a company
        
        Args:
            tenant (tenant_obj): all information for the tenant.
        """
        pass

    @abstractmethod
    def update_db(self, device, company, tenant):
        """
        Verify a device is in the DB and is up to date.

        Args:
            device (device_obj): all information for the deivce.
            company (company_obj): all information for the company.
            teanant (tenant_obj): all information for the tenant.
        """
        pass
        
    @abstractmethod
    def post(self, device, company, tenant):
        """
        Verify device is up to date on the Autotask tenant side.

        Args:
            device (device_obj): all information for the device.
            company (company_obj): all information for the company.
            tenant (tenant_obj): all information for the tenant.
        """
        pass

class AutotaskTicketInterface(Interface):
    class Meta:
        interface = 'autotask_ticket_interface'

    @abstractmethod
    def create(self, alert):
        """
        Add a new Ticket to Autotask
        
        Args:
            company (company_obj): all information for the company.
            teanant (tenant_obj): all information for the tenant.          
        """
        pass

    @abstractmethod
    def update(self, tenant, company, ticket_no, note, status):
        """
        add a note to a ticket

        Args:
            company (company_obj): all information for the company.
            teanant (tenant_obj): all information for the tenant.
            ticket_no: The autotask ticket number
            note: to add to ticket
            status: the new status for the ticket (complete)
        """
        pass
