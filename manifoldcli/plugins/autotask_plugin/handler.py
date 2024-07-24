from cement import Handler
from .interface import *
from .models.database import *
from ...models.database import *
from ...models.devices import *
from ...models.companies import *
from pyautotask import atsite
from pyautotask.atsite import APIError
import datetime
import sys
import os

class AutotaskTenantHandler(AutotaskTenantInterface, Handler):
    class Meta:
        label = 'autotask_tenant_handler'

    def add(self, name, tenant_host):
        # Check if entry exsits first
        self.app.log.debug("[Autotask Plugin] Adding Autotask tenant to database")
        tenant = Autotask_Tenants(
            name = name,
            host = tenant_host,
            is_active = True
        )
        # TODO detect UNIQUE constraint and explain it to the user
        self.app.session.add(tenant)
        self.app.session.commit()

    def list(self):
        return self.app.session.query( Autotask_Tenants ).all()

    def delete(self):
        pass

    def disable(self):
        pass

    def enable(self):
        pass

    def auth(self, tenant, user, password):
        pass

    def tenant_api_object(self, tenant_db_object):
        name = tenant_db_object.name
        host = tenant_db_object.host
        username = None
        password = None
        interactioncode = None

        section = "autotask." + name
        if self.app.config.has_section(section):
            if self.app.config.get(section,'user') is not None:
                username = self.app.config.get(section,'user')
            else:
                self.app.log.error('[Autotask plugin] Variables "username" is missing! Please define varibles first.')
                sys.exit()

            if self.app.config.get(section,'password') is not None:
                password = self.app.config.get(section,'password')
            else:
                self.app.log.error('[Autotask plugin] variables "password" is missing! Please define varibles first.')
                sys.exit()
            if self.app.config.get(section,'interactioncode') is not None:
                interactioncode = self.app.config.get(section,'interactioncode')
            else:
                self.app.log.error('[Autotask plugin] variables "interactioncode" is missing! Please define varibles first. autotask refers to this as APIInteractionCode')
                sys.exit()
            return atsite.atSite(host=host, username=username, password=password, interactioncode=interactioncode)
        else:
            self.app.log.error('[Autotask plugin] variables are missing! Please define varibles first.')
            sys.exit()

class AutotaskCompanyHandler(AutotaskCompanyInterface, Handler):
    class Meta:
        label = 'autotask_company_handler'
    
    def sync_all(self):
        tenants = self.app.session.query(Autotask_Tenants).all()
        for tenant in tenants:
            # TODO Check last sync of tenant
            self.sync_tenant(tenant)
        
    def sync_tenant(self, tenant):
        self.app.log.info("[Autotask plugin] Syncing Autotask Companies for Tenant: " + tenant.name)

        # Update database
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        filter_fields = { 'op': 'and',
                            'items': [
                                {'op':'eq','field':'isActive','value': '1'},
                                {'op':'eq','field':'companyType','value': '1'}, # Customer
                            ]
                        }
        
        include_fields = [
            "companyName", "companyNumber"
        ]
        # FIXME Need to fix pyautotask to allow include_fields
        companies = at.get_companies(filter_fields=str(filter_fields))
        for company in companies:
            self.update_db(company, tenant)
        
        # Remove companies from database that are no longer in the tenant
        # TODO create a hook, that checks if any other plugin cares about the company before deleting.
        # TODO This only works because there is only 1 tenant in autotask. Need new logic to remove companies
        companies_db = self.app.session.query(Companies).all()
        for company_db in companies_db:
            on_tenant = False
            autotask_company = self.app.session.query(Autotask_Companies).filter_by(company_key=company_db.primary_key).all()
            if autotask_company:
                    on_tenant = True
            
            if on_tenant == False:
                self.app.log.warn("[Autotask plugin] Deleting company from DB: company not found in tenant. [company: " + company_db.name + "]")
                self.app.session.delete(company_db)
                self.app.session.commit()
        # TODO Add entry in last full sync last sync to database. Maybe we need to create a full sync function that syncs companies, devices and contracts, then doa  full sync for that

    def _create_company_object(self,company):
        company_obj = CompanyObject(
            name=company['companyName'],
            number=company['companyNumber']
        )
        return company_obj

    def update_unifi(self, company, autotask_company_db):
            # TODO probably turn this into a hook
            if self.app.config.get('unifi', 'sites2companies') == "autotask-udf":
                unifi = self.app.handler.get('unifi_interface', 'unifi_api', setup=True)
                site_ids = None
                udfs = company['userDefinedFields']
                for udf in udfs:
                    if udf['name'] == "Unifi Site ID": site_ids = udf['value']
                if site_ids:
                    unifi.site.link_sites_to_company_from_autotask(site_ids=site_ids, company_key=autotask_company_db.parent.primary_key)

    def update_db(self, company, tenant):
        company_obj = self._create_company_object(company)
        db_companies = self.app.handler.get('db_interface', 'db_companies', setup=True)
        existing_entry = self.app.session.query(Autotask_Companies).filter_by(autotask_company_id=company['id'], autotask_tenant_key=tenant.primary_key).first()
        if existing_entry:
            db_companies.update(company_obj, existing_entry.parent, "Autotask")
            self.update_unifi(company, autotask_company_db=existing_entry)
        else:
            company_db = None
            autotask_company_db = None
            existing_companies = self.app.session.query( Companies ).filter_by( name=company['companyName'] ).all()
            for existing_company in existing_companies:
                autotask_company_db = self.app.session.query(Autotask_Companies).filter_by( company_key=existing_company.primary_key ).first()
                company_db=existing_company

            if company_db is None:
                company_db = db_companies.add(company_obj, "Autotask")

            if not autotask_company_db:
                autotask_company_db = Autotask_Companies(
                    autotask_company_id = company['id'],
                    autotask_tenant_key = tenant.primary_key,
                    parent = company_db
                )

            self.app.log.debug("[Autotask plugin] Adding company to DB:  [Company: " + company['companyName'] + " | Company ID: " + str(company['id']) + "]")
            self.app.session.add(autotask_company_db)
            self.app.session.commit()

            # FIXME Might trigger a hook
            self.update_unifi(company, autotask_company_db=autotask_company_db)

    def _contracts_entity_fields_need_refresh(self, tenant):
        return_value = True
        # return_value = None
        # last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=Autotask_Contracts_Type.__tablename__, tenant_key = tenant.primary_key).first()
        # if rmm_manufacturer_last_sync.last_sync < (rmm_manufacturer_last_sync.last_sync - datetime.timedelta(hours=24)):
        #     return True
        # else:
        #     return_value = False
        # rmm_model_last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=Autotask_RMM_Model.__tablename__, tenant_key = tenant.primary_key).first()        
        # if rmm_model_last_sync.last_sync < (rmm_model_last_sync.last_sync - datetime.timedelta(hours=24)):
        #     return True
        # else:
        #     return_value = False
        return return_value

    def post(self, company_db, tenant):
        """
        Verify company is up to date on the tenant side.

        Args:
            company (company_obj): all information for the company.
            tenant (tenant_obj): all information for the tenant.
        """
        pass

    def hooks(self, company, tenant, source):
        pass

class AutotaskDeviceHandler(AutotaskDeviceInterface, Handler):
    class Meta:
        label = 'autotask_device_handler'

    def _pull_devices(self, at_db_company):
        self.app.log.debug("[Autotask plugin] Pulling devices from Autotask and adding them to the database")
        tenant = self.app.session.query(Autotask_Tenants).filter_by(primary_key=at_db_company.autotask_tenant_key).first()
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        filter_fields = { 'op': 'and',
                            'items': [
                                {'op':'eq','field':'isActive','value': '1'},
                                {'op':'eq','field':'companyID','value': str(at_db_company.autotask_company_id)},
                            ]
                        }
        
        include_fields = [
            "id", 
            "companyID", "installDate", "isActive", "referenceTitle", "serialNumber", "createDate", 
            "dattoSerialNumber", "dattoHostname",  "dattoInternalIP", 
            "rmmDeviceAuditMacAddress",'rmmDeviceAuditModelID', 'rmmDeviceAuditManufacturerID', 'rmmDeviceAuditDescription'
            "userDefinedFields",
        ]
    
        at_devices = at.get_cis(filter_fields=str(filter_fields))
        for device in at_devices:
            device_obj = self._create_device_object(device, tenant.name)
            self.update_db(device_obj, at_db_company.autotask_company_id, tenant.name)
            # TODO Maybe run through alerts for autotask. Checked in date after X days. Maybe others
            # autotask_api = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
            # unifi_api.alert.device_alerts(device)
        return at_devices

    def _remove_old_db(self, at_db_company, at_devices):
        self.app.log.debug("[Autotask plugin] removing devices from autotask datebase if they are not in Autotask anymore")
        # Remove devices in the Autotask Devices table if it's not in the Autotask Company
        at_db_devices = self.app.session.query(Autotask_Devices).filter_by(autotask_company_key=at_db_company.company_key).all()
        for at_db_device in at_db_devices:
            exist_on_at = False
            for at_device in at_devices:
                if at_device['id'] == at_db_device.autotask_device_id:
                    exist_on_at = True
            if exist_on_at == False:
                # TODO, Need to send this to a hook so we can check if this device is legit for another source
                db_devices = self.app.handler.get('db_interface', 'db_devices', setup=True)

                db_devices.delete( at_db_device.parent, "Autotask")
                self.app.session.delete( at_db_device )
                self.app.session.commit()

    def get_product_id(self, tenant_name, manufacturer, model):
        tenant = self.app.session.query(Autotask_Tenants).filter_by(name=tenant_name).first()
        self._get_products(tenant)
        product = self.app.session.query(Autotask_Products).filter_by(manufacturer=manufacturer, sku=model ).first()
        if product:
            return product.autotask_id
        else:
            return None

    def update_autotask(self,db_device, at_device, tenant):
        # TODO, Need to change the line before to a look up of all Autotask sources
        if db_device.source != 3:
            changed = False
            #self.app.log.debug("[Autotask plugin] Device exist in Autotask")
            at = AutotaskTenantHandler.tenant_api_object(self, tenant)
            filter_fields = {
                'op': 'eq',
                'field': 'id',
                'value': at_device.autotask_device_id
            }
            at_ci = at.get_cis(filter_fields=str(filter_fields))[0]
            params = {
                'id': str(at_ci['id'])
            }
            if at_ci['referenceTitle'] != db_device.name:
                params['referenceTitle'] = db_device.name
                changed = True
            #TODO add description
            if at_ci['serialNumber'] != db_device.serial:
                params['serialNumber'] = db_device.serial
                changed = True


            # date = at_ci['installDate'].split('T')[0]
            # date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")

            # if date_obj > db_device.install_date:
            #     params['installDate'] = db_device.install_date
            #     changed = True
            
            # product_id = self.get_product_id(tenant.name, db_device.manufacturer, db_device.model)
            # if at_ci['productID'] != product_id:
            #     params['productID'] = product_id
            #     changed = True
            #     print(product_id)
            #     print(at_ci['productID'])
            #     sys.exit()

            if changed:
                #print(params)
                #sys.exit()
                self.app.log.debug("[Autotask plugin] updaing Device - Autotask: " +  at_ci['referenceTitle'] + " Params:" + str(params))
                at.ci_push(params)

    def _push_devices(self, at_db_company):
        self.app.log.debug("[Autotask plugin] Finding other devices assoicated with the Autotask company and adding them to Autotask")
        tenant = self.app.session.query(Autotask_Tenants).filter_by(primary_key=at_db_company.autotask_tenant_key).first()
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        db_devices = self.app.session.query( Devices ).filter_by( company_key=at_db_company.company_key ).all()

        #self._product_entity_fields(tenant_name)
        for db_device in db_devices:
            #self.app.log.debug("[Autotask plugin] Device - " + str(db_device))
            at_device = self.app.session.query( Autotask_Devices ).filter_by( autotask_company_key=at_db_company.company_key, device_key=db_device.primary_key ).first()

            #self.app.log.debug("[Autotask plugin] AT Device - " + str(at_device))
            if at_device:
                self.update_autotask(db_device,at_device,tenant)
            else:
                self.post(db_device, at_db_company, tenant)

    def _get_products(self, tenant):
        #self.app.log.debug("[Autotask plugin] get tenant - " + tenant_name)
        #tenant = self.app.session.query(Autotask_Tenants).filter_by(name=tenant_name).first()
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)

        products_last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=Autotask_Products.__tablename__, tenant_key = tenant.primary_key).first()
        sync = False
        if products_last_sync:
            if products_last_sync.last_sync < (products_last_sync.last_sync - datetime.timedelta(hours=24)):
                sync = True    
        else:
            sync = True

        if sync:
            self.app.log.debug("[Autotask plugin] Clearing Products cashe data")
            products = self.app.session.query( Autotask_Products ).filter_by(tenant_key=tenant.primary_key).all()
            if products:
                self.app.session.delete(products)
                self.app.session.commit()

            self.app.log.debug("[Autotask plugin] Grabing cache for products")
            for product in at.get_products():
                db_obj = Autotask_Products(
                    autotask_id = product['id'],
                    manufacturer = product['manufacturerName'],
                    manufacturerProductName = product['manufacturerProductName'],
                    name = product['name'],
                    sku = product['sku'],
                    tenant_key = tenant.primary_key
                )
                self.app.session.add(db_obj)
                self.app.session.commit()
            cache_db = Autotask_Cache_Last_Sync(
                name = Autotask_Products.__tablename__,
                tenant_key = tenant.primary_key,
                last_sync = datetime.datetime.now()
            )
            self.app.session.add(cache_db)
            self.app.session.commit()

    def _ci_entity_fields_need_refresh(self, tenant):
        return_value = None
        rmm_manufacturer_last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=Autotask_RMM_Manufacturer.__tablename__, tenant_key = tenant.primary_key).first()
        
        if rmm_manufacturer_last_sync:
            if rmm_manufacturer_last_sync.last_sync < (rmm_manufacturer_last_sync.last_sync - datetime.timedelta(hours=24)):
                return True
            else:
                return_value = False
        else:
            return True
        
        rmm_model_last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=Autotask_RMM_Model.__tablename__, tenant_key = tenant.primary_key).first()        
        if rmm_model_last_sync:
            if rmm_model_last_sync.last_sync < (rmm_model_last_sync.last_sync - datetime.timedelta(hours=24)):
                return True
            else:
                return_value = False
            return return_value
        else:
            return True

    def _get_ci_entity_fields(self, tenant_name):
        tenant = self.app.session.query(Autotask_Tenants).filter_by(name=tenant_name).first()
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        # rmm_manufacturer = self.app.session.query( Autotask_RMM_Manufacturer ).filter_by(tenant_key=tenant.primary_key).all()
        # rmm_model = self.app.session.query( Autotask_RMM_Model ).filter_by(tenant_key=tenant.primary_key).all()

        if self._ci_entity_fields_need_refresh(tenant):
            self.app.log.debug("[Autotask plugin] Clearing CI Entries cashe data")
            rmm_manufacturer = self.app.session.query( Autotask_RMM_Manufacturer ).filter_by(tenant_key=tenant.primary_key).all()
            if rmm_manufacturer:
                self.app.session.delete(rmm_manufacturer)
            rmm_model = self.app.session.query( Autotask_RMM_Model ).filter_by(tenant_key=tenant.primary_key).all()
            if rmm_model:
                self.app.session.delete(rmm_model)
            self.app.session.commit()

            self.app.log.debug("[Autotask plugin] Grabing cache for rmm manufacturers and models")
            for entity in at._api_read("ConfigurationItems/entityInformation/fields")['fields']:
                if entity['isPickList'] == True:
                    if entity['name'] == 'rmmDeviceAuditManufacturerID':
                        for value in entity['picklistValues']:
                            db_obj = Autotask_RMM_Manufacturer(
                                value = value['value'],
                                label = value['label'],
                                tenant_key = tenant.primary_key
                        )
                            self.app.session.add(db_obj)
                            self.app.session.commit()
                        cache_db = Autotask_Cache_Last_Sync(
                            name = Autotask_RMM_Manufacturer.__tablename__,
                            tenant_key = tenant.primary_key,
                            last_sync = datetime.datetime.now()
                        )
                        self.app.session.add(cache_db)
                        self.app.session.commit()
                        
                    if entity['name'] == 'rmmDeviceAuditModelID':
                        for value in entity['picklistValues']:
                            db_obj = Autotask_RMM_Model(
                                value = value['value'],
                                label = value['label'],
                                tenant_key = tenant.primary_key
                        )
                            self.app.session.add(db_obj)
                            self.app.session.commit()
                        cache_db = Autotask_Cache_Last_Sync(
                            name = Autotask_RMM_Model.__tablename__,
                            tenant_key = tenant.primary_key,
                            last_sync = datetime.datetime.now()
                        )
                        self.app.session.add(cache_db)
                        self.app.session.commit()

    def _create_device_object(self, device, tenant_name):
        # device: unifi device
        tenant = self.app.session.query(Autotask_Tenants).filter_by(name=tenant_name).first()
        source = self.app.session.query(Sources).filter_by(plugin_name="Autotask", tenant_key=tenant.primary_key).first()
        mac_list_obj = MacAddressListObject(results=[])
        #self.app.log.debug("[Autotask plugin] " + str(device))
        #self.app.log.debug("[Autotask plugin] Creating device object")

        if device['userDefinedFields']:
            for udf in device['userDefinedFields']:
                #if udf['name'] == 'MAC Addreses' and udf['value'] != None:
                if isinstance(udf, dict) and 'name' in udf and 'value' in udf and udf['name'] == 'MAC Addresses' and udf['value'] is not None:
                    print("UDF Mac Address: " + udf['value'])
                    sys.exit()

        # TODO copy mac logic for ip_addresses
        if device['rmmDeviceAuditMacAddress']:
            for mac in device['rmmDeviceAuditMacAddress'].split(","):
                if len(mac) >= 17:
                    mac_obj = MacAddressObject(
                        mac_address=mac
                    )
                    mac_list_obj.add_result(mac_obj)
        device_obj = DeviceObject(
            mac_address=mac_list_obj,
            source=source.primary_key
        )
        if device['referenceTitle']:
            device_obj.name=device['referenceTitle']
        elif device['dattoHostname']:
            device_obj.name=device['dattoHostname']

        # TODO figure out how to get a manufacturer and model
        #manufacturer="Ubiquiti"
        # model=device['model'],
        if device['serialNumber']:
            device_obj.serial=device['serialNumber']
        elif device['dattoSerialNumber']:
            device_obj.serial=device['dattoSerialNumber']

        if device['installDate']:
            date = device['installDate'].split('T')[0]
            device_obj.install_date = datetime.datetime.strptime(date, "%Y-%m-%d")

        if device['createDate']:
            date = device['createDate'].split('T')[0]
            createDate = datetime.datetime.strptime(date, "%Y-%m-%d")
            if createDate < device_obj.install_date:
                device_obj.install_date = createDate

        self._get_ci_entity_fields(tenant_name)
        self._get_products(tenant)
        if device['rmmDeviceAuditManufacturerID'] != None:
            rmm_manufacturer = self.app.session.query( Autotask_RMM_Manufacturer ).filter_by(value=device['rmmDeviceAuditManufacturerID'] ,tenant_key=tenant.primary_key).first()
            if rmm_manufacturer:
                device_obj.manufacturer = rmm_manufacturer.label
        
        if device['rmmDeviceAuditModelID'] != None:
            rmm_model = self.app.session.query( Autotask_RMM_Model ).filter_by(value=device['rmmDeviceAuditModelID'] ,tenant_key=tenant.primary_key).first()
            if rmm_model:
                device_obj.model = rmm_model.label

        #if device_obj.manufacturer != None:



        if device_obj.name or device_obj.serial:
            return device_obj
        else:
            return None

    def update_db(self, device_obj, company_id, tenant_name):
        """
        Verify a device is in the DB and is up to date.

        Args:
            device (device_obj): all information for the deivce.
            company (company_obj): all information for the company.
            teanant (tenant_obj): all information for the tenant.
        """
        #self.app.log.debug("[Autotask plugin] Adding Autotask Device")
        db_devices = self.app.handler.get('db_interface', 'db_devices', setup=True)

        if device_obj:
            tenant_db = self.app.session.query( Autotask_Tenants ).filter_by( name=tenant_name ).first()
            company_db = self.app.session.query( Autotask_Companies ).filter_by(autotask_company_id=company_id, autotask_tenant_key=tenant_db.primary_key   ).first()

            if company_db.primary_key:
                #self.app.log.debug("[Autotask plugin] Device Object" + str(device_obj))
                device_obj.company = company_db.primary_key

            existing_device = self.app.session.query( Devices ).filter_by( serial=device_obj.serial, company_key=company_db.primary_key ).first()
            device_db = None
            if existing_device:
                device_db = existing_device
            else:
                device_db = db_devices.add(device_obj, "Autotask")

            existing_autotask = self.app.session.query( Autotask_Devices ).filter_by(device_key=device_db.primary_key).first()
            if existing_autotask:
                db_devices.update(device_obj, existing_autotask.parent, "Autotask")
            else:
                if device_db.serial:
                    at = AutotaskTenantHandler.tenant_api_object(self, tenant_db)
                    filter_fields = None
                    company_filter = at.create_filter('eq', 'companyID', company_id)

                    serial_filter = at.create_filter('eq', 'serialNumber', device_db.serial)
                    filter_fields = company_filter + "," + serial_filter

                    at_ci = at.get_cis(filter_fields=str(filter_fields))[0]
                    
                    autotask_device_db = Autotask_Devices(
                        autotask_device_id = at_ci['id'],
                        parent = device_db,
                        autotask_company_key = company_db.primary_key,
                        device_key = device_db.primary_key,
                    )
                    if at_ci['userDefinedFields']:
                        for udf in at_ci['userDefinedFields']:
                            if udf['name'] == 'UniFi Alerts Ignore List' and udf['value'] != None:
                                #ignore_alert = at_ci['userDefinedFields']['UniFi Alerts Ignore List']
                                sys.exit(at_ci)

                    self.app.log.debug("[Autotask plugin] Linking device to autotask_device. [Device: " + str(at_ci['id']) + "]")
                    self.app.session.add(autotask_device_db)
                    self.app.session.commit()
                # TODO create an else that looks for other things to match. Maybe Mac Address
        # TODO remove all devices not still connected to a Autotask Company
        
    def post(self, device, company, tenant):
        """
        Verify device is up to date on the tenant side.

        Args:
            device (device_obj): all information for the device.
            company (company_obj): all information for the company.
            tenant (tenant_obj): all information for the tenant.
        """
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        
        self.app.log.debug("[Autotask plugin] Device is not in Autotask. " + str(device))
        self._get_products(tenant)
        # TODO Need somethign better than using the name
        # TODO Need something that checks the source. If UniFi then we can assume it's a UniFi Generic Product, otherwaise we have to figure something else out.
        product = self.app.session.query( Autotask_Products ).filter_by(tenant_key=tenant.primary_key, manufacturer="Ubiquiti", name="UniFi Generic Product").first()
        # TODO if UniFi
        configurationItemCategoryID = 110
        configurationItemType = 11

        at_company = self.app.session.query( Autotask_Companies ).filter_by(autotask_tenant_key=tenant.primary_key, company_key=company.primary_key).first()

        if device.install_date:
            install_date = device.install_date.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        else:
            install_date = None
        params = {
            'configurationItemCategoryID': configurationItemCategoryID,
            'configurationItemType': configurationItemType,
            'companyID': at_company.autotask_company_id,
            'isActive': True,
            'installDate': install_date,
            'productID': product.autotask_id,
            'referenceTitle': device.name,
            'serialNumber': device.serial,
            'userDefinedFields':[]
            
        }
        # TODO grab return, which should have the id. Add device to the autotask device table
        ci_return = None
        try:
            ci_return = at.ci_push(params)
        except APIError as e:
            self.app.log.error(f"[Autotask plugin] caught: {e}")
        if ci_return:
            self.app.log.debug("[Autotask plugin] CI Push returned: " + str(ci_return))
            ci = at.get_ci_by_id(str(ci_return['itemId']))
            self.app.log.debug("[Autotask plugin] full CI: " + str(ci))
            device_obj = self._create_device_object(ci[0], tenant.name)
            self.app.log.info("[Autotask plugin] Need to add device to Autotask Devices")
            self.update_db(device_obj, at_company.autotask_company_id, tenant.name)
        else:
            self.app.log.error("[Autotask plugin] could not push device to Autotask")
            self.app.log.error("[Autotask plugin] " + str(device))

    def sync_company(self, tenant_name, company_id):
        tenant = self.app.session.query(Autotask_Tenants).filter_by(name=tenant_name).first()
        at_db_company = self.app.session.query( Autotask_Companies ).filter_by(autotask_company_id=company_id).first()
        self.app.log.debug("[Autotask plugin] Syncing Devices for " + at_db_company.parent.name)

        # TODO Check for duplicate CI's with the same serial numbers

        # Pull Devices from Autotask and sync with local database
        at_devices = self._pull_devices(at_db_company)
        
        # Checking for a vaild source
        none_devices = 0
        for at_device in at_devices:
            if not at_device['rmmDeviceID']:
                if at_device['referenceTitle'] == None:
                     none_devices += 1
                # else:
                #     sys.exit(at_device)
        if none_devices > 1:
            self.app.log.error("[Autotask plugin] " + at_db_company.parent.name + " has too many 'None' devices")

        # sys.exit()

        # Check if there are devices assoicated with the company that are not in Autotask
        self._push_devices(at_db_company)

        # TODO 
        # Check if there are devices in the database that are no longer on Autotask
        #self._remove_old_db(at_db_company, at_devices)

    def sync_tenant(self, tenant_db):
        companies_db = self.app.session.query(Autotask_Companies).filter_by(autotask_tenant_key=tenant_db.primary_key).all()

        for company in companies_db:
            self.app.log.info("[Autotask plugin] Syncing devices for " + company.parent.name)
            self.sync_company(tenant_db.name, company.autotask_company_id)

    def sync_all(self):
        self.app.log.debug("[Autotask plugin] Syning all devices for all tenants")
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        tenants = autotask.tenant.list()
        for tenant in tenants:
            self.sync_tenant(tenant)

class AutotaskTicketHandler(AutotaskTicketInterface, Handler):
    class Meta:
        label = 'autotask_ticket_handler'

    def sync_issuetypes(self, at, tenant):
        ticket_fields = at._api_read("Tickets/entityInformation/fields")
        for ticket_field in ticket_fields['fields']:
            if ticket_field['name'] == "issueType":
                issueTypes = ticket_field['picklistValues']
            if ticket_field['name'] == "subIssueType":
                subIssueTypes = ticket_field['picklistValues']
        
        self.app.log.debug("[Autotask plugin] deleting data in Autotask_Issues")
        self.app.session.query(Autotask_Issues).delete()
        self.app.session.commit()
        for issueType in issueTypes:
            issueType_db = Autotask_Issues(
                value = issueType['value'],
                label = issueType['label'],
                isActive = issueType['isActive'],
                tenant_key = tenant.primary_key
            )
            self.app.session.add(issueType_db)
            self.app.session.commit()

        self.app.log.debug("[Autotask plugin] deleting data in Autotask_Subissues")
        self.app.session.query(Autotask_Subissues).delete()
        self.app.session.commit()
        for item in subIssueTypes:
            item_db = Autotask_Subissues(
                value = item['value'],
                label = item['label'],
                isActive = item['isActive'],
                tenant_key = tenant.primary_key,
                parent_value = item['parentValue'],
            )
            self.app.session.add(item_db)
            self.app.session.commit()
        
        self.app.log.debug("[Autotask plugin] Deleting Autotask_Cache_Last_Sync entry if any")
        self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name="_autotask_issues").delete()
        self.app.session.commit()
        last_sync = Autotask_Cache_Last_Sync(
                name = "_autotask_issues",
                tenant_key = tenant.primary_key,
                last_sync = datetime.datetime.utcnow()
        )
        self.app.session.add(last_sync)
        self.app.session.commit()

    def verify_ci_exist(self, alert, company_db, tenant):
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        devices_db = alert.devices
        other_cis = []
        for device_db in devices_db:
            # TODO should do a search based on serial and company
            device_at = at.get_ci_by_serial(device_db.serial)
            if device_at == []:
                self.app.log.warning("[Autotask plugin] Device does not exist in Autotask. Need to add it.")
                autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
                autotask.device.post(device_db, company_db, tenant)

    def check_issuetypes(self, at, tenant):
        last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name="_autotask_issues").first().last_sync
        self.app.log.debug("[Autotask plugin] Checking last sync of issues")
        if last_sync:
            self.app.log.debug("[Autotask plugin] last_sync has a value")
            if last_sync < datetime.datetime.now() - datetime.timedelta(days=7):
                self.app.log.debug("[Autotask plugin] issue types last_sync is old. Syncing now")
                self.sync_issuetypes(at, tenant)
        else:
            self.app.log.debug("[Autotask plugin] issue types last_sync does not have a value. Syncing now")
            self.sync_issuetypes(at, tenant)

    def add_ticket_db(self, alert, ticket_id, tenant):
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        autotask_ticket = at.get_ticket_by_id(ticket_id['itemId'])[0]
        # TODO add Ticket ID to database

        db = Autotask_Tickets(
            ticket_number = autotask_ticket['ticketNumber'],
            autotask_tenant_key = tenant.primary_key,
            alert_key = alert.primary_key
        )
        self.app.session.add(db)
        self.app.session.commit()

    def create(self, alert):
        # TOD Add worktype
        ticketCategory = None
        # TODO Add site ID and url to discription
        self.app.log.debug("[Autotask plugin] Creating Ticket from alert")
        company_db = self.app.session.query(Companies).filter_by(primary_key=alert.company_key).first()
        at_company = self.app.session.query(Autotask_Companies).filter_by(company_key=alert.company_key).first()
        tenant = self.app.session.query(Autotask_Tenants).filter_by(primary_key=at_company.autotask_tenant_key).first()
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)

        self.verify_ci_exist(alert, company_db, tenant)

        self.check_issuetypes(at, tenant)
        # TODO if Unifi
        if alert.alert_type.name == "No Contract":
            # TODO Need to make this configuratable
            issue_db = self.app.session.query(Autotask_Issues).filter_by(label="Pre-Sale").first()
            subissue_db = self.app.session.query(Autotask_Subissues).filter_by(label="Upsell").first()
            ticketCategory = "107" # TODO: Set to 'Pre-Sales' , but we need to detect the source and set that
        else:
            issue_db = self.app.session.query(Autotask_Issues).filter_by(label="Network").first()
            subissue_db = self.app.session.query(Autotask_Subissues).filter_by(label=alert.alert_type.name, parent_value=issue_db.value).first()
            ticketCategory = "106" # TODO: Set to 'UniFi Alerts' , but we need to detect the source and set that
        if subissue_db == None:
            self.sync_issuetypes(at, tenant)
            if alert.alert_type.name == "No Contract":
                subissue_db = self.app.session.query(Autotask_Subissues).filter_by(label="Upsell").first()
            else:
                subissue_db = self.app.session.query(Autotask_Subissues)\
                    .filter(Autotask_Subissues.label.ilike(alert.alert_type.name))\
                    .filter(Autotask_Subissues.parent_value == issue_db.value).first()
            if subissue_db == None:
                self.app.log.error("[Autotask plugin] TODO: Subissue doesn't exsit. Need to create it. Subissue Type: " + alert.alert_type.name)
        not_complete_filter = at.create_filter("noteq", "status", "5") # Not Complete
        subissue_filter = at.create_filter("eq", "subIssueType", str(subissue_db.value))
        company_filter = at.create_filter("eq", "companyID", at_company.autotask_company_id)
        base_filter_fields = not_complete_filter + "," + subissue_filter + "," + company_filter

        if alert.alert_type.name == "Lost Contact":

            # First check ticket in the database. If there is a ticket, verify it's still opened. If not, delete ticket from db and open a new ticket.
            filter_fields = base_filter_fields + "," + company_filter
            tickets_subissue = at.create_query("tickets", filter_fields)
            if tickets_subissue:
                self.app.log.error("[Autotask] TODO: found tickets with the subissue. Need a process that adds this ticket to that one.")
#                for ticket in tickets_subissue:
#                    pass
        if len(alert.devices) == 0:
            self.app.log.info("[Autotask plugin] TODO: No devices. Need to pick None")
            sys.exit()
        else:
            device_db = self.app.session.query(Autotask_Devices).filter_by(device_key=alert.devices[0].primary_key).first()
            if device_db is None:
                self.app.log.debug("[Autotask plugin] Device is not in the Autotask Device DB. Adding it now")
                db_devices = self.app.handler.get('db_interface', 'db_devices', setup=True)
                device = db_devices.create_object(alert.devices[0])

                autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
                autotask.device.update_db(device, at_company.autotask_company_id, tenant.name)
                device_db = self.app.session.query(Autotask_Devices).filter_by(device_key=alert.devices[0].primary_key).first()

            ci_filter = at.create_filter("eq", "configurationItemID", device_db.autotask_device_id)
            filter_fields = base_filter_fields + "," + ci_filter

            ticket = at.create_query("tickets", filter_fields)

            # Check ignore list
            
            ignore = False
            if device_db.ignore_alert:
                for c in device_db.ignore_alert:
                    if device_db == subissue_db.value:
                        ignore = True

            if not ticket and not ignore:
                # TODO Check if there is a ticket for the other devices on this alert. 
                # If not, add the other devices to this ticket. 
                # If there is, update ticket with these devices and add a note

                self.app.log.info("[Autotask plugin] Creating ticket")
                # TODO need to detect the source
                
                # TODO, should be a better way to do this!
                # If the alert plugin wanted something added to the title of the ticket, do it now. 
                if alert.title_append:
                    ticket_title = "Unifi Alert: " + alert.alert_type.name + " " + alert.title_append
                else:
                    ticket_title = "Unifi Alert: " + alert.alert_type.name
                # TODO need to detect the source and add addication information from the orginal source.
                # TODO Created a "Extra infromation in the alert obj. Need to add that to the database to be sent with Description"
                description = "The UniFi Controller identified an issue.\n"
                if alert.useful_information:
                    description = description + alert.useful_information
                due_date = datetime.datetime.utcnow()
                due_date += datetime.timedelta(hours = 2)
                # TODO worktype set to Maintance
                params = {
                    'title': ticket_title,
                    'description': description,
                    'companyID': at_company.autotask_company_id,
                    'configurationItemID': device_db.autotask_device_id,
                    # 'createDate': date,
                    'dueDateTime': due_date,
                    'issueType': issue_db.value,
                    'subIssueType': subissue_db.value,
                    'source': "8", # TODO: Set to 'Monitoring Alerts', but we need to detect this
                    'status': "1", # TODO Set to 'New', but we need to detect this
                    'ticketCategory': ticketCategory, 
                    'ticketType': "5",  # TODO: Setup to'Alerts' but we need to detect that
                }
                
                if alert.alert_type.name == "Site Down":  # If urgent, go to Helpdesk
                    params['priority'] = "0" # TODO: Set to 'Critical', but we need to detect this.
                    params['queueID'] = "29683481" # TODO Set to 'Helpdesk', but we need to detect this
                elif alert.alert_type.name == "No Contract":
                    params['priority'] = "2" # TODO: Set to 'Critical', but we need to detect this.
                    params['queueID'] = "29683480" # TODO Set to 'Pre-Sales', but we need to detect this
                else: # if not, go to Maintance
                    params['priority'] = "1", # TODO: Set to 'High', but we need to detect this.
                    params['queueID'] = "29683486", # TODO Set to 'Maintance', but we need to detect this

                ticket_id =  at._api_write("Tickets", params)
                self.app.log.debug("[Autotask plugin] create ticket function returned: " + str(ticket_id))
                self.add_ticket_db(alert, ticket_id, tenant)
            else:
                self.app.log.error("[Autotask] Ticket is already assoicated with a ticket in Autotask. Need a process to fix this.")

    def update(self, ticket_db, note=None, status=None):
        #tenant = 
        #at = AutotaskTenantHandler.tenant_api_object(self, tenant)

        if note:
            params = {
                #"createDateTime": "2024-05-08T16:08:53.556Z",
                #"createdByContactID": 0,
                #"creatorResourceID": 0,
                "description": note,
                "noteType": 0, # TODO need to look up Note Types
                "publish": 0, # TODO need to look up value publish. I bet 1 = True
                "ticketID": 0, # TODO Grab Ticket ID from alert_db
                "title": "Some devices have cleared this alert",
            }

            # note_return = at._api_update("TicketsNotes", params)

        if status == "Complete":
            params = {
                'id': 0,# TODO Grab Ticket ID from alert_db
                'status': "5", # Complete TODO use a varible that is looked up for "Complete".
            }
            #ticket_return = at._api_update("Tickets", params)

    def _close_ticket(self, ticket_db, ticket_at):
        tenant = self.app.session.query( Autotask_Tenants ).filter_by( primary_key=ticket_db.autotask_tenant_key ).first()
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        params = {
            "description": "The Unifi alert that created this ticket cleared.",
            "noteType": 1, # TODO need to look up Note Types
            "publish": 1, # TODO need to look up value publish. I bet 1 = True
            "ticketID": ticket_at['id'], 
            "title": "Alert Cleared",
        }
        note_return = at._api_write("Tickets/" + str(ticket_at['id']) + "/Notes", params)

        filter_fields = {
            'op':'eq',
            'field':'ticketID',
            'value': ticket_at['id']
        }
        ticket_times = at.create_query("TimeEntries", str(filter_fields))
        if ticket_times is None:
            params = {
                'id': ticket_at['id'],
                'status': "5",
            }
            at._api_update("Tickets", params)

    def close_ticket(self, alert_db):
        ticket_db = self.app.session.query( Autotask_Tickets ).filter_by( alert_key=alert_db.primary_key ).first()
        if ticket_db:
            self.app.log.debug("[Autotask plugin] Closing Ticket: " + ticket_db.ticket_number)
            source_db = self.app.session.query( Sources ).filter_by( primary_key=alert_db.source_key ).first()
            tenant = self.app.session.query( Autotask_Tenants ).filter_by( primary_key=source_db.tenant_key ).first()
            if not tenant:
                self.app.log.error("[Autotask plugin] Didn't find the tenant!")
                self.app.log.error("[Autotask plugin] alert: " + str(alert_db.primary_key))
                self.app.log.error("[Autotask plugin] ticket: " + str(ticket_db))
                sys.exit()
            at = AutotaskTenantHandler.tenant_api_object(self, tenant)

            try: 
                ticket_at = at.get_ticket_by_number(ticket_db.ticket_number)[0]
            except IndexError as e:
                self.app.log.error("[Autotask plugin] Ticket is not found in Autotask. Deleting from database")
                self.app.session.delete(ticket_db)
                self.app.session.commit()
                ticket_at = None

            if ticket_at:
                # TODO Change 5 to a ticket status closed comparison. 5 should not need to be hardcoded here
                if ticket_at['status'] != 5:
                    params = {
                        #"createDateTime": "2024-05-08T16:08:53.556Z",
                        #"createdByContactID": 0,
                        #"creatorResourceID": 0,
                        "description": "The Unifi alert that created this ticket cleared.",
                        "noteType": 1, # TODO need to look up Note Types
                        "publish": 1, # TODO need to look up value publish. I bet 1 = True
                        "ticketID": ticket_at['id'], 
                        "title": "Alert Cleared",
                    }
                    note_return = at._api_write("Tickets/" + str(ticket_at['id']) + "/Notes", params)

                    filter_fields = {
                        'op':'eq',
                        'field':'ticketID',
                        'value': ticket_at['id']
                    }
                    ticket_times = at.create_query("TimeEntries", str(filter_fields))
                    if ticket_times is None:
                        params = {
                            'id': ticket_at['id'],
                            'status': "5",
                        }
                        at._api_update("Tickets", params)

                else:
                    self.app.log.debug("[Autotask plugin] Deleting " + str(ticket_db.ticket_number) + " from database")
                    self.app.session.delete(ticket_db)
                    self.app.session.commit()
        else:
            self.app.log.error("[Autotask plugin] Something is triggering a close ticket on a ticket that is not in our DB.")

    def clean_db_of_ticket(self,ticket_db):
        alert_db = self.app.session.query( Alerts ).filter_by( primary_key=ticket_db.alert_key ).first()
        self.app.session.delete(ticket_db)
        if alert_db:
            associated_devices = self.app.session.query(device_alert_association).filter_by(alert_key=alert_db.primary_key).delete(synchronize_session='fetch')
            self.app.session.delete(alert_db)
        self.app.session.commit()

    def check_stagnant(self, tenant):
        # TODO we should only do this once a day, so we need to add a time check
        self.app.log.info("[Autotask plugin] Clecking for stagnant tickets on " + tenant.name)
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)
        tickets_db = self.app.session.query( Autotask_Tickets ).filter_by( autotask_tenant_key=tenant.primary_key ).all()
        for ticket_db in tickets_db:
            try: 
                ticket_at = at.get_ticket_by_number(ticket_db.ticket_number)[0]
            except IndexError as e:
                self.app.log.info("[Autotask plugin] Ticket is not found in Autotask. Deleting from database")
                self.clean_db_of_ticket(ticket_db)
                ticket_at = None

            # TODO, we should use a status here instead of "5"
            if ticket_at:
                if ticket_at['status'] == 5:
                    self.app.log.info("[Autotask plugin] Ticket number " + ticket_db.ticket_number + " is closed, cleaning up database")
                    self.clean_db_of_ticket(ticket_db)
                else:
                    # Check if the alert assoicated with the ticket is still active.
                    alert_db = self.app.session.query( Alerts ).filter_by( primary_key = ticket_db.alert_key ).first()
                    if not alert_db:
                        self._close_ticket(ticket_db, ticket_at)
                        self.clean_db_of_ticket(ticket_db)

    def check_all_stagnant(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        tenants = autotask.tenant.list()
        for tenant in tenants:
            self.check_stagnant(tenant)

    def pull_by_number(self, ticket_number, tenant_name):
        tenant = self.app.session.query(Autotask_Tenants).filter_by(name=tenant_name).first()
        at = AutotaskTenantHandler.tenant_api_object(self, tenant)

        ticket_at = at.get_ticket_by_number(ticket_number)[0]
        self.app.log.info("[Autotask plugin] Ticket information: " + str(ticket_at))

        # filter_fields = {
        #     'op':'eq',
        #     'field':'ticketID',
        #     'value': ticket_at['id']
        # }
        # ticket_notes = at.create_query("TicketNotes", str(filter_fields))
        # for note in ticket_notes:
        #     self.app.log.info("[Autotask plugin] Ticket Note: " + str(note ))
        # ticket_times = at.create_query("TimeEntries", str(filter_fields))
        # for time in ticket_times:
        #     self.app.log.info("[Autotask plugin] Ticket time: " + str(time))

    def alert_device_cleared(self):
        sys.exit("Need a function")

class AutotaskContractHandler(AutotaskContractInterface, Handler):
    class Meta:
        label = 'autotask_contract_handler'

    def _contracts_entity_fields_need_refresh(self, tenant_db):
        cache_name = Autotask_Contract_Category.__tablename__
        cache_name_last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=cache_name).first()
        if cache_name_last_sync:
            last_sync = self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=cache_name).first().last_sync
            if last_sync:
                if last_sync < datetime.datetime.now() - datetime.timedelta(days=7):
                    return True
                else:
                    return False
            else:
                return True

    def _get_contracts_entity_fields(self, tenant_db):
        at = AutotaskTenantHandler.tenant_api_object(self, tenant_db)

        if self._contracts_entity_fields_need_refresh(tenant_db):
            self.app.log.info("[Autotask plugin] TODO: Change this to check if anything changes. If it does, we have to adjust or resync all contract!")
            self.app.log.debug("[Autotask plugin]  Clearing Contracts Entries cashe data")
            self.app.session.query(Autotask_Contract_Category).delete()
            self.app.session.commit()

            self.app.log.debug("[Autotask plugin] Grabing cache for contract types")
            for entity in at._api_read("Contracts/entityInformation/fields")['fields']:
                if entity['name'] == 'contractCategory':
                    self.app.log.info("[Autotask plugin] " + str(entity['name']))
                    for list_value in entity['picklistValues']:
                        entry_db = Autotask_Contract_Category(
                            value = list_value['value'],
                            label = list_value['label'],
                            isActive = list_value['isActive'],
                            tenant_key = tenant_db.primary_key
                        )
                        self.app.session.add(entry_db)
                        self.app.session.commit()
                    
                    self.app.log.debug("[Autotask plugin] Deleting Autotask_Cache_Last_Sync entry if any")
                    cache_name = Autotask_Contract_Category.__tablename__
                    self.app.session.query(Autotask_Cache_Last_Sync).filter_by(name=cache_name).delete()
                    self.app.session.commit()
                    last_sync = Autotask_Cache_Last_Sync(
                            name = cache_name,
                            tenant_key = tenant_db.primary_key,
                            last_sync = datetime.datetime.now()
                    )
                    self.app.session.add(last_sync)
                    self.app.session.commit()

    def pull_company_contract(self, tenant_db, company_autotask_db):
        at = AutotaskTenantHandler.tenant_api_object(self, tenant_db)
        contracts = at.get_contracts_from_company_id(company_autotask_db.autotask_company_id)
        return contracts

    def sync_company(self, tenant_db, company_autotask_db):
        # TODO add ContractServices, might be able to get away with just recording contract ID from Contracts.
        company_db = self.app.session.query(Companies).filter_by( primary_key=company_autotask_db.company_key ).first()
        self.app.log.info("[Autotask plugin] Syncing Contracts for " + company_db.name)
        self._get_contracts_entity_fields(tenant_db)

        contracts_at = self.pull_company_contract(tenant_db, company_autotask_db)
        for contract_at in contracts_at:
            exsiting_contract_db = self.app.session.query( Autotask_Contracts ).filter_by( autotask_id=contract_at['id'] ).first()
            
            if exsiting_contract_db:
                if contract_at['status'] == 0 or contract_at['contractCategory'] == None:
                    self.app.session.delete(exsiting_contract_db)
                else:
                    changed = False
                    if exsiting_contract_db.autotask_name != contract_at['contractName']:
                        exsiting_contract_db.autotask_name = contract_at['contractName']
                        changed = True

                    if exsiting_contract_db.contract_category_value != contract_at['contractCategory']:
                        exsiting_contract_db.contract_category_value = contract_at['contractCategory']
                        changed = True
                    
                    date = contract_at['startDate'].split('T')[0]
                    start_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                    if exsiting_contract_db.start_date != start_date:
                        exsiting_contract_db.start_date = start_date
                        changed = True

                    date = contract_at['endDate'].split('T')[0]
                    end_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                    if exsiting_contract_db.end_date != end_date:
                        exsiting_contract_db.end_date = end_date
                        changed = True
            
                    if changed:
                        self.app.log.debug("[Autotask Plugin] Updating contract in DB: [contract: " + contract_at['contractName'] + "]")
                        self.app.session.commit()
            else:
                if contract_at['status'] != 0 and contract_at['contractCategory'] != None:
                    date = contract_at['startDate'].split('T')[0]
                    start_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                    date = contract_at['endDate'].split('T')[0]
                    end_date = datetime.datetime.strptime(date, "%Y-%m-%d")

                    autotask_contract_db = Autotask_Contracts(
                        autotask_id = contract_at['id'],
                        autotask_company_key = company_autotask_db.primary_key,
                        contract_category_value = contract_at['contractCategory'],
                        autotask_name = contract_at['contractName'],
                        start_date = start_date,
                        end_date = end_date,
                    )
                    self.app.log.debug("[Autotask plugin] Company: " + company_db.name + " adding contract: " + autotask_contract_db.autotask_name)
                    self.app.session.add(autotask_contract_db)
                    self.app.session.commit()

    def sync_tenant(self, tenant_db):
        self.app.log.info("[Autotask plugin] Syncing Autotask Company's contracts")

        companies_autotask_db = self.app.session.query(Autotask_Companies).filter_by( autotask_tenant_key=tenant_db.primary_key ).all()
        for company_autotask_db in companies_autotask_db:
            self.sync_company(tenant_db, company_autotask_db)

    def sync_all(self):
        autotask = self.app.handler.get('autotask_interface', 'autotask_api', setup=True)
        tenants = autotask.tenant.list()
        for tenant in tenants:
            self.sync_tenant(tenant)

class AutotaskAPI(AutotaskInterface, Handler):
    class Meta:
        label = 'autotask_api'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def _setup(self, *args, **kwargs):
        super()._setup(*args, **kwargs)
        self.tenant = self.app.handler.get('autotask_tenant_interface', 'autotask_tenant_handler', setup=True)
        self.company = self.app.handler.get('autotask_company_interface', 'autotask_company_handler', setup=True)
        self.device = self.app.handler.get('autotask_device_interface', 'autotask_device_handler', setup=True)
        self.ticket = self.app.handler.get('autotask_ticket_interface', 'autotask_ticket_handler', setup=True)
        self.contract = self.app.handler.get('autotask_contract_interface', 'autotask_contract_handler', setup=True)
    
    def full_sync(self):
        self.company.sync_all()
        #self.devices.sync_all()
        #self.contracts.sync_all()
        # TODO add last_full_sync date to the database

def alert_update_hook( app ):
    autotask = app.handler.get('autotask_interface', 'autotask_api', setup=True)
    autotask.ticket.create(app.last_alert)
    # TODO Add note about the devices no loner effected by this alert, alert primary tech

# def alert_device_cleared_hook( app ):
#     app.log.debug("[Autotask plugin] Clearing device from an alert")
#     autotask = app.handler.get('autotask_interface', 'autotask_api', setup=True)
#     autotask.ticket.alert_device_cleared()

def alert_cleared_hook( app ):
    app.log.debug("[Autotask plugin] Clearing old alert")
    autotask = app.handler.get('autotask_interface', 'autotask_api', setup=True)

    # Close tickets for cleared alerts
    alerts_db = app.session.query( Alerts ).filter_by( cleared=1 ).all()
    for alert_db in alerts_db:
        autotask.ticket.close_ticket(alert_db)

    # Update tickets for cleared devices
    associations = app.session.query( device_alert_association ).filter_by( cleared=1 ).all()
    for association in associations:
        # TODO group assoications per ticket and add one note, instead of 1 note/deivce state change

        ticket_db = app.session.query( Autotask_Tickets ).filter_by( alert_key=association.alert_key ).first()
        device_db = app.session.query( Devices ).filter_by( primary_key=association.device_key ).first()
        note = "Alert for " + device_db.name + " cleared."
        autotask.ticket.update(ticket_db, note)

def hook_check_alert( app ):
    ticket_db = app.session.query( Autotask_Tickets ).filter_by( alert_key=app.alert_db.primary_key ).first()
    if ticket_db:
        return 1
    else:
        return 0

def full_run(app):
    autotask = app.handler.get('autotask_interface', 'autotask_api', setup=True)
    tenants = app.session.query(Autotask_Tenants).all()
    for tenant in tenants:
        do_full_run = True

        # TODO Make the time configuratable        
        if tenant.last_full_sync != None:
            now = datetime.datetime.now()
            time_diff = now - tenant.last_full_sync
            if time_diff <= datetime.timedelta(days=1):
                do_full_run = False
       
        if do_full_run:
            app.log.info("[Autotask plugin] Syncing companies")
            try:
                autotask.company.sync_tenant(tenant)
            except Exception as e:
                app.log.error("[Autotask plugin] Function: Company Sync Tenant | Tenant: " + tenant.name + " - " + str(e))

            app.log.info("[Autotask plugin] Syncing devices")
            try:
                autotask.device.sync_tenant(tenant)
            except Exception as e:
                app.log.error("[Autotask plugin] Function: Device Sync Tenant | Tenant: " + tenant.name + " - " + str(e))

            # TODO This is too much for every 24 hours. Neeed to create a last sync for each type of sync and configure them based on need
            # TODO Maybe we can do contracts opertunisitly. Meaning we only check for a contract when it's relavant. 
            # TODO So ether there is a ticket for no contract, or there is a contract. If there is a contract, don't bother checking for an update until the next month
            app.log.info("[Autotask plugin] Syncing contracts")
            try:
                autotask.contract.sync_tenant(tenant)
            except Exception as e:
                app.log.error("[Autotask plugin] Function: Contract Sync Tenant | Tenant: " + tenant.name + " - " + str(e))

            app.log.info("[Autotask plugin] Check for stagnant tickets")
            try:
                autotask.ticket.check_all_stagnant()
            except Exception as e:
                app.log.error("[Autotask plugin] Function: Ticket Check All Stagnant | Tenant: " + tenant.name + " - " + str(e))

            tenant.last_full_sync = datetime.datetime.now()
            app.session.commit()
        else:
            app.log.info("[Autotask plugin] Tenant: " + tenant.name + " - Last run was done within 24 hours. Skipping")
