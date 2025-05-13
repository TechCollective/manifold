import os
from flask import Flask
from flask_session import Session
from flask_session.sessions import FileSystemSessionInterface
from authlib.integrations.flask_client import OAuth

from manifold_web.routes.auth import auth_bp
from manifold_web.routes.dashboard import dashboard_bp
from manifold_web.plugins.unifi.routes import unifi_bp

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
    session_dir = os.getenv("SESSION_FILE_DIR", "/opt/manifold/flask_session")
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
        client_id=os.getenv("OIDC_CLIENT_ID"),
        client_secret=os.getenv("OIDC_CLIENT_SECRET"),
        server_metadata_url="https://oauth.id.jumpcloud.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )
    app.oauth = oauth

    # Register routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(unifi_bp)
    
    return app