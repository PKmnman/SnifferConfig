from django.apps import AppConfig
from master_sniffer.models import Device
from master_sniffer.server import SnifferDiscovery


def device_discovered(thread: SnifferDiscovery, data: bytes, addr: tuple[str, int]):
    if not Device.objects.filter(address=addr[0]).exists():
        # TODO: Decode response data
        # TODO: Check if we have a device with the same serial code, if so, update the address and return
        # TODO: Else, add the device to the registry
        pass


class SnifferConfig(AppConfig):
    name='master_sniffer'

    def ready(self):
        # Start the discovery server
        srv = SnifferDiscovery(device_discovered)
        srv.start()

