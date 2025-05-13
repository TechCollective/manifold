from flask import Blueprint, redirect, url_for, session, current_app
import os
import logging
logging.basicConfig(level=logging.DEBUG)


auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    redirect_uri = "https://manifold.techcollective.com/callback"
    print(f"[DEBUG] Using redirect URI: {redirect_uri}")
    return current_app.oauth.jumpcloud.authorize_redirect(redirect_uri)

@auth_bp.route("/callback")
def callback():
    print("[DEBUG] /callback hit")
    token = current_app.oauth.jumpcloud.authorize_access_token()
    user_info = current_app.oauth.jumpcloud.userinfo(token=token)
    session["user"] = user_info
    return redirect(url_for("dashboard.home"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")