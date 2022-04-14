import logging
import threading
import queue
import requests
import time

REQUEST_QUEUE = queue.Queue()

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
                token = '9cf6a67a3904cdeec16bcdc89caa098e79ae4520'
                req.headers["Authentication"] = f'Token{token}'
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

#request_handler = WebUpdateHandler(REQUEST_QUEUE)
#request_handler.start()