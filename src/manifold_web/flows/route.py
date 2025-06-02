from flask import Blueprint, request, session, render_template, redirect, url_for, jsonify
import logging
from flask import jsonify

from manifold_web.routes.auth import get_authenticated_email
from manifold_core.plugins.autotask.core import get_ticket, extract_udf, update_ticket_udf
from manifold_core.plugins.slack.api import SlackAPI
from manifold_core.plugins.slack.core import get_slack_name


flows_bp = Blueprint("flows", __name__, url_prefix="/flows")
logger = logging.getLogger(__name__)

@flows_bp.route("/livelink/<int:integration_id>")
def livelink_preview(integration_id: int):
    email = session.get("user", {}).get("email")
    if not email:
        return redirect(url_for("auth.login", next=request.full_path))
    return render_template("flows/livelink_preview.html", integration_id=integration_id)


@flows_bp.route("/api/livelink/<int:integration_id>")
def api_livelink_preview(integration_id: int):
    email = session.get("user", {}).get("email")
    if not email:
        return jsonify({"error": "Unauthorized"}), 403

    # Grab values from the query string
    ticket_id = request.args.get("ticketID", type=int)
    ticket_number = request.args.get("ticketNumber")
    title = request.args.get("title", "")
    description = request.args.get("description", "")
    slack_id = request.args.get("slackID")

    # If anything critical is missing, bail early
    if not ticket_id or not ticket_number:
        return jsonify({"error": "Missing required ticket fields"}), 400

    ticket = {
        "id": ticket_id,
        "ticketNumber": ticket_number,
        "title": title,
        "description": description,
    }

    slack_error = None

    # If SlackID is not present, perform Slack lookup
    if not slack_id:
        try:
            slack = SlackAPI(get_slack_name())
            channel_name = ticket_number.lower().replace(".", "_")
            logger.debug(f"Looking up Slack channel: {channel_name}")

            channel_id = slack.get_channel_id_by_name(channel_name)

            if channel_id:
                slack_id = channel_id
                logger.debug(f"Found Slack channel ID: {channel_id}")

                # Attempt to update the Autotask UDF
                try:
                    update_ticket_udf(integration_id, ticket_id, "SlackID", slack_id)
                except Exception as e:
                    slack_error = f"SlackID found, but failed to update Autotask: {e}"
                    logger.exception("Failed to update Autotask ticket with SlackID")
            else:
                logger.warning(f"Slack channel not found: {channel_name}")

        except Exception as e:
            slack_error = f"Slack integration failed: {e}"
            logger.exception("Slack lookup failed")

    return jsonify({
        "ticket": ticket,
        "slack_id": slack_id,
        "slack_error": slack_error
    })