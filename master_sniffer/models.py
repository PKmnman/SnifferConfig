from django.db import models

class TrackingEvent(models.Model):
    sniffer_serial = models.SlugField()

class Device(models.Model):
    serial_num = models.SlugField(unique=True)
    address = models.GenericIPAddressField(protocol='IPv4')
    location = models.CharField(max_length=128, default="")
    active = models.BooleanField(default=False)