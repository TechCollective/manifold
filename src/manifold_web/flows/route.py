from flask import Blueprint, request, session, render_template
from manifold_web.routes.auth import get_authenticated_email

flows_bp = Blueprint("flows", __name__, url_prefix="/flows")

@flows_bp.route("/livelink", methods=["GET"])
def livelink_landing():
    # ✅ Pull the ticket ID from query params
    ticket_id = request.args.get("ticketID")
    if not ticket_id:
        return "Missing ticketID", 400

    # ✅ Get authenticated email (abstracted for auth system)
    email = get_authenticated_email(session)
    if not email:
        return "Unauthorized: No authenticated email found.", 403

    # ✅ For now, just show the information
    return render_template("flows/livelink_preview.html", ticket_id=ticket_id, email=email)
