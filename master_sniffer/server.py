import fcntl
import socket
import logging
import struct
import threading
import time
import re
import queue

#logging.basicConfig(stream=sys.stdout, format="[%(asctime)s] %(levelname)s: %(message)s")
import requests

from master_sniffer.models import Device

RESPONSE_QUEUE = queue.Queue()

class SnifferDiscovery(threading.Thread):

    SEARCH_INTERVAL = 5
    BROADCAST_IP = '239.255.255.250'
    UPNP_PORT = 1900
    M_SEARCH_REQ_MATCH = 'M-SEARCH'

    __logger__ = logging.getLogger()

    def __init__(self):
        super(SnifferDiscovery, self).__init__()
        self.interrupted = False


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
            fcntl.ioctl(sock.fileno(), 0x8915, struct.pack('256s', ))
            while True:
                data, addr = sock.recvfrom(1024)
                self.__logger__.info("Device discovered at {}:{}", *addr)
                self.__logger__.info("Data received from device: {}", data.decode('ASCII'))
                RESPONSE_QUEUE.put_nowait((data, addr))
                #if self._callback is not None:
                #    self._callback(self, data, addr)
        except:
            if sock is not None:
                sock.close()


class DiscoveryHandler(threading.Thread):

    header_pattern = re.compile(r'^([^:\n]+):(?: ([^\n\r]+))?$', re.MULTILINE | re.ASCII)
    separator_pattern = re.compile(r'^\n+', re.MULTILINE | re.ASCII)

    def __init__(self):
        super().__init__()

    def run(self) -> None:
        self.poll_responses()

    def poll_responses(self):
        """Consumes discovery responses pushed into the global queue."""
        while True:
            # Wait for a response to show up
            data, addr = RESPONSE_QUEUE.get(block=True)
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

    def __init__(self, q: queue.Queue[requests.Request]):
        super().__init__()
        self.update_queue = q

    def run(self):
        pass

    def update_loop(self):
        while True:
            req = self.update_queue.get(block=True)
            session = requests.session()

            prepped_req = session.prepare_request(req)
            session.send(prepped_req)
            self.update_queue.task_done()

    def enqueue(self, data):
        try:
            self.update_queue.put(data)
            return True
        except queue.Full:
            return False

if __name__ == '__main__':
    srv = SnifferDiscovery()
    srv.start()
