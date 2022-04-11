from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from master_sniffer.serializers import TrackingEventSerializer


@api_view(['GET', 'PUT'])
def list_events(request):
    if request.method == 'GET':
        pass

    elif request.method == 'PUT':
        serializer = TrackingEventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, content_type='application/json', status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)