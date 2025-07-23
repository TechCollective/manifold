# manifold_core/plugins/unifi/api.py

from pyunifi.controller import Controller
from manifold_core.plugins.unifi.models import UnifiServer
from manifold_core.secrets.get import get_secret_backend


class UniFiAPI:
    def __init__(self, server: UnifiServer):
        self.server = server
        self.controller = None
        self.secrets = get_secret_backend()

    def _get_credentials(self):
        username = self.secrets.get_secret(f"unifi:{self.server.name}:username")
        password = self.secrets.get_secret(f"unifi:{self.server.name}:password")
        return username, password

    def connect(self):
        username, password = self._get_credentials()
        self.controller = Controller(
            host=self.server.host,
            username=username,
            password=password,
            port=self.server.port,
            ssl_verify=True,
        )
        self.controller._login()

    def get_version(self):
        if not self.controller:
            self.connect()
        return self.controller.get_controller_version()

    def is_unifi_os(self):
        version = self.get_version()
        return "/proxy/network" in self.controller.baseurl

    # Example future method
    def get_sites(self):
        if not self.controller:
            self.connect()
        return self.controller.get_sites()

    def get_admins(self):
        """Get all admins from the UniFi controller."""
        if not self.controller:
            self.connect()
        
        try:
            print("Getting admin users using api/stat/admin endpoint...")
            admin_response = self.controller._read(self.controller.url + "api/stat/admin")

            print(f"Found {len(admin_response)} admin users")
            return admin_response
                    
        except Exception as e:
            print(f"Error getting admins: {e}")
            return []

    def get_site_admins(self, site_name: str):
        """Get admins for a specific site."""
        if not self.controller:
            self.connect()
        
        # Set site context directly using site name
        self.controller.site_id = site_name
        
        try:
            # Use the correct admin API endpoint
            return self.controller._api_read(f"api/s/{site_name}/stat/admin")
        except Exception as e:
            print(f"Admin API failed for site {site_name}: {e}")
            # Fallback to empty list if admin API fails
            return []

    def remove_admin_from_site(self, site_name: str, admin_id: str) -> bool:
        """
        Remove an admin from a specific site using the cmd/sitemgr endpoint.
        
        Args:
            site_name: The UniFi site name
            admin_id: The admin user ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self.controller:
            self.connect()
        
        try:
            # Set site context
            self.controller.site_id = site_name
            
            # Use the cmd/sitemgr endpoint with revoke-admin command
            params = {"admin": admin_id, "cmd": "revoke-admin"}
            result = self.controller._api_write("cmd/sitemgr", params=params)
            
            print(f"Revoked admin {admin_id} from site {site_name}: {result}")
            return result is not None
            
        except Exception as e:
            print(f"Error removing admin {admin_id} from site {site_name}: {e}")
            return False

    def add_admin_to_site(self, site_name: str, admin_id: str, role: str = "admin") -> bool:
        """
        Add an admin to a specific site using the cmd/sitemgr endpoint.
        
        Args:
            site_name: The UniFi site name
            admin_id: The admin user ID to add
            role: The role to assign (admin, hotspot, readonly)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.controller:
            self.connect()
        
        try:
            # Set site context
            self.controller.site_id = site_name
            
            # Use the cmd/sitemgr endpoint with grant-admin command
            params = {"admin": admin_id, "cmd": "grant-admin", "role": role}
            result = self.controller._api_write("cmd/sitemgr", params=params)
            
            print(f"Granted admin {admin_id} role '{role}' on site {site_name}: {result}")
            return result is not None
            
        except Exception as e:
            print(f"Error adding admin {admin_id} to site {site_name}: {e}")
            return False

    def modify_admin_role(self, site_name: str, admin_id: str, role: str) -> bool:
        """
        Modify an admin's role on a specific site using the cmd/sitemgr endpoint.
        
        Args:
            site_name: The UniFi site name
            admin_id: The admin user ID to modify
            role: The new role to assign (admin, hotspot, readonly)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.controller:
            self.connect()
        
        try:
            # Set site context
            self.controller.site_id = site_name
            
            # Use the cmd/sitemgr endpoint with grant-admin command to modify role
            params = {"admin": admin_id, "cmd": "grant-admin", "role": role}
            result = self.controller._api_write("cmd/sitemgr", params=params)
            
            print(f"Modified admin {admin_id} role to '{role}' on site {site_name}: {result}")
            return result is not None
            
        except Exception as e:
            print(f"Error modifying admin {admin_id} role on site {site_name}: {e}")
            return False

    def revoke_super_admin(self, admin_id: str) -> bool:
        """
        Revoke super admin status from an admin using the cmd/sitemgr endpoint.
        
        Args:
            admin_id: The admin user ID to revoke super admin status from
            
        Returns:
            True if successful, False otherwise
        """
        if not self.controller:
            self.connect()
        
        try:
            # Use the cmd/sitemgr endpoint with revoke-super-admin command
            params = {"admin": admin_id, "cmd": "revoke-super-admin"}
            result = self.controller._api_write("cmd/sitemgr", params=params)
            
            print(f"Revoked super admin status from {admin_id}: {result}")
            return result is not None
            
        except Exception as e:
            print(f"Error revoking super admin status from {admin_id}: {e}")
            return False

    def remove_admin_from_all_sites(self, admin_id: str, exclude_sites: list = None) -> dict:
        """
        Remove an admin from all sites except those in exclude_sites.
        
        Args:
            admin_id: The admin user ID to remove
            exclude_sites: List of site names to exclude from removal
            
        Returns:
            Dictionary with results for each site
        """
        if not self.controller:
            self.connect()
        
        if exclude_sites is None:
            exclude_sites = []
        
        sites = self.get_sites()
        results = {
            "admin_id": admin_id,
            "total_sites": len(sites),
            "excluded_sites": exclude_sites,
            "removed_from": [],
            "failed_sites": [],
            "skipped_sites": []
        }
        
        for site in sites:
            site_name = site.get("name", "Unknown")
            
            if site_name in exclude_sites:
                results["skipped_sites"].append({
                    "site_name": site_name,
                    "site_desc": site.get("desc", ""),
                    "reason": "Explicitly excluded"
                })
                continue
            
            success = self.remove_admin_from_site(site_name, admin_id)
            
            if success:
                results["removed_from"].append({
                    "site_name": site_name,
                    "site_desc": site.get("desc", "")
                })
            else:
                results["failed_sites"].append({
                    "site_name": site_name,
                    "site_desc": site.get("desc", ""),
                    "reason": "API call failed"
                })
        
        return results

    def get_admin_info(self, admin_id: str, exclude_sites: list = None) -> dict:
        """
        Get information about a specific admin across all sites except excluded ones.
        
        Args:
            admin_id: The admin user ID
            exclude_sites: List of site names to exclude from search
            
        Returns:
            Dictionary with admin information across sites
        """
        if not self.controller:
            self.connect()
        
        if exclude_sites is None:
            exclude_sites = []
        
        admin_info = {
            "admin_id": admin_id,
            "sites": [],
            "total_sites": 0,
            "excluded_sites": exclude_sites
        }
        
        sites = self.get_sites()
        
        for site in sites:
            site_name = site.get("name", "Unknown")
            if site_name in exclude_sites:
                continue
                
            try:
                # Set site context for this iteration
                self.controller.site_id = site_name
                site_admins = self.controller.get_users()
                admin = next((a for a in site_admins if a.get("name") == admin_id), None)
                
                if admin:
                    admin_info["sites"].append({
                        "site_name": site_name,
                        "site_desc": site.get("desc", ""),
                        "admin_info": admin
                    })
                    admin_info["total_sites"] += 1
                    
            except Exception as e:
                print(f"Error getting admin info for site {site_name}: {e}")
                continue
                
        return admin_info
