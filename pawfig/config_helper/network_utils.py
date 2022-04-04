
import re
from logging import getLogger
from enum import Enum
from subprocess import run, PIPE, STDOUT
from typing import Any, Iterable, Union, Optional, Mapping
from time import sleep

class KeyManagement(Enum):
    WPA_PSK = 'WPA-PSK'
    WPA_EAP = 'WPA-EAP'
    IEEE8021X = 'IEEE8021X'

class EapMethod(Enum):
    MD5 = 'MD5'
    MSCHAPv2 = 'MSCHAPv2'
    OTP = 'OTP'
    GTC = 'GTC'
    TLS = 'TLS'
    PEAP = 'PEAP'
    TTLS = 'TTLS'
    FAST = 'FAST'


def has_field(field: str, dictionary: dict[str, Any]):
    return field in dictionary

def quote_str(val):
    return f"\"{val}\""

class NetworkArgs:
    """
    Just a namespace class for processing network profile arguments
    """
    __logger__ = getLogger('root')

    @classmethod
    def create_args(cls, **kwargs):
        # Return None if given no arguments
        if len(kwargs.keys()) < 1:
            return None

        args = cls()
        args.__dict__ = kwargs
        return args


    # Used to validate attributes against required arguments
    def validate(self, arg1, *required):
        # Convert to a list to append first argument
        list_required = list(required)
        list_required.insert(0, arg1)
        # Check for missing arguments
        for argument in list_required:
            if not hasattr(self, argument):
                return False
        return True


class Network:
    """
    A class representing a network profile entered by a user.
    ----------
    ssid : str
        The ssid of the network
    key_mgmt : KeyManagement
        The type of key management used in authentication
    """

    __logger__ = getLogger('root')

    _ssid: str
    _key_mgmt: KeyManagement = KeyManagement.WPA_PSK
    _scan_ssid: Optional[bool] = None

    _psk: Optional[str] = None

    _eap: Optional[set[EapMethod]] = None

    _identity: Optional[str] = None
    _password: Optional[str] = None
    _ca_cert: Optional[str] = None

    _phase2_auth: Optional[str] = None

    @staticmethod
    def __validate_params(*params: Iterable[str], args: dict[str, Any]):
        return all(map(lambda x: has_field(x, args), params))


    def __init__(self, ssid: str, **kwargs):
        """
        Creates a new Network object. Depending on the value of the key_mgmt keyword argument, which keyword arguments
        are required change. By default, it is set to ``KeyManagement.WPA_PSK``, which causes the constructor to
        require ``psk`` as a keyword argument.

        :param ssid: The ssid of the network.
        :param kwargs: A list of profile attributes.
        """
        args = NetworkArgs.create_args(**kwargs)

        self._ssid = ssid
        if hasattr(args, 'key_mgmt'):
            self._key_mgmt = args.key_mgmt
            kwargs.pop('key_mgmt')

        self._scan_ssid = None

        if self.key_mgmt == KeyManagement.WPA_PSK:
            if not args.validate('psk'):
                raise RuntimeError('Missing required argument for WPA_PSK key management: \'psk\'')

            self._psk = args.psk
            kwargs.pop('psk')

        elif self.key_mgmt == KeyManagement.WPA_EAP:
            # Check that all the params we need are defined
            if not Network.__validate_params('identity', 'password', 'eap', args=kwargs):
                raise RuntimeError('Missing required argument(s) for WPA_EAP key management: %s', ', '.join(
                    filter(
                        lambda x: x not in kwargs, ('identity', 'password', 'eap')
                    )
                ))

            self._eap = args.eap

            self._identity = args.identity

            if self.eap == EapMethod.PEAP and args.validate('phase2_auth'):
                self._phase2_auth = args.phase2_auth


            self._password = args.password

        else:
            raise NotImplementedError("Unsupported key management type!!")

        self.__logger__.info("Created network profile: %s", self._ssid)


    @property
    def ssid(self) -> str:
        # Surround the ssid in quotes before returning it
        return quote_str(self._ssid)

    @property
    def password(self) -> str:
        if self.key_mgmt == KeyManagement.WPA_EAP and hasattr(self, '_password'):
            return quote_str(self._password)
        elif self.key_mgmt == KeyManagement.WPA_PSK:
            return quote_str(self._psk)

    @property
    def key_mgmt(self) -> KeyManagement:
        return self._key_mgmt

    @property
    def scan_ssid(self) -> Union[bool, None]:
        if hasattr(self, '_scan_ssid'):
            return self._scan_ssid
        return None

    @property
    def eap(self):
        if self.key_mgmt == KeyManagement.WPA_EAP and hasattr(self, '_eap'):
            return self._eap
        return None

    @property
    def phase2_auth(self):
        if self.eap == "PEAP" and hasattr(self, '_phase2'):
            return self._phase2
        return None

    def __str__(self):
        initial_base = "network={\nssid=%s\nkey_mgmt=%s\n".format(self.ssid, self.key_mgmt.value)
        if self.scan_ssid is not None:
            initial_base = initial_base + f"scan_ssid={self.scan_ssid}"

        if self.key_mgmt == KeyManagement.WPA_PSK:
            initial_base = (initial_base + "psk=%s\n").format(self.password)
        elif self.key_mgmt == KeyManagement.WPA_EAP:
            initial_base = (initial_base + "eap=%s\n").format(self.eap)


def get_cmd(*cmd):
    result = ['/etc/bash', '-c']
    result.extend(*cmd)
    return result


class NetworkManager:

    __logger__ = getLogger('root')
    __scan_results = None

    network_profiles = []

    # Scans for wi-fi networks and returns a list of ssid's and strengths
    async def scan_networks(self):
        command = get_cmd('wpa_cli scan')

        self.__logger__.info(f"Running network configuration command: {' '.join(command[2:])}")
        result = run(command, text=True, stdout=PIPE, stderr=STDOUT)
        if result.returncode != 0:
            self.__logger__.error("Command returned %s: %s", result.returncode, result.stderr)

        self.__logger__.debug('Output from command: %s', result.stdout)

        # Wait for the results to populate before running retrieval command
        self.__logger__.info("Waiting for scan results...")
        sleep(5)

        # Get scan results
        command = get_cmd('wpa_cli scan_results')
        self.__logger__.info(f"Running network configuration command: %s", " ".join(command[2:]))
        result = run(command, text=True, stdout=PIPE, stderr=STDOUT)
        self.__logger__.debug('Output from command: %s', result.stdout)

        # TODO: Parse out SSID (and optionally signal strength) from the command output

        ## Return a list of JSON-like objects (ssid & signal_strength)


    def add_network(self, profile: Union[Network, dict]):
        # TODO: Implement function to add a network profile
        raise NotImplementedError()

        # Check the type of the passed profile

        ## If it's a dict, try converting it to a Network object


    def save_config(self):
        # TODO: Have wpa_supplicant save it's config
        raise NotImplementedError()


    def list_networks(self) -> list[Mapping[str, Any]]:
        command = get_cmd('wpa_cli list_networks')
        result = run(command, text=True, stdout=PIPE, stderr=STDOUT)

        # Parse the output into a list of tuples
        output = map(lambda line: tuple(line.split()),result.stdout.splitlines()[2:])
        networks = []

        # Convert the 2D array into a list of dictionaries
        for net in output:
            if len(net) < 3:
                continue

            network = {
                "id": net[0],
                "ssid": net[1],
                "bssid": net[2],
                "flags": None,
                "saved": True
            }

            if network in self.network_profiles:
                pass

            if len(net) > 3:
                network['flags'] = net[3]

            networks.append(network)

        return networks
