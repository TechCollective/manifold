import os
from flask import Blueprint, render_template, session, redirect, url_for

dashboard_bp = Blueprint("dashboard", __name__)

USE_AUTH = os.getenv("MANIFOLD_AUTH_BACKEND", "jumpcloud") != "none"

@dashboard_bp.route("/")
def index():
    return render_template("index.html")

@dashboard_bp.route("/dashboard")
def home():
    if USE_AUTH and "user" not in session:
        return redirect(url_for("auth.login"))
    user = session.get("user", {"name": "dev", "email": "dev@localhost"})
    return render_template("dashboard.html", user=user, auth_enabled=USE_AUTH)
