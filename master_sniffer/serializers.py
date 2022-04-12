from rest_framework import serializers
from master_sniffer.models import TrackingEvent

class TrackingEventSerializer(serializers.Serializer):

    sniffer_serial = serializers.SlugField(required=True)
    beacon_addr = serializers.CharField(required=True, allow_blank=False)
    event_time = serializers.DateTimeField(format="%m-%d-%y %H:%M:%S.%f", required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        return TrackingEvent.objects.create(**validated_data)

