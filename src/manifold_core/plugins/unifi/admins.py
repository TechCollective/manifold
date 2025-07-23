"""
Admin management for UniFi integrations.
"""

from typing import Dict, List, Optional, Any
from manifold_core.models.base import SessionLocal
from manifold_core.plugins.unifi.models import UnifiServer, UnifiAdmin, UnifiAdminSitePermission, UnifiSite
from manifold_core.plugins.unifi.api import UniFiAPI


def sync_unifi_admins(server_id=None):
    """
    Sync admins from UniFi servers to the database.
    
    Args:
        server_id: Optional specific server ID to sync. If None, syncs all servers.
        
    Returns:
        Number of admins synced
    """
    session = SessionLocal()
    
    try:
        if server_id:
            servers = session.query(UnifiServer).filter_by(id=server_id).all()
        else:
            servers = session.query(UnifiServer).all()
        
        count = 0
        total_attempted = 0
        
        for server in servers:
            try:
                api = UniFiAPI(server)
                admins = api.get_admins()
                total_attempted += len(admins) if admins else 0
                
                print(f"\n=== Admin sync for server {server.name} ===")
                if admins:
                    print(f"Found {len(admins)} admin users")
                    
                    # Get all existing admins for this server
                    existing_admins = session.query(UnifiAdmin).filter_by(server_id=server.id).all()
                    existing_admin_ids = {admin.id for admin in existing_admins}
                    
                    # Track admins found in this sync
                    found_admin_ids = set()
                    
                    for admin in admins:
                        admin_id = admin.get("_id")
                        name = admin.get("name", "Unknown")
                        email = admin.get("email", "")
                        is_super = str(admin.get("is_super", "false")).lower()
                        
                        # Use email as username if no specific username field
                        username = admin.get("ubic_name", email)
                        
                        found_admin_ids.add(admin_id)
                        print(f"Processing admin: {name} ({email}) - Super Admin: {is_super}")
                        
                        # Check if admin already exists
                        existing_admin = session.query(UnifiAdmin).filter_by(
                            id=admin_id,
                            server_id=server.id
                        ).first()
                        
                        if not existing_admin:
                            new_admin = UnifiAdmin(
                                id=admin_id,
                                server_id=server.id,
                                name=name,
                                username=username,
                                email=email,
                                is_super=is_super,
                                active="true"
                            )
                            session.add(new_admin)
                            count += 1
                            print(f"Added admin: {name}")
                        else:
                            # Update existing admin
                            existing_admin.name = name
                            existing_admin.username = username
                            existing_admin.email = email
                            existing_admin.is_super = is_super
                            existing_admin.active = "true"  # Mark as active since it exists
                            print(f"Updated admin: {name}")
                        
                        # Handle site permissions for non-super admins
                        if is_super != "true":
                            # Get roles array from admin data
                            roles = admin.get("roles", [])
                            
                            # Clear existing site permissions for this admin
                            session.query(UnifiAdminSitePermission).filter_by(admin_id=admin_id).delete()
                            
                            # Add site permissions for each role
                            for role_data in roles:
                                site_id = role_data.get("site_id")
                                site_name = role_data.get("site_name")
                                site_desc = role_data.get("site_desc")
                                role = role_data.get("role")
                                permissions = role_data.get("permissions", [])
                                
                                if site_id and site_name:
                                    # Create site permission record regardless of whether site exists in our database
                                    # This allows us to track admin permissions even for sites we haven't synced yet
                                    site_permission = UnifiAdminSitePermission(
                                        admin_id=admin_id,
                                        site_id=site_id,
                                        site_name=site_name,
                                        site_desc=site_desc,
                                        role=role,
                                        permissions=str(permissions) if permissions else None
                                    )
                                    session.add(site_permission)
                                    print(f"  Added site permission: {site_name} ({role})")
                                else:
                                    print(f"  Warning: Invalid role data - missing site_id or site_name")
                        else:
                            print(f"  Skipping site permissions for super admin")
                    
                    # Mark admins that weren't found as inactive
                    for admin_id in existing_admin_ids - found_admin_ids:
                        admin = session.query(UnifiAdmin).filter_by(id=admin_id, server_id=server.id).first()
                        if admin:
                            admin.active = "false"
                            print(f"Marked admin {admin.name} as inactive (not found in UniFi)")
                else:
                    print("No admin data found")
                
                session.commit()
                
            except Exception as e:
                session.rollback()
                print(f"Error syncing admins for server {server.name}: {e}")
        
        print(f"\n=== Sync Summary ===")
        print(f"Total entries processed: {total_attempted}")
        print(f"Actual admins synced: {count}")
        
        return count
        
    finally:
        session.close()


def get_all_unifi_admins() -> List[Dict[str, Any]]:
    """
    Get all admins from the database.
    
    Returns:
        List of admin dictionaries
    """
    session = SessionLocal()
    try:
        # Query only active admins
        admins = session.query(UnifiAdmin).filter(UnifiAdmin.active == "true").all()
        result = []
        for admin in admins:
            # Determine role based on is_super flag and site permissions
            if admin.is_super == "true":
                role = "Super Administrator"
            else:
                # Get site-specific roles from permissions table
                site_permissions = session.query(UnifiAdminSitePermission).filter_by(admin_id=admin.id).all()
                if site_permissions:
                    # Check for different role types
                    has_admin_role = any(perm.role == "admin" for perm in site_permissions)
                    has_hotspot_role = any(perm.role == "hotspot" for perm in site_permissions)
                    has_readonly_role = any(perm.role == "readonly" for perm in site_permissions)
                    
                    if has_admin_role:
                        role = "Site Administrator"
                    elif has_hotspot_role:
                        role = "HotSpot Manager"
                    elif has_readonly_role:
                        role = "Read Only"
                    else:
                        # If no specific role found, use the first available role or default
                        roles = [perm.role for perm in site_permissions if perm.role]
                        role = roles[0] if roles else "Site Administrator"
                else:
                    role = "Site Administrator"
            
            # Get site permissions for this admin
            site_permissions = []
            if admin.is_super != "true":
                permissions = session.query(UnifiAdminSitePermission).filter_by(admin_id=admin.id).all()
                site_permissions = [
                    {
                        "site_id": perm.site_id,
                        "site_name": perm.site_name,
                        "site_desc": perm.site_desc,
                        "role": perm.role,
                        "permissions": perm.permissions
                    }
                    for perm in permissions
                ]
            
            result.append({
                "id": admin.id,
                "name": admin.name,
                "username": admin.username,
                "email": admin.email,
                "role": role,
                "site_permissions": site_permissions
            })
        session.close()
        return result
    except Exception as e:
        session.close()
        print(f"Error getting all admins: {e}")
        return []


def get_admins_for_server(server_id: int) -> List[Dict[str, Any]]:
    """
    Get all admins from a specific UniFi server.
    
    Args:
        server_id: The UniFi server ID
        
    Returns:
        List of admin dictionaries
    """
    session = SessionLocal()
    try:
        server = session.query(UnifiServer).filter_by(id=server_id).first()
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")
            
        api = UniFiAPI(server)
        return api.get_admins()
        
    finally:
        session.close()


def get_admins_for_site(server_id: int, site_name: str) -> List[Dict[str, Any]]:
    """
    Get admins for a specific site on a specific server.
    
    Args:
        server_id: The UniFi server ID
        site_name: The UniFi site name
        
    Returns:
        List of admin dictionaries for the site
    """
    session = SessionLocal()
    try:
        server = session.query(UnifiServer).filter_by(id=server_id).first()
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")
            
        api = UniFiAPI(server)
        return api.get_site_admins(site_name)
        
    finally:
        session.close()


def remove_admin_from_site(server_id: int, site_name: str, admin_id: str) -> bool:
    """
    Remove an admin from a specific site.
    
    Args:
        server_id: The UniFi server ID
        site_name: The UniFi site name
        admin_id: The admin user ID to remove
        
    Returns:
        True if successful, False otherwise
    """
    session = SessionLocal()
    try:
        server = session.query(UnifiServer).filter_by(id=server_id).first()
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")
            
        api = UniFiAPI(server)
        return api.remove_admin_from_site(site_name, admin_id)
        
    finally:
        session.close()


def remove_admin_from_all_sites(server_id: int, admin_id: str, exclude_sites: List[str] = None) -> Dict[str, Any]:
    """
    Remove an admin from all sites on a server except those in exclude_sites.
    
    Args:
        server_id: The UniFi server ID
        admin_id: The admin user ID to remove
        exclude_sites: List of site names to exclude from removal
        
    Returns:
        Dictionary with results for each site
    """
    session = SessionLocal()
    try:
        server = session.query(UnifiServer).filter_by(id=server_id).first()
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")
            
        api = UniFiAPI(server)
        return api.remove_admin_from_all_sites(admin_id, exclude_sites)
        
    finally:
        session.close()


def get_admin_info(server_id: int, admin_id: str, exclude_sites: List[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific admin across all sites except excluded ones.
    
    Args:
        server_id: The UniFi server ID
        admin_id: The admin user ID
        exclude_sites: List of site names to exclude from search
        
    Returns:
        Dictionary with admin information across sites or None if not found
    """
    session = SessionLocal()
    try:
        server = session.query(UnifiServer).filter_by(id=server_id).first()
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")
            
        api = UniFiAPI(server)
        return api.get_admin_info(admin_id, exclude_sites)
        
    finally:
        session.close()


def list_all_admins() -> List[Dict[str, Any]]:
    """
    Get all admins from all UniFi servers.
    
    Returns:
        List of admin dictionaries with server information
    """
    session = SessionLocal()
    try:
        servers = session.query(UnifiServer).all()
        all_admins = []
        
        for server in servers:
            try:
                api = UniFiAPI(server)
                admins = api.get_admins()
                
                for admin in admins:
                    admin_info = admin.copy()
                    admin_info["server_id"] = server.id
                    admin_info["server_name"] = server.name
                    admin_info["server_host"] = server.host
                    all_admins.append(admin_info)
                    
            except Exception as e:
                print(f"Error getting admins from server {server.name}: {e}")
                
        return all_admins
        
    finally:
        session.close() 