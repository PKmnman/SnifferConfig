import logging
import subprocess
import sys
import re

import django.http
from django.http import HttpRequest, HttpResponse, Http404, JsonResponse
from django.shortcuts import render

from platform import system
from subprocess import run, Popen, PIPE

from pawfig.models import Device

LOGGER = logging.getLogger('root')

## Homepage view
def index(request):
    assert isinstance(request, HttpRequest)

    return render(request, "index.html",
                  context={
                      "title": "Pawpharos Configuration"
                  })

## Debug view for testing purposes
def run_cmd(request, cmd: str):
    assert isinstance(request, HttpRequest)

    if system() == 'Windows':
        arguments = re.findall(r'[^\s"\']+|"[^"]+"|\'[^\']+\'', cmd)
        print(arguments)
        val = run(cmd, shell=True, capture_output=True)
        output = val.stdout.decode('utf-8')

        return JsonResponse({"command": cmd, "output": output})

    elif system() == 'Linux':
        exec = '/bin/bash'
        arguments = re.split(r'[^\s"\']+|"[^"]+"|\'[^\']+\'', cmd)

        print(arguments)
        output = None
        with Popen(executable=exec, args=arguments, stdout=PIPE) as proc:
            output = proc.stdout.read()
            print(output)

        return JsonResponse({"command": cmd, "output": output})

    return Http404()

## Returns a list of registered Wifi Networks
def list_wifi(request):
    # Only supported when running in a Linux environment
    if request.method == "GET":
        shell = ['/bin/bash']
        command = ['-c', 'wpa_cli list_networks']
        networks = []
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

        return render(request, "wifi_list.html", status=200,
                      context={ "network_list": networks})

    return Http404()


def devices(request):
    return render(request,
                  template_name='devices.html',
                  context={
                      'devices': Device.objects.all()
                  })

def test(request, sniffer_serial):
    return render(request, 'test/room.html', {'room_name': sniffer_serial})


def test_index(request):
    return render(request, 'test/index.html', {})