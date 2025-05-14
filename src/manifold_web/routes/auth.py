from flask import Blueprint, redirect, url_for, session, current_app, request
import os
import logging
logging.basicConfig(level=logging.DEBUG)

AUTH_MODE = os.getenv("AUTH_MODE", "JUMPCLOUD_AUTH")

auth_bp = Blueprint("auth", __name__)

def login_required(view_func):
    """Decorator that enforces login only if AUTH_MODE is set to JUMPCLOUD_AUTH"""
    def wrapped_view(*args, **kwargs):
        if AUTH_MODE == "NO_AUTH":
            return view_func(*args, **kwargs)
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return view_func(*args, **kwargs)
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view


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