import socketio
import logging
import eventlet

eventlet.monkey_patch()

server = socketio.Server(async_handlers=False, logger=logging.getLogger('root'))

@server.event(namespace="debug")
def test(sid, data):
    server.logger.info("Received data: %s", data)
    return "OK"

@server.event(namespace="/ws/master")
def tracking_update(sid, data):
    server.logger.info("Received tracking data: %s", data)


