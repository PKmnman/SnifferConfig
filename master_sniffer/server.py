#import fcntl
import socket
import logging
import struct
import threading
import time
import re
import queue

import requests

from master_sniffer.models import Device

RESPONSE_QUEUE = queue.Queue()

class SnifferDiscovery(threading.Thread):

    SEARCH_INTERVAL = 5
    BROADCAST_IP = '239.255.255.250'
    UPNP_PORT = 1900
    M_SEARCH_REQ_MATCH = 'M-SEARCH'

    __logger__ = logging.getLogger()

    def __init__(self, q: queue.Queue):
        super(SnifferDiscovery, self).__init__()
        self.interrupted = False
        self.response_queue = q


    def run(self):
        self.loop_search()

    def stop(self):
        self.interrupted = True
        self.__logger__.info("UPNP server stopped.")

    def loop_search(self):
        try:
            while True:
                self.search()
                for x in range(self.SEARCH_INTERVAL):
                    time.sleep(1)
                    if self.interrupted:
                        return
        except Exception as e:
            self.__logger__.error("An exception occured on the discovery server!", exc_info=e)

    def search(self):
        sock = None
        try:
            DISCOVER = 'M-SEARCH * HTTP/1.1\n' \
                       f'HOST: {self.BROADCAST_IP}:{self.UPNP_PORT}\n' \
                       'MAN: "ssdp:discover"\n' \
                       'MX: 1\n' \
                       'ST: urn:sniffer:slave\n' \
                       '\n'

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('192.168.4.1', 1900))
            sock.sendto(DISCOVER.encode('ASCII'), (self.BROADCAST_IP, self.UPNP_PORT))
            sock.settimeout(3)
            #fcntl.ioctl(sock.fileno(), 0x8915, struct.pack('256s', ))
            while True:
                data, addr = sock.recvfrom(1024)
                self.__logger__.info("Device discovered at {}:{}", *addr)
                self.__logger__.info("Data received from device: {}", data.decode('ASCII'))
                self.response_queue.put_nowait((data, addr))
        except:
            if sock is not None:
                sock.close()


class DiscoveryHandler(threading.Thread):

    header_pattern = re.compile(r'^([^:\n]+):(?: ([^\n\r]+))?$', re.MULTILINE | re.ASCII)
    separator_pattern = re.compile(r'^\n+', re.MULTILINE | re.ASCII)

    __logger__ = logging.getLogger()

    def __init__(self, q: queue.Queue):
        super().__init__()
        self.response_queue = q
        self.interrupted = False

    def run(self) -> None:
        self.poll_responses()

    def stop(self):
        self.interrupted = True

    def poll_responses(self):
        """Consumes discovery responses pushed into the global queue."""
        while True:
            self.handle_response()
            # Give up the processor for a bit
            time.sleep(1)
            if self.interrupted:
                return

    def handle_response(self):
        """
        Pulls a response from the queue and processes it, registering a device if necessary.
        This function blocks until there is a response in the queue to process.
        """
        # Wait for a response to show up
        data, addr = self.response_queue.get(block=True)
        if not Device.objects.filter(address=addr[0]).exists():
            # Decode response data
            decoded = data.decode('ASCII')
            # Split away the response body if it exists
            sections = self.separator_pattern.split(decoded, 1)
            headers = {}

            for head in self.header_pattern.findall(sections[0]):
                headers[head[1].upper()] = head[2]

            urn = headers["URN"][5:]

            if not Device.objects.filter(serial_num=urn).exists():
                # Create a new sniffer device in the registry
                device = Device.objects.create(serail_num=urn, address=addr[0])
                device.save()
            elif not Device.objects.get(serial_num=urn).address == addr[0]:
                # Update address for device
                device = Device.objects.get(serial_num=urn)
                device.address = addr[0]
                device.save()


class WebUpdateHandler(threading.Thread):

    UPDATE_INTERVAL = 5

    __logger__ = logging.getLogger()

    def __init__(self, q: queue.Queue[requests.Request]):
        super().__init__()
        self.update_queue = q
        self.interrupted = False

    def run(self):
        self.update_loop()

    def stop(self):
        self.interrupted = True

    def update_loop(self):
        """Periodically sends """
        while True:
            self.send_update()
            # Only Update periodically, give the server time to process
            for x in range(self.UPDATE_INTERVAL):
                time.sleep(1)
                if self.interrupted:
                    self.__logger__.info("Web request handler interrupted. Thread exiting...")
                    return

    def send_update(self):
        iter_num = 0
        session = requests.session()
        while True:
            # Empty the queue of requests
            try:
                req = self.update_queue.get(block=False)
            except queue.Empty:
                # If there are no requests to process, end the loop
                break
            else:
                # Prepare and send the request
                prepped_req = session.prepare_request(req)
                self.__logger__.debug("Processing")

                session.send(prepped_req)
                # Wrap up the task
                self.update_queue.task_done()
                iter_num += 1
                # Only send ten requests per interval
                if iter_num >= 10:
                    break
        session.close()

