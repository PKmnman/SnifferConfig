from django.apps import AppConfig

class SnifferConfig(AppConfig):
    name='master_sniffer'

    def ready(self):
        # Start the discovery server
        pass