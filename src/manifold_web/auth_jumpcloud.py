from authlib.integrations.flask_client import OAuth
from flask import Blueprint, redirect, url_for, session, request
import os

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name="jumpcloud",
        client_id=os.getenv("JUMPCLOUD_CLIENT_ID"),
        client_secret=os.getenv("JUMPCLOUD_CLIENT_SECRET"),
        server_metadata_url="https://console.jumpcloud.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

@auth_bp.route("/login")
def login():
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.jumpcloud.authorize_redirect(redirect_uri)

@auth_bp.route("/callback")
def callback():
    token = oauth.jumpcloud.authorize_access_token()
    user = oauth.jumpcloud.parse_id_token(token)
    session["user"] = user
    return redirect(url_for("dashboard.home"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
