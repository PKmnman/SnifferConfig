import re
from django.db import models
from django.core.validators import RegexValidator

# Create your models here.

mac_addr_pattern = re.compile(
    r"([\dA-Fa-f]{2})-([\dA-Fa-f]{2})-([\dA-Fa-f]{2})-([\dA-Fa-f]{2})-([\dA-Fa-f]{2})-([\dA-Fa-f]{2})",
    re.UNICODE
)

class Account(models.Model):
    username = models.CharField(max_length=64)
    token = models.CharField(max_length=128, unique=True)

class Device(models.Model):
    serial_num = models.SlugField(unique=True)
    address = models.GenericIPAddressField(protocol='IPv4')
    location = models.CharField(max_length=128)

class Beacon(models.Model):
    address = models.CharField(max_length=17,
                               validators=[
                                   RegexValidator(
                                       regex=mac_addr_pattern,
                                       message="Enter a valid MAC address"
                                   )
                               ])
    pet_name = models.CharField(max_length=64)



class TrackingUpdate(models.Model):
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING, to_field="serial_num")
    beacon = models.ForeignKey(Beacon, on_delete=models.DO_NOTHING)
    time_received = models.DateTimeField(verbose_name="Time Received")
    time_published = models.TimeField(verbose_name="Time Published")
    pushed_to_server = models.BooleanField(default=False)
