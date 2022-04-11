import fcntl
import socket
import logging
import struct
import sys
import threading
import time

#logging.basicConfig(stream=sys.stdout, format="[%(asctime)s] %(levelname)s: %(message)s")

class SnifferDiscovery(threading.Thread):

    SEARCH_INTERVAL = 5
    BROADCAST_IP = '239.255.255.250'
    UPNP_PORT = 1900
    M_SEARCH_REQ_MATCH = 'M-SEARCH'

    __logger__ = logging.getLogger()

    def __init__(self, callback=None):
        super(SnifferDiscovery, self).__init__()
        self.interrupted = False
        self._callback = None


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
                if self._callback is not None:
                    self._callback(self, data, addr)
        except:
            if sock is not None:
                sock.close()

if __name__ == '__main__':
    srv = SnifferDiscovery()
    srv.start()