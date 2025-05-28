import pkgutil
import manifold_core.plugins
from flask import Blueprint, jsonify

integrations_bp = Blueprint("integration", __name__, url_prefix="/integrations")

@integrations_bp.route("/available")
def available_integrations():
    plugins = [
        module.name
        for module in pkgutil.iter_modules(manifold_core.plugins.__path__)
        if not module.name.startswith("_")
    ]
    return jsonify(sorted(plugins))
