from flask import Blueprint, request, session, render_template
from manifold_web.routes.auth import get_authenticated_email
from manifold_core.plugins.autotask.core import get_ticket, extract_udf
from flask import jsonify
from manifold_core.plugins.slack.api import SlackAPI

flows_bp = Blueprint("flows", __name__, url_prefix="/flows")


@flows_bp.route("/livelink/<int:integration_id>")
def livelink_preview(integration_id: int):
    email = session.get("user", {}).get("email")
    if not email:
        return "Unauthorized", 403

    return render_template("flows/livelink_preview.html", integration_id=integration_id)


@flows_bp.route("/api/livelink/<int:integration_id>")
def api_livelink_preview(integration_id: int):
    email = session.get("user", {}).get("email")
    if not email:
        return jsonify({"error": "Unauthorized"}), 403

    ticket_id = request.args.get("ticketID", type=int)
    if not ticket_id:
        return jsonify({"error": "Missing ticketID parameter"}), 400

    try:
        ticket = get_ticket(integration_id, ticket_id)
        slack_id = extract_udf(ticket, "SlackID")

        # If no Slack channel has been set, try to look it up
        if not slack_id:
            slack = SlackAPI("default")  # update name if needed
            channel_name = f"{ticket['ticketNumber'].lower().replace('.', '_')}"
            channel_id = slack.get_channel_id_by_name(channel_name)

            if channel_id:
                # Optionally: update Autotask UDF with this channel ID here
                slack_id = channel_id

        return jsonify({
            "ticket": ticket,
            "slack_id": slack_id
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500
