import pawfig.forms as forms
import logging
import json
import re

from django.http import HttpRequest, HttpResponse, Http404, JsonResponse
from django.shortcuts import render

from pawfig.models import Device
from pawfig.helpers.network_utils import list_networks



LOGGER = logging.getLogger('root')

## Homepage view
def index(request):
    assert isinstance(request, HttpRequest)

    return render(request, "index.html",
                  context={
                      "title": "Pawpharos Configuration"
                  })

## Returns a list of registered Wifi Networks
def list_wifi(request):
    # Only supported when running in a Linux environment
    if request.method == "GET":
        networks = []
        """
        shell = ['/bin/bash']
        command = ['-c', 'wpa_cli list_networks']
        
        shell.extend(command)

        LOGGER.info("Executing shell command: wpa_cli list_networks")
        result = run(shell, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        output = result.stdout
        LOGGER.info("Return code = %d", result.returncode)
        LOGGER.info("Command output: %s", output)
        LOGGER.info("Command error: %s", result.stderr)
        # Parse output
        lines = re.split(r'\n|\n\r', output)[2:]
        LOGGER.info(f"Found {len(lines)} network profiles...")
        for line in lines:
            fields = re.split(r'[^\n\S]+', line)
            if len(fields) < 3:
                continue
            network = {
                "id": fields[0],
                "ssid": fields[1],
                "bssid": fields[2],
                "flags": None
            }

            if len(fields) > 3:
                network["flags"] = fields[3]
            # Store to list of networks
            networks.append(network)
        """
        return render(request, "wifi_list.html", status=200,
                      context={ "network_list": networks})

    return Http404()

def get_networks(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        return JsonResponse(list_networks(), safe=False)

def networks(request: HttpRequest, action: str):
    if request.method == 'POST':

        if action == 'add':
            # add the given network to wpa_supplicant
            return Http404('Not implemented')
        elif action == 'del':
            # Forget the given network ssid
            return Http404('Not implemented')

    return Http404('Invalid request method')

def devices(request):
    return render(request,
                  template_name='devices.html',
                  context={
                      'devices': Device.objects.all()
                  })

def account(request: HttpRequest):
    if request.method == 'GET':
        return render(request, 'wifi/network-form.html', context={'form': forms.NetworkForm()})



def test(request, sniffer_serial):
    return render(request, 'test/room.html', {'room_name': sniffer_serial})


def test_index(request):
    return render(request, 'test/index.html', {})