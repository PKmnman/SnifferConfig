import requests

import master_sniffer
import pawfig.forms as forms
import logging


from django.http import HttpRequest, HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect

from pawfig.models import Device
from pawfig.helpers.network_utils import list_networks

from master_sniffer.apps import SNIFFER_CONFIG


LOGGER = logging.getLogger('root')

## Homepage view
def index(request):
    assert isinstance(request, HttpRequest)
    if SNIFFER_CONFIG.credentials[1] is None:
        return redirect('login')

    return render(request, "index.html",
                  context={
                      "title": "Pawpharos Configuration"
                  })

def login(request: HttpRequest):
    if request.method == "GET":
        return render(request, "login.html",
                      context={
                          "title": "Pawpharos Configuration - Login",
                          "form": forms.LoginForm
                      })
    elif request.method == "POST":
        data = {}
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            SNIFFER_CONFIG.credentials = form.cleaned_data['username'], form.get_token()
            SNIFFER_CONFIG.save()
        resp = requests.post(
            url=master_sniffer.WEB_SERVER_URL + 'api-token-auth/',
            data=data
        )


## Returns a list of registered Wifi Networks
def list_wifi(request):
    # Only supported when running in a Linux environment
    if request.method == "GET":
        networks = []
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



def test_index(request):
    return render(request, 'test/index.html', {})