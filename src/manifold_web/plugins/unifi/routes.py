from flask import Blueprint, render_template, request, redirect, flash, render_template, jsonify, url_for
from manifold_core.secrets.get import get_secret_backend
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


unifi_bp = Blueprint("unifi", __name__, template_folder="templates")



@unifi_bp.route("/unifi", methods=["GET"])
def index():
    servers = list_unifi_servers()
    return render_template("unifi.html", unifi_servers=servers)


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

    return redirect("/unifi")


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
    return redirect("/unifi")


@unifi_bp.route("/unifi/delete/<int:server_id>", methods=["POST"])
def delete_unifi_server_route(server_id):
    try:
        delete_unifi_server(server_id)
    except Exception as e:
        print(f"Delete failed: {e}")
    return redirect("/unifi")


@unifi_bp.route("/unifi/credentials", methods=["POST"])
def set_unifi_credentials_route():
    try:
        server_id = int(request.form["id"])
        username = request.form["username"]
        password = request.form["password"]
        set_unifi_credentials(server_id, username, password)
    except Exception as e:
        print(f"Credential set failed: {e}")
    return redirect("/unifi")



@unifi_bp.route("/unifi/<int:server_id>/sites", methods=["GET"])
def get_sites_json(server_id):
    try:
        sites = get_unifi_sites(server_id)
        return jsonify(sites)
    except Exception as e:
        print(f"Error fetching sites for server {server_id}: {e}")
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


__all__ = ["unifi_bp"]