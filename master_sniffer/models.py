from django.db import models

class TrackingEvent(models.Model):
    app_label="master_sniffer"
    sniffer_serial = models.SlugField()
    beacon_addr = models.CharField(max_length=120)
    event_time = models.DateTimeField()
    rssi = models.IntegerField()

    class Meta:
        ordering = ['-event_time']


class Device(models.Model):
    app_label = "master_sniffer"
    serial_num = models.SlugField(unique=True)
    address = models.GenericIPAddressField(protocol='IPv4')
    location = models.CharField(max_length=128, default="")
    active = models.BooleanField(default=False)