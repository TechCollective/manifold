import os
from flask import Blueprint, render_template, session, redirect, url_for
from manifold_web.routes.auth import login_required, AUTH_MODE
dashboard_bp = Blueprint("dashboard", __name__)

#USE_AUTH = os.getenv("MANIFOLD_AUTH_BACKEND", "jumpcloud") != "none"

@dashboard_bp.route("/")
@login_required
def index():
    return render_template("index.html")

@dashboard_bp.route("/dashboard")
@login_required
def home():
    user = session.get("user", {"name": "dev", "email": "dev@localhost"})
    auth_enabled = AUTH_MODE == "JUMPCLOUD_AUTH"
    return render_template("dashboard.html", user=user, auth_enabled=auth_enabled)
