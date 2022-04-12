from django.apps import AppConfig
from master_sniffer.server import SnifferDiscovery, DiscoveryHandler
from queue import Queue
from master_sniffer.config import Config

WEB_REQUEST_QUEUE = Queue(maxsize=-1)
SNIFFER_CONFIG = Config()

TOKEN_AUTH = False

class SnifferConfig(AppConfig):
    name='master_sniffer'

    def ready(self):
        handler = DiscoveryHandler()
        handler.start()
        # Start the discovery server
        srv = SnifferDiscovery()
        srv.start()

        # Check to see if we have an auth token stored
        global TOKEN_AUTH
        TOKEN_AUTH = SNIFFER_CONFIG.credentials[1] is not None


