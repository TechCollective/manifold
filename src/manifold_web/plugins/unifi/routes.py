from flask import Blueprint, render_template, request, redirect, flash, render_template, jsonify, url_for
from manifold_core.secrets.get import get_secret_backend
from manifold_core.models.base import SessionLocal
from manifold_core.plugins.unifi.models import UnifiServer, UnifiAdmin
from manifold_core.plugins.unifi.servers import (
    list_unifi_servers,
    add_unifi_server,
    edit_unifi_server,
    delete_unifi_server,
    set_unifi_credentials,
)

from manifold_core.plugins.unifi.sites import (
    get_unifi_sites,
    sync_unifi_sites
)

from manifold_core.plugins.unifi.devices import (
    lookup_unifi_device,
    sync_unifi_devices
)

from manifold_core.plugins.unifi.admins import (
    get_admins_for_server,
    get_admins_for_site,
    remove_admin_from_site,
    remove_admin_from_all_sites,
    get_admin_info,
    list_all_admins,
    sync_unifi_admins,
    get_all_unifi_admins
)

from manifold_core.plugins.unifi.alerts import (
    sync_unifi_alerts,
    get_all_unifi_alerts,
    get_alert_keys,
    update_alert_key_description
)

from manifold_web.utils.integration_config import get_integration_config


unifi_bp = Blueprint("unifi", __name__, template_folder="templates")


@unifi_bp.route("/unifi", methods=["GET"])
def index():
    servers = list_unifi_servers()
    return render_template("unifi.html", unifi_servers=servers)


@unifi_bp.route("/unifi/test", methods=["GET"])
def test():
    return render_template("unifi_test.html")


@unifi_bp.route("/unifi/<int:server_id>/edit", methods=["GET"])
def edit_unifi_server_page(server_id):
    """Show edit server page"""
    session = SessionLocal()
    server = session.query(UnifiServer).filter(UnifiServer.id == server_id).first()
    session.close()
    
    if not server:
        flash("Server not found", "error")
        return redirect(url_for("unifi.index"))
    
    return render_template("unifi_edit.html", server=server)


@unifi_bp.route("/unifi/<int:server_id>/add-credentials", methods=["GET"])
def add_credentials_page(server_id):
    """Show add credentials page"""
    session = SessionLocal()
    server = session.query(UnifiServer).filter(UnifiServer.id == server_id).first()
    session.close()
    
    if not server:
        flash("Server not found", "error")
        return redirect(url_for("unifi.index"))
    
    return render_template("unifi_credentials.html", server=server)


@unifi_bp.route("/unifi/add", methods=["POST"])
def add_unifi_server_route():
    try:
        name = request.form["name"]
        host = request.form["host"]
        port = int(request.form["port"])
        username = request.form["username"]
        password = request.form["password"]

        server = add_unifi_server(name, host, port)
        set_unifi_credentials(server.id, username, password)

    except Exception as e:
        print(f"Failed to add server: {e}")

    return redirect(url_for("unifi.index"))


@unifi_bp.route("/unifi/edit/<int:server_id>", methods=["POST"])
def edit_unifi_server_route(server_id):
    try:
        edit_unifi_server(server_id, {
            "name": request.form["name"],
            "host": request.form["host"],
            "port": int(request.form["port"]),
        })
    except Exception as e:
        print(f"Edit failed: {e}")
    return redirect(url_for("unifi.index"))


@unifi_bp.route("/unifi/delete/<int:server_id>", methods=["POST"])
def delete_unifi_server_route(server_id):
    try:
        delete_unifi_server(server_id)
    except Exception as e:
        print(f"Delete failed: {e}")
    return redirect(url_for("unifi.index"))


@unifi_bp.route("/unifi/credentials", methods=["POST"])
def set_unifi_credentials_route():
    try:
        server_id = int(request.form["id"])
        username = request.form["username"]
        password = request.form["password"]
        set_unifi_credentials(server_id, username, password)
    except Exception as e:
        print(f"Credential set failed: {e}")
    return redirect(url_for("unifi.index"))



@unifi_bp.route("/unifi/<int:server_id>/sites", methods=["GET"])
def get_sites_json(server_id):
    try:
        sites = get_unifi_sites(server_id)
        return jsonify(sites)
    except Exception as e:
        print(f"Error fetching sites for server {server_id}: {e}")
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/sites/all", methods=["GET"])
def get_all_sites_json():
    """Get all sites from all servers."""
    try:
        from manifold_core.plugins.unifi.sites import get_all_unifi_sites
        sites = get_all_unifi_sites()
        return jsonify(sites)
    except Exception as e:
        print(f"Error fetching all sites: {e}")
        return jsonify({"error": str(e)}), 500
    
@unifi_bp.route("/unifi/sync-sites", methods=["POST"])
def sync_sites_web():
    try:
        sync_unifi_sites()  # Import this from your core if not already
        flash("Sites synced successfully.", "success")
    except Exception as e:
        flash(f"Failed to sync sites: {str(e)}", "error")
    return redirect(url_for("unifi.index"))

@unifi_bp.route("/unifi/sync-devices", methods=["POST"])
def sync_devices_web():
    try:
        count = sync_unifi_devices()  # Function doesn't accept server_id parameter
        flash(f"Synced {count} devices successfully.", "success")
    except Exception as e:
        flash(f"Error syncing devices: {str(e)}", "error")
    return redirect(url_for("unifi.index"))


@unifi_bp.route("/unifi/lookup-device", methods=["POST"])
def lookup_device():
    data = request.get_json()
    identifier = data.get("identifier")

    if not identifier:
        return jsonify({"error": "Missing identifier."}), 400

    try:
        result = lookup_unifi_device(identifier)
        if not result or result.get("error"):
            return jsonify({"error": "Device not found."}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/devices/all", methods=["GET"])
def get_all_devices_json():
    """Get all devices from all servers."""
    try:
        from manifold_core.plugins.unifi.devices import get_all_unifi_devices
        devices = get_all_unifi_devices()
        return jsonify(devices)
    except Exception as e:
        print(f"Error fetching all devices: {e}")
        return jsonify({"error": str(e)}), 500


# Admin Management Routes
@unifi_bp.route("/unifi/<int:server_id>/admins", methods=["GET"])
def get_admins_json(server_id):
    """Get all admins for a specific server."""
    try:
        admins = get_admins_for_server(server_id)
        return jsonify(admins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/<int:server_id>/sites/<site_name>/admins", methods=["GET"])
def get_site_admins_json(server_id, site_name):
    """Get admins for a specific site."""
    try:
        admins = get_admins_for_site(server_id, site_name)
        return jsonify(admins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/<int:server_id>/admins/<admin_id>/info", methods=["GET"])
def get_admin_info_json(server_id, admin_id):
    """Get detailed information about a specific admin."""
    try:
        exclude_sites = request.args.getlist("exclude_sites")
        admin_info = get_admin_info(server_id, admin_id, exclude_sites)
        if admin_info:
            return jsonify(admin_info)
        else:
            return jsonify({"error": "Admin not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/<int:server_id>/admins/<admin_id>/remove", methods=["POST"])
def remove_admin_route(server_id, admin_id):
    """Remove an admin from all sites except excluded ones."""
    try:
        data = request.get_json()
        exclude_sites = data.get("exclude_sites", [])
        
        result = remove_admin_from_all_sites(server_id, admin_id, exclude_sites)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/<int:server_id>/sites/<site_name>/admins/<admin_id>/remove", methods=["POST"])
def remove_admin_from_site_route(server_id, site_name, admin_id):
    """Remove an admin from a specific site."""
    try:
        success = remove_admin_from_site(server_id, site_name, admin_id)
        if success:
            return jsonify({"success": True, "message": f"Admin removed from site {site_name}"})
        else:
            return jsonify({"error": f"Failed to remove admin from site {site_name}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/sync-admins", methods=["POST"])
def sync_admins_web():
    try:
        count = sync_unifi_admins()
        flash(f"Synced {count} admins successfully.", "success")
    except Exception as e:
        flash(f"Error syncing admins: {str(e)}", "error")
    return redirect(url_for("unifi.index"))


@unifi_bp.route("/unifi/admins", methods=["GET"])
def list_all_admins_route():
    """Get all admins from all servers."""
    try:
        admins = get_all_unifi_admins()
        return jsonify(admins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/admin/revoke", methods=["POST"])
def revoke_admin_access():
    """Revoke admin access from selected sites."""
    try:
        data = request.get_json()
        admin_id = data.get("admin_id")
        site_names = data.get("site_names", [])
        
        if not admin_id or not site_names:
            return jsonify({"error": "Missing admin_id or site_names"}), 400
        
        # Get the server for the admin
        session = SessionLocal()
        admin = session.query(UnifiAdmin).filter_by(id=admin_id).first()
        if not admin:
            session.close()
            return jsonify({"error": "Admin not found"}), 404
        
        server = admin.server
        session.close()
        
        # Use the UniFi API to revoke access
        from manifold_core.plugins.unifi.api import UniFiAPI
        api = UniFiAPI(server)
        
        results = {}
        for site_name in site_names:
            success = api.remove_admin_from_site(site_name, admin_id)
            results[site_name] = success
        
        return jsonify({"results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/admin/add", methods=["POST"])
def add_admin_access():
    """Add admin access to selected sites."""
    try:
        data = request.get_json()
        admin_id = data.get("admin_id")
        site_names = data.get("site_names", [])
        role = data.get("role", "admin")
        
        if not admin_id or not site_names:
            return jsonify({"error": "Missing admin_id or site_names"}), 400
        
        # Get the server for the admin
        session = SessionLocal()
        admin = session.query(UnifiAdmin).filter_by(id=admin_id).first()
        if not admin:
            session.close()
            return jsonify({"error": "Admin not found"}), 404
        
        server = admin.server
        session.close()
        
        # Use the UniFi API to add access
        from manifold_core.plugins.unifi.api import UniFiAPI
        api = UniFiAPI(server)
        
        results = {}
        for site_name in site_names:
            success = api.add_admin_to_site(site_name, admin_id, role)
            results[site_name] = success
        
        return jsonify({"results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/admin/modify", methods=["POST"])
def modify_admin_role():
    """Modify admin role on selected sites."""
    try:
        data = request.get_json()
        admin_id = data.get("admin_id")
        site_names = data.get("site_names", [])
        role = data.get("role", "admin")
        
        if not admin_id or not site_names:
            return jsonify({"error": "Missing admin_id or site_names"}), 400
        
        # Get the server for the admin
        session = SessionLocal()
        admin = session.query(UnifiAdmin).filter_by(id=admin_id).first()
        if not admin:
            session.close()
            return jsonify({"error": "Admin not found"}), 404
        
        server = admin.server
        session.close()
        
        # Use the UniFi API to modify role
        from manifold_core.plugins.unifi.api import UniFiAPI
        api = UniFiAPI(server)
        
        results = {}
        for site_name in site_names:
            success = api.modify_admin_role(site_name, admin_id, role)
            results[site_name] = success
        
        return jsonify({"results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Alert Management Routes
@unifi_bp.route("/unifi/sync-alerts", methods=["POST"])
def sync_alerts_web():
    try:
        count = sync_unifi_alerts()
        flash(f"Synced {count} alerts successfully.", "success")
    except Exception as e:
        flash(f"Error syncing alerts: {str(e)}", "error")
    return redirect(url_for("unifi.index"))


@unifi_bp.route("/unifi/alerts/all", methods=["GET"])
def list_all_alerts_route():
    """Get all alerts from all servers."""
    try:
        alerts = get_all_unifi_alerts()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/alert-keys", methods=["GET"])
def list_alert_keys_route():
    """Get all alert keys with descriptions."""
    try:
        keys = get_alert_keys()
        return jsonify(keys)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/alert-keys/<int:key_id>/description", methods=["PUT"])
def update_alert_key_description_route(key_id):
    """Update the description for an alert key."""
    try:
        data = request.get_json()
        description = data.get("description", "")
        
        success = update_alert_key_description(key_id, description)
        if success:
            return jsonify({"success": True, "message": "Description updated successfully"})
        else:
            return jsonify({"error": "Alert key not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@unifi_bp.route("/unifi/admin/revoke-super", methods=["POST"])
def revoke_super_admin():
    """Revoke super admin status from an admin"""
    try:
        data = request.get_json()
        admin_id = data.get("admin_id")
        
        if not admin_id:
            return jsonify({"success": False, "error": "Missing admin_id"}), 400
        
        # Get the server for this admin
        session = SessionLocal()
        admin = session.query(UnifiAdmin).filter(UnifiAdmin.id == admin_id).first()
        if not admin:
            session.close()
            return jsonify({"success": False, "error": "Admin not found"}), 404
        
        server = session.query(UnifiServer).filter(UnifiServer.id == admin.server_id).first()
        session.close()
        
        if not server:
            return jsonify({"success": False, "error": "Server not found"}), 404
        
        # Import here to avoid circular imports
        from manifold_core.plugins.unifi.api import UniFiAPI
        
        api = UniFiAPI(server)
        success = api.revoke_super_admin(admin_id)
        
        if success:
            # Update the admin's is_super status in the database
            session = SessionLocal()
            admin = session.query(UnifiAdmin).filter(UnifiAdmin.id == admin_id).first()
            if admin:
                admin.is_super = "false"
                session.commit()
            session.close()
            
            return jsonify({
                "success": True,
                "message": "Super admin status revoked successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to revoke super admin status"
            }), 500
        
    except Exception as e:
        print(f"Error revoking super admin: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


__all__ = ["unifi_bp"]