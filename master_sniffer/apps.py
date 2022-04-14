

from django.apps import AppConfig


TOKEN_AUTH = False

WEB_SERVER_URL = "https://pawpharos.com/"
RESPONSE_QUEUE = None
WEB_REQUEST_QUEUE = None
SNIFFER_CONFIG = None


class SnifferConfig(AppConfig):
    name='master_sniffer'

