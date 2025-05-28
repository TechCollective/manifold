from flask import Blueprint, request, session, render_template
from manifold_web.routes.auth import get_authenticated_email

flows_bp = Blueprint("flows", __name__, url_prefix="/flows")

@flows_bp.route("/livelink", methods=["GET"])
def livelink_preview():
    # 🔐 Ensure the user is authenticated
    email = session.get("user", {}).get("email")
    if not email:
        return "Unauthorized: You must be logged in via JumpCloud.", 403

    # 📥 Read the ticket ID from the query string
    ticket_id = request.args.get("ticketID")
    if not ticket_id:
        return "Missing required ticketID parameter", 400

    # 🔎 Look up the ticket info using Autotask API
    from manifold_core.plugins.autotask.core import list_autotask_integrations
    from manifold_core.plugins.autotask.api import AutotaskAPI

    integrations = list_autotask_integrations()
    if not integrations:
        return "No Autotask integration configured.", 500

    try:
        api = AutotaskAPI(integrations[0].id)
        ticket = api.get_ticket(ticket_id)

        ticket_number = ticket.get("ticketNumber")
        description = ticket.get("title") or ticket.get("description") or ""
        udf_fields = ticket.get("userDefinedFields", {})
        slack_id = udf_fields.get("SlackID")

    except Exception as e:
        return f"Failed to retrieve ticket: {e}", 500

    return render_template("livelink_preview.html",
                           email=email,
                           ticket_id=ticket_id,
                           ticket_number=ticket_number,
                           ticket_description=description,
                           slack_id=slack_id)

