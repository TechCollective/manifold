from flask import Blueprint, render_template, request, redirect, flash
from manifold_core.plugins.slack.core import (
    list_slack_integrations,
    add_slack_integration,
    delete_slack_integration,
    set_slack_token,
)
from manifold_web.utils.integration_config import get_integration_config

slack_bp = Blueprint("slack", __name__, url_prefix="/slack", template_folder="templates")

@slack_bp.route("/")
def slack_index():
    integrations = list_slack_integrations()
    config = get_integration_config('slack')
    context = config.get_template_context(integrations)
    return render_template("integration_base.html", **context)


@slack_bp.route("/add", methods=["GET", "POST"])
def slack_add():
    if request.method == "POST":
        name = request.form["name"]
        workspace = request.form["workspace"]
        token = request.form["token"]
        try:
            record = add_slack_integration(name=name, workspace=workspace)
            set_slack_token(slack_id=record.id, token=token)
            flash("Slack integration added.", "success")
            return redirect("/slack")
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template("slack_add.html")

@slack_bp.route("/delete/<name>", methods=["POST"])
def slack_delete(name):
    try:
        delete_slack_integration(name)
        flash(f"Deleted {name}.", "success")
    except Exception as e:
        flash(f"Error deleting {name}: {e}", "danger")
    return redirect("/slack")
