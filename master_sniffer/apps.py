from django.apps import AppConfig


TOKEN_AUTH = False

WEB_SERVER_URL = "https://pawpharos.com/"
RESPONSE_QUEUE = None
WEB_REQUEST_QUEUE = None
SNIFFER_CONFIG = None


class SnifferConfig(AppConfig):
    name='master_sniffer'

    def ready(self):
        from master_sniffer.server import WebUpdateHandler, DiscoveryHandler, SnifferDiscovery
        from queue import Queue

        global WEB_SERVER_URL, RESPONSE_QUEUE, WEB_REQUEST_QUEUE, SNIFFER_CONFIG
        RESPONSE_QUEUE = Queue()
        WEB_REQUEST_QUEUE = Queue()
        SNIFFER_CONFIG = Config()

        def initialize_threads():
            web_handler = WebUpdateHandler(WEB_REQUEST_QUEUE)
            discovery_handler = DiscoveryHandler(RESPONSE_QUEUE)
            discovery_server = SnifferDiscovery(RESPONSE_QUEUE)

            web_handler.start()
            discovery_server.start()
            discovery_handler.start()

        initialize_threads()
        # Check to see if we have an auth token stored
        global TOKEN_AUTH
        TOKEN_AUTH = SNIFFER_CONFIG.credentials[1] is not None
