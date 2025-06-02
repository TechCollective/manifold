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
            return redirect(url_for('auth.login', next=request.url))
        return view_func(*args, **kwargs)
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view


@auth_bp.route("/login")
def login():
    redirect_uri = url_for("auth.callback", _external=True)
    next_url = request.args.get("next", "/")
    session["next_url"] = next_url  # Save for after auth
    print(f"[DEBUG] Redirecting to JumpCloud with callback URI: {redirect_uri}")
    return current_app.oauth.jumpcloud.authorize_redirect(redirect_uri)


@auth_bp.route("/callback")
def callback():
    try:
        print("[DEBUG] /callback hit")
        token = current_app.oauth.jumpcloud.authorize_access_token()
        print(f"[DEBUG] Token: {token}")
        user_info = current_app.oauth.jumpcloud.userinfo(token=token)
        print(f"[DEBUG] User info: {user_info}")
        session["user"] = user_info

        # Redirect to the originally requested URL
        next_url = session.pop("next_url", url_for("dashboard.home"))
        return redirect(next_url)

    except Exception as e:
        print(f"[ERROR] Callback failed: {e}")
        return "Authentication failed", 500


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


def get_authenticated_email(session) -> str | None:
    """Returns the authenticated user's email from the session, or None if not logged in."""
    return session.get("user", {}).get("email")
