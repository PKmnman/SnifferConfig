
import re
import subprocess as sp
import logging
from enum import Enum
from typing import Any, Iterable, Union, Optional, Mapping
from time import sleep
from collections import namedtuple

__logger__ = logging.getLogger('root')

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


class NetworkCommandError(Exception):

    def __init__(self, msg: str = "Network configuration command failed!!", *args):
        super(NetworkCommandError, self).__init__(msg.format(*args))


def wpa_run(command: str, *args: str, interface='wlxe84e0650603f'):
    if command == '':
        raise ValueError('wpa_cli command cannot be empty!!')

    wpa_cmd = f"wpa_cli -i {interface} {command} {' '.join(args)}"

    try:
        proc = sp.run(wpa_cmd, text=True, shell=True, executable='/bin/bash', capture_output=True, check=True)
    except sp.CalledProcessError as err:
        raise NetworkCommandError('Failed to execute wpa_cli command: %s', wpa_cmd[8:]) from err

    return proc.stdout


def has_field(field: str, dictionary: dict[str, Any]):
    return field in dictionary


def _quote_str(val: str) -> str:
    return f"\"{val}\""


def parse_flags(flag_str: str) -> set:
    flags = set()
    flag_re = re.compile(r"\[(?P<flag>[^\]\[]+)]")
    for flag in flag_re.finditer(flag_str):
        # Check that the flag is empty (just to be safe)
        if flag['flag'] is not None:
            flag_data = flag['flag']
            flags.add(flag_data)

    return flags


def parse_scan(scan: str, configured_ssids: Iterable[str] = ()) -> list[Iterable]:
    # This is a named tuple used to hold the individual scan results
    ScanResult = namedtuple('ScanResult', ['ssid', 'frequency', 'signal_level', 'flags'])
    results = scan.splitlines()[1:]
    # This will be the list of scanned networks that are returned
    networks = []

    for l in results:
        fields = l.split()
        if len(fields) < 5:
            continue

        # Store fields
        ssid = fields[4]
        freq = fields[1]
        signal_level = fields[2]
        # Parse Flags
        flags = parse_flags(fields[3])

        networks.append(ScanResult(ssid, freq, signal_level, flags))

    return networks


class NetworkArgs:
    """
    Just a namespace class for processing network profile arguments
    """

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
        return _quote_str(self._ssid)

    @property
    def password(self) -> str:
        if self.key_mgmt == KeyManagement.WPA_EAP and hasattr(self, '_password'):
            return _quote_str(self._password)
        elif self.key_mgmt == KeyManagement.WPA_PSK:
            return _quote_str(self._psk)

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


def list_networks() -> list[Mapping[str, Any]]:
    result = wpa_run('list_networks')

    networks = []

    # Parse the output into a list of tuples
    output = map(lambda line: tuple(line.split()),result.splitlines()[1:])

    # Convert the 2D array into a list of dictionaries
    for net in output:
        network = {
            "id": net[0],
            "ssid": net[1],
            "bssid": net[2],
            "flags": set(),
            "saved": True
        }
        if len(net) > 3:
            network['flags'] = parse_flags(net[3])

        networks.append(network)

    return networks


async def scan_networks():
    """Scans and returns a list of available wi-fi networks"""
    command = 'scan'
    try:
        # Start scanning
        __logger__.info(f"Running network configuration command: %s", command)
        result = wpa_run(command)
        __logger__.debug('Output from command: %s', result)

        # Wait for the results to populate before running retrieval command
        __logger__.info("Waiting for scan results...")
        sleep(5)
        command = 'scan_results'

        # Get scan results
        __logger__.info(f"Running network configuration command: %s", command)
        result = wpa_run(command)
        __logger__.debug('Output from command: %s', result)

    except NetworkCommandError as err:
        __logger__.error("Failed to execute %s command!!", command, exc_info=err)
        raise RuntimeError() from err
    return parse_scan(result)


def save_config():
    # Have wpa_supplicant save it's config
    wpa_run('save_config')
    sleep(3)
    # Force wpa_supplicant to re-read it's config file
    wpa_run('reconfigure')


def add_network(profile):
    # TODO: Implement function to add a network profile

    raise NotImplementedError()

    # Check the type of the passed profile

    ## If it's a dict, try converting it to a Network object

