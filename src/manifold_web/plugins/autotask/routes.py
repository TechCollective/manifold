from flask import Blueprint, render_template, request, redirect, flash, url_for
from manifold_core.plugins.autotask.core import (
    list_autotask_integrations,
    add_autotask_integration,
    edit_autotask_integration,
    delete_autotask_integration,
    set_autotask_credentials,
)
from manifold_web.utils.integration_config import get_integration_config

autotask_bp = Blueprint("autotask", __name__, url_prefix="/autotask", template_folder="templates")

@autotask_bp.route("/")
def index():
    integrations = list_autotask_integrations()
    config = get_integration_config('autotask')
    context = config.get_template_context(integrations)
    return render_template("integration_base.html", **context)


@autotask_bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        api_url = request.form["api_url"]
        username = request.form["username"]
        integration_code = request.form["integration_code"]
        secret = request.form["secret"]

        try:
            record = add_autotask_integration(name=name, api_url=api_url)
            set_autotask_credentials(
                autotask_id=record.id,
                username=username,
                integration_code=integration_code,
                secret=secret,
            )
            flash("Autotask integration added successfully.", "success")
            return redirect(url_for("autotask.index"))
        except Exception as e:
            flash(f"Failed to add integration: {e}", "danger")

    return render_template("autotask_add.html")


@autotask_bp.route("/delete/<int:integration_id>", methods=["POST"])
def delete(integration_id):
    try:
        delete_autotask_integration(integration_id)
        flash("Autotask integration deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting integration: {e}", "danger")
    return redirect(url_for("autotask.index"))
