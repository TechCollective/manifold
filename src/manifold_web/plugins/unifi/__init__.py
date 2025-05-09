def register_plugin(app):
    from .routes import unifi_bp
    app.register_blueprint(unifi_bp)