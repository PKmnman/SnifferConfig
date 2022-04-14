import logging

from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from master_sniffer.serializers import TrackingEventSerializer
from master_sniffer.models import TrackingEvent
from master_sniffer.apps import WEB_SERVER_URL
from Pawfiguration import REQUEST_QUEUE
from requests import Request
from datetime import timedelta

@api_view(['GET', 'PUT'])
def list_events(request):

    if request.method == 'GET':
        return JsonResponse(data={"status": status.HTTP_501_NOT_IMPLEMENTED},status=status.HTTP_501_NOT_IMPLEMENTED)

    elif request.method == 'PUT':
        logging.info('Received tracking event!!')
        serializer = TrackingEventSerializer(data=request.data)
        if serializer.is_valid():

            #sniffer_query = Device.objects.filter(serial_num = event.sniffer_serial, active=True)

            # Make sure we don't receive repeat request
            prev_event = TrackingEvent.objects\
                .filter(beacon_addr=serializer.validated_data['beacon_addr'])\
                .order_by('event_time')[0]

            if all([prev_event.sniffer_serial == serializer.validated_data['sniffer_serial'],
                    (serializer.validated_data['event_time'] - prev_event.event_time) < timedelta(minutes=5)]):
                event = serializer.create(serializer.validated_data)
                logging.info('Tracking event from %s created! Beacon MAC %s detected.', event.sniffer_serial, event.beacon_addr)
                event.save()
                req = Request(
                    method='POST',
                    url=WEB_SERVER_URL,
                    json= {
                        'sniffer_serial': event.sniffer_serial,
                        'beacon_addr': event.beacon_addr,
                        'event_time': event.event_time,
                        'rssi': event.rssi
                    }
                )
                logging.info('Update request added to queue.')
                # Then queue this event to get pushed to the webserver
                REQUEST_QUEUE.put_nowait(req)
                return JsonResponse(serializer.data, content_type='application/json', status=status.HTTP_201_CREATED)
            else:
                logging.info('Duplicate event detected, ignoring!')
                return JsonResponse(serializer.data, status=status.HTTP_208_ALREADY_REPORTED)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)