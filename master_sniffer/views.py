from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from master_sniffer.serializers import TrackingEventSerializer
from master_sniffer.models import Device
from master_sniffer.apps import WEB_REQUEST_QUEUE, WEB_SERVER_URL
from requests import Request

@api_view(['GET', 'PUT'])
def list_events(request):

    if request.method == 'GET':
        return JsonResponse(data={"status": status.HTTP_501_NOT_IMPLEMENTED},status=status.HTTP_501_NOT_IMPLEMENTED)

    elif request.method == 'PUT':
        serializer = TrackingEventSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.create(serializer.validated_data)
            sniffer_query = Device.objects.filter(serial_num = event.sniffer_serial, active=True)
            # Check that the sniffer is registered and active
            if sniffer_query.exists():
                event.save()
                req = Request()
                req.url = WEB_SERVER_URL
                req.json = {
                    'sniffer_serial': event.sniffer_serial,
                    'beacon_addr': event.beacon_addr,
                    'event_time': event.event_time,
                    'rssi': event.rssi
                }

                # Then queue this event to get pushed to the webserver
                WEB_REQUEST_QUEUE.put_nowait(req)
            return JsonResponse(serializer.data, content_type='application/json', status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)