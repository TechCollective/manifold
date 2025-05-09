# manifold_core/plugins/unifi/api.py

from unifi.controller import Controller
from manifold_core.plugins.unifi.models import UnifiServer
from manifold_core.secrets.get import get_secret_backend


class UniFiAPI:
    def __init__(self, server: UnifiServer):
        self.server = server
        self.controller = None
        self.secrets = get_secret_backend()

    def _get_credentials(self):
        username = self.secrets.get_secret(f"unifi:{self.server.name}:username")
        password = self.secrets.get_secret(f"unifi:{self.server.name}:password")
        return username, password

    def connect(self):
        username, password = self._get_credentials()
        self.controller = Controller(
            host=self.server.host,
            username=username,
            password=password,
            port=self.server.port,
            ssl_verify=False,
        )
        self.controller.login()

    def get_version(self):
        if not self.controller:
            self.connect()
        return self.controller.get_controller_version()

    def is_unifi_os(self):
        version = self.get_version()
        return "/proxy/network" in self.controller.baseurl

    # Example future method
    def get_sites(self):
        if not self.controller:
            self.connect()
        return self.controller.get_sites()
