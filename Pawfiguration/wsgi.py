"""
WSGI config for Pawfiguration project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
import signal

import Pawfiguration

#signal.signal(signal.SIGTERM, Pawfiguration.request_handler.stop)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Pawfiguration.settings')

application = get_wsgi_application()
