import django.forms as forms

class NetworkForm(forms.Form):

    KEY_MANAGEMENT_CHOICES = [
        ('OPEN', "None"),
        ('WPA-PSK', 'WPA/WPA2-Personal'),
        ('WPA-EAP', 'WPA3-Enterprise')
    ]

    EAP_METHOD_CHOICES = [
        ('PEAP', 'PEAP'),
        ('TLS', 'TLS'),
        ('TTLS', 'TTLS')
    ]

    PHASE2_AUTH_CHOICES = [
        ('MSCHAPV2', 'MSCHAPv2'),
        ('GTC', 'GTC')
    ]

    template_name = 'wifi/network-form.html'

    ssid = forms.SlugField(required=True,
                           label='SSID',
                           widget=forms.TextInput({
                               'class': 'form-control'
                           }))

    key_mgmt = forms.ChoiceField(
        required=True,
        label="Security",
        choices=KEY_MANAGEMENT_CHOICES,
        widget=forms.Select({
            'class': 'form-select'
        })
    )

    ## WPA-PSK Fields
    psk = forms.CharField(
        required=False,
        label="Password",
        widget=forms.TextInput({
            'class': 'form-control wpa-personal',
            'type': 'password',
            'placeholder': 'Enter password'
        })
    )

    ## WPA/WPA2/WPA3-Enterprise

    eap_method = forms.ChoiceField(
        required=False,
        label="EAP method",
        choices=EAP_METHOD_CHOICES,
        widget=forms.Select({
            'class': 'form-select wpa-enterprise'
        })
    )

    ca_cert = forms.ChoiceField(
        required=False,
        label="CA certificate",
        choices=[(None, 'Not Supported')]
    )

    ## PEAP Phase2

    def sample(self):
        self.render('wifi/network-form.html', context={ 'form': self })




