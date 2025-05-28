from flask import Blueprint, request, session, render_template
from manifold_web.routes.auth import get_authenticated_email
from manifold_core.plugins.autotask.core import get_ticket

flows_bp = Blueprint("flows", __name__, url_prefix="/flows")

@flows_bp.route("/livelink/<int:integration_id>")
def livelink_preview(integration_id: int):
    # 🔐 Ensure the user is authenticated
    email = session.get("user", {}).get("email")
    if not email:
        return "Unauthorized: You must be logged in via JumpCloud.", 403

    # 📥 Read the ticket ID from the query string
    ticket_id = request.args.get("ticketID", type=int)
    if not ticket_id:
        return "Missing required ticketID parameter", 400

    try:
        ticket = get_ticket(integration_id, ticket_id)
    except Exception as e:
        return f"Failed to retrieve ticket: {e}", 500   

    return render_template("flows/livelink_preview.html", ticket=ticket)

