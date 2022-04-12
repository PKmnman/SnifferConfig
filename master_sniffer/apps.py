from django.apps import AppConfig
from master_sniffer.server import SnifferDiscovery, device_discovered, DiscoveryHandler


class SnifferConfig(AppConfig):
    name='master_sniffer'

    def ready(self):
        handler = DiscoveryHandler()
        handler.start()
        # Start the discovery server
        srv = SnifferDiscovery(device_discovered)
        srv.start()

