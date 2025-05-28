from flask import Blueprint, request, session, render_template
import logging
from flask import jsonify

from manifold_web.routes.auth import get_authenticated_email
from manifold_core.plugins.autotask.core import get_ticket, extract_udf
from manifold_core.plugins.slack.api import SlackAPI
from manifold_core.plugins.slack.core import get_slack_name


flows_bp = Blueprint("flows", __name__, url_prefix="/flows")
logger = logging.getLogger(__name__)

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

    # Step 1: Try to retrieve the Autotask ticket
    try:
        ticket = get_ticket(integration_id, ticket_id)
    except Exception as e:
        logger.exception("Failed to fetch Autotask ticket")
        return jsonify({"error": f"Failed to fetch ticket: {str(e)}"}), 500

    # Step 2: Try to retrieve Slack channel
    slack_id = extract_udf(ticket, "SlackID")
    slack_error = None

    if not slack_id:
        try:
            slack = SlackAPI(get_slack_name())
            channel_name = f"ticket-{ticket['ticketNumber'].lower().replace('.', '_')}"
            logger.debug(f"Looking up Slack channel: {channel_name}")

            channel_id = slack.get_channel_id_by_name(channel_name)

            if channel_id:
                slack_id = channel_id
                logger.debug(f"Found Slack channel ID: {channel_id}")

                # TODO: Update Autotask ticket UDF with slack_id here

            else:
                logger.warning(f"Slack channel not found: {channel_name}")

        except Exception as e:
            slack_error = f"Slack integration failed: {str(e)}"
            logger.exception("Slack lookup failed")

    # Step 3: Return the results
    return jsonify({
        "ticket": ticket,
        "slack_id": slack_id,
        "slack_error": slack_error
    })

