import os
from flask import Flask
from flask_session import Session
from flask_session.sessions import FileSystemSessionInterface
from authlib.integrations.flask_client import OAuth

from manifold_web.routes.auth import auth_bp
from manifold_web.routes.dashboard import dashboard_bp
from manifold_web.plugins.unifi.routes import unifi_bp
from manifold_web.plugins.slack.routes import slack_bp
from manifold_web.plugins.autotask.routes import autotask_bp
from manifold_web.routes.integrations import integrations_bp
from manifold_web.flows.route import flows_bp

from manifold_core.secrets.bitwarden.backend import Backend

from dotenv import load_dotenv
load_dotenv()


class PatchedFileSystemSessionInterface(FileSystemSessionInterface):
    def save_session(self, app, session, response):
        session_id = session.sid
        if isinstance(session_id, bytes):
            session_id = session_id.decode("utf-8")
        response.set_cookie(app.config["SESSION_COOKIE_NAME"], session_id)
        super().save_session(app, session, response)

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

    # File-based session configuration
    session_dir = os.getenv("SESSION_DIR", "/opt/manifold/sessions")

    os.makedirs(session_dir, exist_ok=True)
    app.config.update(
        SESSION_TYPE="filesystem",
        SESSION_FILE_DIR=session_dir,
        SESSION_PERMANENT=False,
        SESSION_COOKIE_NAME="manifold_session",
    )
    app.session_interface = PatchedFileSystemSessionInterface(
        cache_dir=session_dir,
        threshold=500,
        mode=0o600,
        key_prefix=""
    )
    Session(app)

    # Configure OIDC with JumpCloud's oauth.id domain
    oauth = OAuth(app)
    oauth.register(
        name="jumpcloud",
        client_id = Backend().get_secret("OIDC_CLIENT_ID"),
        client_secret=Backend().get_secret("OIDC_CLIENT_SECRET"),
        server_metadata_url="https://oauth.id.jumpcloud.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )
    app.oauth = oauth

    # Register routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(unifi_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(slack_bp)
    app.register_blueprint(autotask_bp)
    app.register_blueprint(flows_bp)
    
    from manifold_core.plugins.unifi.servers import list_unifi_servers
    from manifold_core.plugins.slack.core import list_slack_integrations
    from manifold_core.plugins.autotask.core import list_autotask_integrations

    @app.context_processor
    def inject_integrations():
        integrations = {}

        try:
            if list_unifi_servers():
                integrations["unifi"] = list_unifi_servers()
        except Exception:
            pass

        try:
            if list_slack_integrations():
                integrations["slack"] = list_slack_integrations()
        except Exception:
            pass

        try:
            if list_autotask_integrations():
                integrations["autotask"] = list_autotask_integrations()
        except Exception:
            pass

        return {
            "active_integrations": sorted(integrations.keys()),
            **{f"{k}_integrations": v for k, v in integrations.items()}
        }
    
    
    return app