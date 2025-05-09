import os
from flask import Flask
from flask_session import Session

from manifold_web.routes.dashboard import dashboard_bp
from manifold_web.plugins.unifi.routes import unifi_bp

from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")
    app.config["SESSION_TYPE"] = "filesystem"

    Session(app)

    # Only register auth routes if needed
    auth_backend = os.getenv("MANIFOLD_AUTH_BACKEND", "jumpcloud")

    if auth_backend != "none":
        from manifold_web.auth_jumpcloud import auth_bp, init_oauth
        init_oauth(app)
        app.register_blueprint(auth_bp)

    app.register_blueprint(dashboard_bp)
    from manifold_web.plugins.unifi.routes import unifi_bp
    from manifold_web.plugins import unifi
    unifi.register_plugin(app)
       
    
    return app

