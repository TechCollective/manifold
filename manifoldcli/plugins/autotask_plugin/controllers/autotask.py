
from cement import Controller, ex
from ....core.db_interface import *
from ....core.db_devices_handler import *
from ..interface import *
from ..handler import *

class Autotask(Controller):
    class Meta:
        label = 'autotask'
        stacked_on = 'base'
        stacked_type = 'nested'
        interfaces = [DBInterface, AutotaskInterface, AutotaskTenantInterface, AutotaskCompanyInterface, AutotaskTicketInterface, AutotaskContractInterface]
        handlers = [DBDevicesHandler, AutotaskTenantHandler, AutotaskAPI, AutotaskCompanyHandler, AutotaskTicketHandler, AutotaskContractHandler]

    def _default(self):
        self._parser.print_help()

    @ex(
        help='Setup a new Autotask Tenant',
        arguments=[
            (['--name'], {
                'help': "Your name for the Autotask Tenant",
                'required': True,
                'dest': 'autotask_name'
                
            }),
            (['--host'],{
                'help': 'URL for the Autotask Tenant',
                'required': True,
                'dest': 'autotask_host'
            }),
        ]
    )
    def add_autotask_tenant(self):
        """Setup Autotask Tenant"""
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        autotask.tenant.add(name=self.app.pargs.autotask_name, tenant_host=self.app.pargs.autotask_host)
        # FIXME output better!
        print("Create an API user in your Autotask User, then add the following to your autotask enviroment file, replace wiht the correct values.")
        print(" " + self.app.pargs.autotask_name + ".user=USERNAME")
        print(" " + self.app.pargs.autotask_name + ".password=PASSWORD")
        print(" " + self.app.pargs.autotask_name + ".interactioncode=PASSWORD")

    @ex(
        help='List all Autotask Tenants'
    )
    def list_tenants(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        tenants = autotask.tenant.list()
        # FIXME fix output
        print("Autotask Tenants:")
        for tenant in tenants:
            print(" - " + tenant.name + " " + tenant.host )

    @ex(
        help='Sync all companies in a tenant',
        arguments=[
            (['--tenant-name'], {
                'help': "Tenant you will to sync",
                'required': True,
                'dest': 'tenant_name'
            })
        ]
    )
    def sync_tenant_companies(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        tenants = autotask.tenant.list()
        for tenant in tenants:
            autotask.company.sync_tenant(tenant)

    @ex(
        help='Sync device for a company',
        arguments=[
            (['--company-id'], {
                'help': "Company ID you will to sync",
                'required': True,
                'dest': 'company_id'
                
            }),
            (['--tenant-name'], {
                'help': "Tenant you will to sync",
                'required': True,
                'dest': 'tenant_name'
                
            })]
    )
    def sync_company_devices(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        autotask.device.sync_company(self.app.pargs.tenant_name, self.app.pargs.company_id)

    @ex(
        help='Sync all devices for all companies on an Autotask tenant',
        arguments=[
            (['--tenant-name'], {
                'help': "Tenant name",
                'required': True,
                'dest': 'tenant_name'
                
            })]
    )
    def sync_tenant_devices(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        autotask.device.sync_tenant(self.app.pargs.tenant_name)


    # @ex(
    #     help='Sync contracts for a company',
    #     arguments=[
    #         (['--company-id'], {
    #             'help': "Company ID you will to sync",
    #             'required': True,
    #             'dest': 'company_id'
                
    #         }),
    #         (['--tenant-name'], {
    #             'help': "Tenant you will to sync",
    #             'required': True,
    #             'dest': 'tenant_name'
                
    #         })]
    # )
    # def sync_company_contracts(self):
    #     autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
    #     autotask.contract.sync_company(self.app.pargs.tenant_name, self.app.pargs.company_id)

    @ex(
        help="Sync all contracts for all companies on an Autotask tenant",
        arguments=[
            (['--tenant-name'], {
                'help': "Tenant name",
                'required': True,
                'dest': 'tenant_name'
                
            })]
    )
    def sync_tenant_contracts(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        tenants = autotask.tenant.list()
        for tenant in tenants:
            autotask.contract.sync_tenant(tenant)
    
    @ex(
        help="Sync all company's contracts from all Autotask Tenants",
    )
    def sync_all_contracts(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        autotask.contract.sync_all()
    
    @ex(
        help="Pull ticket information by ticket number from an Autotask Tenant",
        arguments=[
            (['--ticket_number'], {
                'help': "ticket number of the ticket you wish to pull",
                'required': True,
                'dest': 'ticket_number'
                
            }),
            (['--tenant-name'], {
                'help': "Tenant name",
                'required': True,
                'dest': 'tenant_name'
                
            })]
    )
    def pull_ticket(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        autotask.ticket.pull_by_number(self.app.pargs.ticket_number, self.app.pargs.tenant_name)
    
    @ex(
        help="If the ticket is closed in the Autotask Tenant, delete reocrd in manifold's database",
    )
    def check_all_stagnant_ticket(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        autotask.ticket.check_all_stagnant()
